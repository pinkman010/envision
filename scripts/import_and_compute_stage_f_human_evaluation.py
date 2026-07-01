from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.storage.p0_review_store import P0ReviewStore


DEFAULT_RUN_ID = "20260630T113930Z_e3_final_current_effective_set_accepted"
DEFAULT_INPUT_DIR = (
    ROOT_DIR
    / "data"
    / "runs"
    / "stage_f"
    / "20260701T030010Z_f_human_evaluation_completed"
)
REVIEWERS = ("staff", "professor", "member")
VERDICT_CLASSES = ("disclosed", "partially_disclosed", "not_disclosed", "manual_review")
SUPPORT_CLASSES = ("met", "partially_met", "not_met", "manual_review")
NO_ERROR_VALUES = {"none", "no_error", ""}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Import completed F human evaluation sheets into E4 SQLite and compute F metrics."
    )
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--db-path", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir or _new_output_dir()
    output_dir.mkdir(parents=True, exist_ok=False)

    store = P0ReviewStore(db_path=args.db_path)
    store.init_schema()

    assessments = store.list_assessments(args.run_id)
    advisor_items = store.list_advisor_items(args.run_id)
    assessment_by_manifest = {row["manifest_item_id"]: row for row in assessments}
    advisor_by_manifest = {row["manifest_item_id"]: row for row in advisor_items}

    source_rows = _load_all_review_rows(input_dir)
    import_summary = _import_reviews(
        store,
        args.run_id,
        source_rows,
        assessment_by_manifest=assessment_by_manifest,
        advisor_by_manifest=advisor_by_manifest,
    )

    metrics_payload = _compute_metrics(source_rows)
    error_analysis = _compute_error_analysis(source_rows)
    consensus_rows = _build_consensus_rows(source_rows)

    _write_json(output_dir / "f_human_review_import_summary.json", import_summary)
    _write_json(output_dir / "f_metrics_summary.json", metrics_payload)
    _write_json(output_dir / "f_error_analysis.json", error_analysis)
    _write_json(output_dir / "f_consensus_review_rows.json", consensus_rows)
    _write_csv(output_dir / "assessment_consensus_review_rows.csv", consensus_rows["assessment"])
    _write_csv(output_dir / "advisor_consensus_review_rows.csv", consensus_rows["advisor"])
    _write_csv(output_dir / "requirement_consensus_review_rows.csv", consensus_rows["requirement"])

    run_summary = {
        "run_id": output_dir.name,
        "source_e4_run_id": args.run_id,
        "created_at_utc": _utc_now(),
        "input_dir": str(input_dir.relative_to(ROOT_DIR)),
        "output_dir": str(output_dir.relative_to(ROOT_DIR)),
        "db_path": str(store.db_path),
        "status": "completed",
        "imported_review_decision_count": import_summary["imported_total"],
        "metrics_calculated": True,
        "assessment_majority_accuracy": metrics_payload["assessment"]["majority"]["accuracy"],
        "assessment_majority_macro_f1": metrics_payload["assessment"]["majority"]["macro_f1"],
        "advisor_majority_acceptance_rate": metrics_payload["advisor"]["majority"]["accepted_or_minor_revision_rate"],
        "requirement_majority_support_accuracy": metrics_payload["requirement"]["majority"]["support_status_accuracy"],
        "limitations": [
            "Metrics use completed human review workbooks archived in Stage F.",
            "Requirement-level metrics are calculated on the sampled requirement sheet, not on every requirement object.",
            "Traceability cleanup waivers remain in force for PDF full-string matching and evidence binding normalization.",
        ],
    }
    _write_json(output_dir / "run_summary.json", run_summary)
    print(json.dumps(run_summary, ensure_ascii=False, indent=2))
    return 0


def _new_output_dir() -> Path:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_f_metrics_and_error_analysis"
    return ROOT_DIR / "data" / "runs" / "stage_f" / run_id


def _load_all_review_rows(input_dir: Path) -> dict[str, dict[str, list[dict[str, Any]]]]:
    result: dict[str, dict[str, list[dict[str, Any]]]] = {
        "assessment": {},
        "advisor": {},
        "requirement": {},
    }
    for kind in result:
        for reviewer in REVIEWERS:
            path = input_dir / f"{kind}_review_completed_{reviewer}.json"
            rows = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(rows, list):
                raise ValueError(f"Expected list in {path}")
            result[kind][reviewer] = rows
    return result


def _import_reviews(
    store: P0ReviewStore,
    run_id: str,
    rows_by_kind: dict[str, dict[str, list[dict[str, Any]]]],
    *,
    assessment_by_manifest: dict[str, dict[str, Any]],
    advisor_by_manifest: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    imported_by_kind: dict[str, dict[str, int]] = {}
    errors: list[dict[str, Any]] = []

    for kind, rows_by_reviewer in rows_by_kind.items():
        imported_by_kind[kind] = {}
        for reviewer_label, rows in rows_by_reviewer.items():
            count = 0
            for row in rows:
                payload = _review_decision_payload(
                    kind,
                    reviewer_label,
                    row,
                    run_id,
                    assessment_by_manifest=assessment_by_manifest,
                    advisor_by_manifest=advisor_by_manifest,
                )
                if payload is None:
                    errors.append(
                        {
                            "kind": kind,
                            "reviewer": reviewer_label,
                            "row_key": row.get("review_key") or row.get("sample_id"),
                            "manifest_item_id": row.get("manifest_item_id"),
                            "error": "unmatched_manifest_item_id",
                        }
                    )
                    continue
                store.save_review_decision(payload)
                count += 1
            imported_by_kind[kind][reviewer_label] = count

    return {
        "status": "ok" if not errors else "failed",
        "imported_by_kind": imported_by_kind,
        "imported_total": sum(sum(by_reviewer.values()) for by_reviewer in imported_by_kind.values()),
        "error_count": len(errors),
        "errors": errors,
    }


def _review_decision_payload(
    kind: str,
    reviewer_label: str,
    row: dict[str, Any],
    run_id: str,
    *,
    assessment_by_manifest: dict[str, dict[str, Any]],
    advisor_by_manifest: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    manifest_item_id = _clean(row.get("manifest_item_id"))
    if not manifest_item_id:
        return None
    reviewer = _clean(row.get("reviewer")) or reviewer_label
    source = f"f_human_evaluation_import_{kind}_{reviewer_label}"

    assessment_id = None
    advisor_item_id = None
    if kind == "advisor":
        advisor = advisor_by_manifest.get(manifest_item_id)
        if advisor is None:
            return None
        advisor_item_id = advisor["advisor_item_id"]
    else:
        assessment = assessment_by_manifest.get(manifest_item_id)
        if assessment is None:
            return None
        assessment_id = assessment["assessment_id"]

    natural_key = row.get("sample_id") or row.get("review_key") or manifest_item_id
    review_decision_id = _stable_id("review", run_id, kind, reviewer_label, natural_key)

    if kind == "assessment":
        return {
            "review_decision_id": review_decision_id,
            "run_id": run_id,
            "assessment_id": assessment_id,
            "advisor_item_id": None,
            "manifest_item_id": manifest_item_id,
            "reviewer": reviewer,
            "human_verdict": _clean(row.get("human_verdict")),
            "evidence_page_check": _clean(row.get("human_evidence_page_check")),
            "requirement_gap_check": _clean(row.get("human_requirement_gap_check")),
            "advisor_usefulness_rating": None,
            "error_type": _normalize_error(row.get("human_error_code")),
            "correction_note": _clean(row.get("human_error_notes")),
            "review_comment": _clean(row.get("human_verdict_reason")),
            "source": source,
        }
    if kind == "advisor":
        review_comment = _join_nonempty(
            [
                f"accuracy={_clean(row.get('human_accuracy_check'))}",
                f"overreach={_clean(row.get('human_overreach_check'))}",
                f"requirement_binding={_clean(row.get('human_requirement_binding_check'))}",
                f"internal_data_flag={_clean(row.get('human_internal_data_flag_check'))}",
                _clean(row.get("human_comment")),
            ]
        )
        return {
            "review_decision_id": review_decision_id,
            "run_id": run_id,
            "assessment_id": None,
            "advisor_item_id": advisor_item_id,
            "manifest_item_id": manifest_item_id,
            "reviewer": reviewer,
            "human_verdict": _clean(row.get("human_accuracy_check")),
            "evidence_page_check": None,
            "requirement_gap_check": _clean(row.get("human_requirement_binding_check")),
            "advisor_usefulness_rating": _clean(row.get("human_usefulness_rating")),
            "error_type": _normalize_error(row.get("human_error_code")),
            "correction_note": _clean(row.get("human_comment")),
            "review_comment": review_comment,
            "source": source,
        }
    if kind == "requirement":
        review_comment = _join_nonempty(
            [
                f"sample_id={_clean(row.get('sample_id'))}",
                f"requirement_id_effective={_clean(row.get('requirement_id_effective'))}",
                f"human_requirement_text_check={_clean(row.get('human_requirement_text_check'))}",
                f"human_evidence_binding_check={_clean(row.get('human_evidence_binding_check'))}",
                _clean(row.get("human_comment")),
            ]
        )
        return {
            "review_decision_id": review_decision_id,
            "run_id": run_id,
            "assessment_id": assessment_id,
            "advisor_item_id": None,
            "manifest_item_id": manifest_item_id,
            "reviewer": reviewer,
            "human_verdict": _clean(row.get("human_support_status")),
            "evidence_page_check": _clean(row.get("human_evidence_binding_check")),
            "requirement_gap_check": _clean(row.get("human_requirement_text_check")),
            "advisor_usefulness_rating": None,
            "error_type": _normalize_error(row.get("human_error_code")),
            "correction_note": _clean(row.get("human_comment")),
            "review_comment": review_comment,
            "source": source,
        }
    raise ValueError(f"Unsupported kind: {kind}")


def _compute_metrics(rows_by_kind: dict[str, dict[str, list[dict[str, Any]]]]) -> dict[str, Any]:
    assessment = _assessment_metrics(rows_by_kind["assessment"])
    advisor = _advisor_metrics(rows_by_kind["advisor"])
    requirement = _requirement_metrics(rows_by_kind["requirement"])
    return {
        "created_at_utc": _utc_now(),
        "assessment": assessment,
        "advisor": advisor,
        "requirement": requirement,
        "methodology": {
            "reviewer_labels": list(REVIEWERS),
            "majority_rule": "Use the most common human label across three reviewers; ties are recorded as no_consensus.",
            "no_error_values": sorted(NO_ERROR_VALUES),
            "manual_review_treatment": "manual_review is treated as a valid abstention/risk-control class for classification metrics and also reported separately.",
        },
    }


def _assessment_metrics(rows_by_reviewer: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    per_reviewer = {}
    for reviewer, rows in rows_by_reviewer.items():
        y_true = [_clean(row.get("human_verdict")) for row in rows]
        y_pred = [_clean(row.get("ai_verdict")) for row in rows]
        per_reviewer[reviewer] = {
            **_classification_metrics(y_true, y_pred, VERDICT_CLASSES),
            "human_verdict_distribution": dict(Counter(y_true)),
            "ai_verdict_distribution": dict(Counter(y_pred)),
            "evidence_page_check_ok_rate": _rate(row.get("human_evidence_page_check") == "ok" for row in rows),
            "requirement_gap_check_ok_rate": _rate(row.get("human_requirement_gap_check") == "ok" for row in rows),
            "human_correction_rate": _rate(_clean(row.get("ai_verdict")) != _clean(row.get("human_verdict")) for row in rows),
            "non_no_error_rate": _rate(_normalize_error(row.get("human_error_code")) for row in rows),
            "error_distribution": dict(Counter(_normalize_error(row.get("human_error_code")) or "no_error" for row in rows)),
        }

    majority_rows = _majority_rows(rows_by_reviewer, "manifest_item_id", "human_verdict")
    y_true_majority = [row["majority_label"] for row in majority_rows if row["majority_label"]]
    y_pred_majority = [row["ai_verdict"] for row in majority_rows if row["majority_label"]]
    majority_metrics = {
        **_classification_metrics(y_true_majority, y_pred_majority, VERDICT_CLASSES),
        "row_count": len(majority_rows),
        "consensus_full_agreement_rate": _rate(row["full_agreement"] for row in majority_rows),
        "no_consensus_count": sum(1 for row in majority_rows if not row["majority_label"]),
        "manual_review_ai_trigger_rate": _rate(row["ai_verdict"] == "manual_review" for row in majority_rows),
        "manual_review_human_majority_rate": _rate(row["majority_label"] == "manual_review" for row in majority_rows),
        "human_correction_rate": _rate(
            row["majority_label"] and row["ai_verdict"] != row["majority_label"] for row in majority_rows
        ),
    }
    return {"per_reviewer": per_reviewer, "majority": majority_metrics}


def _advisor_metrics(rows_by_reviewer: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    per_reviewer = {}
    for reviewer, rows in rows_by_reviewer.items():
        usefulness = [_clean(row.get("human_usefulness_rating")) for row in rows]
        per_reviewer[reviewer] = {
            "row_count": len(rows),
            "usefulness_distribution": dict(Counter(usefulness)),
            "accepted_rate": _rate(value == "accepted" for value in usefulness),
            "accepted_or_minor_revision_rate": _rate(value in {"accepted", "minor_revision"} for value in usefulness),
            "accuracy_ok_rate": _rate(row.get("human_accuracy_check") == "ok" for row in rows),
            "overreach_ok_rate": _rate(row.get("human_overreach_check") == "ok" for row in rows),
            "requirement_binding_ok_rate": _rate(row.get("human_requirement_binding_check") == "ok" for row in rows),
            "internal_data_flag_ok_rate": _rate(row.get("human_internal_data_flag_check") == "ok" for row in rows),
            "error_distribution": dict(Counter(_normalize_error(row.get("human_error_code")) or "no_error" for row in rows)),
        }
    majority_rows = _majority_rows(rows_by_reviewer, "review_key", "human_usefulness_rating")
    majority = {
        "row_count": len(majority_rows),
        "consensus_full_agreement_rate": _rate(row["full_agreement"] for row in majority_rows),
        "usefulness_distribution": dict(Counter(row["majority_label"] or "no_consensus" for row in majority_rows)),
        "accepted_rate": _rate(row["majority_label"] == "accepted" for row in majority_rows),
        "accepted_or_minor_revision_rate": _rate(row["majority_label"] in {"accepted", "minor_revision"} for row in majority_rows),
    }
    return {"per_reviewer": per_reviewer, "majority": majority}


def _requirement_metrics(rows_by_reviewer: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    per_reviewer = {}
    for reviewer, rows in rows_by_reviewer.items():
        y_true = [_clean(row.get("human_support_status")) for row in rows]
        y_pred = [_clean(row.get("support_status")) for row in rows]
        per_reviewer[reviewer] = {
            **_classification_metrics(y_true, y_pred, SUPPORT_CLASSES),
            "support_status_accuracy": _accuracy(y_true, y_pred),
            "human_support_distribution": dict(Counter(y_true)),
            "ai_support_distribution": dict(Counter(y_pred)),
            "requirement_text_ok_rate": _rate(row.get("human_requirement_text_check") == "ok" for row in rows),
            "evidence_binding_ok_rate": _rate(row.get("human_evidence_binding_check") == "ok" for row in rows),
            "error_distribution": dict(Counter(_normalize_error(row.get("human_error_code")) or "no_error" for row in rows)),
        }
    majority_rows = _majority_rows(rows_by_reviewer, "sample_id", "human_support_status")
    y_true_majority = [row["majority_label"] for row in majority_rows if row["majority_label"]]
    y_pred_majority = [row["support_status"] for row in majority_rows if row["majority_label"]]
    majority = {
        **_classification_metrics(y_true_majority, y_pred_majority, SUPPORT_CLASSES),
        "row_count": len(majority_rows),
        "support_status_accuracy": _accuracy(y_true_majority, y_pred_majority),
        "consensus_full_agreement_rate": _rate(row["full_agreement"] for row in majority_rows),
        "no_consensus_count": sum(1 for row in majority_rows if not row["majority_label"]),
    }
    return {"per_reviewer": per_reviewer, "majority": majority}


def _compute_error_analysis(rows_by_kind: dict[str, dict[str, list[dict[str, Any]]]]) -> dict[str, Any]:
    result = {"created_at_utc": _utc_now(), "by_kind": {}}
    for kind, rows_by_reviewer in rows_by_kind.items():
        by_reviewer = {}
        aggregate = Counter()
        examples = defaultdict(list)
        for reviewer, rows in rows_by_reviewer.items():
            counter = Counter(_normalize_error(row.get("human_error_code")) or "no_error" for row in rows)
            by_reviewer[reviewer] = dict(counter)
            aggregate.update(counter)
            for row in rows:
                error = _normalize_error(row.get("human_error_code")) or "no_error"
                if error == "no_error" or len(examples[error]) >= 8:
                    continue
                examples[error].append(
                    {
                        "reviewer": reviewer,
                        "key": row.get("manifest_item_id") or row.get("sample_id") or row.get("review_key"),
                        "ai": row.get("ai_verdict") or row.get("support_status") or row.get("linked_ai_verdict"),
                        "human": row.get("human_verdict") or row.get("human_support_status") or row.get("human_usefulness_rating"),
                        "comment": row.get("human_error_notes") or row.get("human_comment") or row.get("human_verdict_reason"),
                    }
                )
        result["by_kind"][kind] = {
            "aggregate_error_distribution": dict(aggregate),
            "by_reviewer": by_reviewer,
            "examples": dict(examples),
        }
    return result


def _build_consensus_rows(rows_by_kind: dict[str, dict[str, list[dict[str, Any]]]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "assessment": _majority_rows(rows_by_kind["assessment"], "manifest_item_id", "human_verdict"),
        "advisor": _majority_rows(rows_by_kind["advisor"], "review_key", "human_usefulness_rating"),
        "requirement": _majority_rows(rows_by_kind["requirement"], "sample_id", "human_support_status"),
    }


def _majority_rows(rows_by_reviewer: dict[str, list[dict[str, Any]]], key_field: str, label_field: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for reviewer, rows in rows_by_reviewer.items():
        for row in rows:
            grouped[str(row.get(key_field, ""))].append((reviewer, row))
    output = []
    for key in sorted(grouped):
        pairs = grouped[key]
        labels = [_clean(row.get(label_field)) for _, row in pairs]
        counts = Counter(labels)
        label, count = counts.most_common(1)[0]
        majority_label = label if count >= 2 else None
        first = pairs[0][1]
        output.append(
            {
                "key": key,
                "manifest_item_id": first.get("manifest_item_id"),
                "standard_id": first.get("standard_id"),
                "canonical_disclosure_id": first.get("canonical_disclosure_id"),
                "ai_verdict": first.get("ai_verdict") or first.get("linked_ai_verdict"),
                "support_status": first.get("support_status"),
                "majority_label": majority_label,
                "full_agreement": len(set(labels)) == 1,
                "reviewer_labels": " | ".join(f"{reviewer}:{_clean(row.get(label_field))}" for reviewer, row in pairs),
                "reviewer_error_codes": " | ".join(
                    f"{reviewer}:{_normalize_error(row.get('human_error_code')) or 'no_error'}" for reviewer, row in pairs
                ),
            }
        )
    return output


def _classification_metrics(y_true: list[str | None], y_pred: list[str | None], classes: tuple[str, ...]) -> dict[str, Any]:
    pairs = [(t, p) for t, p in zip(y_true, y_pred) if t in classes and p in classes]
    matrix = {true: {pred: 0 for pred in classes} for true in classes}
    for true, pred in pairs:
        matrix[true][pred] += 1

    per_class = {}
    f1s = []
    for cls in classes:
        tp = matrix[cls][cls]
        fp = sum(matrix[other][cls] for other in classes if other != cls)
        fn = sum(matrix[cls][other] for other in classes if other != cls)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[cls] = {"precision": precision, "recall": recall, "f1": f1, "support": sum(matrix[cls].values())}
        f1s.append(f1)

    return {
        "row_count": len(y_true),
        "evaluated_count": len(pairs),
        "accuracy": _accuracy([t for t, _ in pairs], [p for _, p in pairs]),
        "macro_f1": sum(f1s) / len(f1s) if f1s else 0.0,
        "per_class": per_class,
        "confusion_matrix": matrix,
    }


def _accuracy(y_true: list[str | None], y_pred: list[str | None]) -> float:
    pairs = [(t, p) for t, p in zip(y_true, y_pred) if t is not None and p is not None]
    if not pairs:
        return 0.0
    return sum(1 for t, p in pairs if t == p) / len(pairs)


def _rate(values) -> float:
    vals = list(values)
    if not vals:
        return 0.0
    return sum(1 for value in vals if bool(value)) / len(vals)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    headers = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                headers.append(key)
                seen.add(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _stable_id(prefix: str, *parts: Any) -> str:
    material = "|".join("" if part is None else str(part) for part in parts)
    return f"{prefix}_{hashlib.sha256(material.encode('utf-8')).hexdigest()[:16]}"


def _normalize_error(value: Any) -> str | None:
    text = _clean(value)
    if text is None:
        return None
    return None if text in {"none", "no_error"} else text


def _join_nonempty(values: list[str | None]) -> str | None:
    joined = " | ".join(value for value in values if value)
    return joined or None


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
