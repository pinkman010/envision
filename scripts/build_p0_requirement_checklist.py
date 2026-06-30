"""Build the P0 E2.1-A requirement checklist from official GRI PDF text.

The builder creates pending-review leaf/checklist items. It does not call LLMs,
rewrite source PDFs, rebuild vector stores, or write databases.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from pypdf import PdfReader

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.paths import (  # noqa: E402
    GRI_REFERENCE_PDF_PATH,
    P0_GRI_REQUIREMENT_CHECKLIST_PATH,
    P0_GRI_REQUIREMENT_PACK_PATH,
)
from src.models import AnalysisMode, GRIRequirementPack  # noqa: E402

CURRENT_PROFILE_ID = "gri_p0_2024_current_disclosure_v1"
ANALYSIS_APPLICABILITY_DATE = "2024-12-31"
GENERIC_3_3_CANONICAL_ID = "3-3_generic"
ROMAN_MARKERS = {"i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"}


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize_text(parts: Sequence[str]) -> str:
    return re.sub(r"\s+", " ", " ".join(part.strip() for part in parts if part.strip())).strip()


def _official_pdf_page(requirement: Any) -> Optional[int]:
    if requirement.manual_locator_review is not None:
        return requirement.manual_locator_review.confirmed_official_pdf_pages[0]
    if requirement.official_pdf_page_candidates:
        return requirement.official_pdf_page_candidates[0]
    return None


def _marker_from_line(line: str) -> Tuple[Optional[str], str]:
    stripped = line.strip()
    if re.fullmatch(r"(?:[a-z]|i|ii|iii|iv|v|vi|vii|viii|ix|x)\.", stripped, re.IGNORECASE):
        return stripped[:-1].lower(), ""
    if re.fullmatch(r"2\.\d+(?:\.\d+)?", stripped):
        return stripped, ""

    text_marker = re.match(
        r"^(?P<text>.+?[.;:])(?P<marker>(?:[a-z]|i|ii|iii|iv|v|vi|vii|viii|ix|x))\.$",
        stripped,
        flags=re.IGNORECASE,
    )
    if text_marker:
        return text_marker.group("marker").lower(), text_marker.group("text").strip()

    numeric_marker = re.match(r"^(?P<text>.+?[.;:])(?P<marker>2\.\d+(?:\.\d+)?)$", stripped)
    if numeric_marker:
        return numeric_marker.group("marker"), numeric_marker.group("text").strip()

    return None, stripped


def _disclosure_text(reader: PdfReader, requirement: Any) -> str:
    page = _official_pdf_page(requirement)
    if page is None:
        return ""
    end_page = min(page + 3, len(reader.pages))
    text = "\n".join(reader.pages[index - 1].extract_text() or "" for index in range(page, end_page + 1))
    disclosure_id = str(requirement.canonical_disclosure_id or "")
    start = text.lower().find(f"disclosure {disclosure_id}".lower())
    disclosure_text = text[start if start >= 0 else 0 :]
    next_disclosure = re.search(r"\nDisclosure\s+\d+-\d+\b", disclosure_text[100:])
    if next_disclosure:
        disclosure_text = disclosure_text[: 100 + next_disclosure.start()]
    return disclosure_text


def _requirement_section_lines(disclosure_text: str) -> List[str]:
    lines = [line.strip() for line in disclosure_text.splitlines() if line.strip()]
    start = 0
    for index, line in enumerate(lines):
        if "REQUIREMENTS" in line:
            start = index + 1
            break

    section: List[str] = []
    for line in lines[start:]:
        if re.match(r"^(RECOMMENDATIONS|Background|Guidance|GUIDANCE|GRI\s+\d+)", line):
            break
        section.append(line)
    return section


def _extract_requirement_units(disclosure_text: str) -> List[Tuple[str, str, str]]:
    """Return (suffix, requirement_type, text) tuples from a disclosure section."""
    units: List[Tuple[str, str, str]] = []
    buffer: List[str] = []
    parent_intro: List[str] = []
    pending_roman_children: List[Tuple[str, str]] = []

    for line in _requirement_section_lines(disclosure_text):
        marker, marker_text = _marker_from_line(line)
        if marker is None:
            buffer.append(marker_text)
            continue

        is_roman = marker in ROMAN_MARKERS
        is_letter = bool(re.fullmatch(r"[a-z]", marker)) and not is_roman
        is_numeric = marker.startswith("2.")

        if marker_text:
            if is_roman and buffer and _normalize_text(buffer).endswith(":"):
                parent_intro = buffer[:]
                item_text = marker_text
            else:
                item_text = _normalize_text(buffer + [marker_text])
                if is_roman and parent_intro and _normalize_text(buffer) == _normalize_text(parent_intro):
                    item_text = marker_text
            buffer = parent_intro[:] if is_roman and parent_intro else []
        elif is_roman:
            colon_index = next(
                (index for index in range(len(buffer) - 1, -1, -1) if buffer[index].strip().endswith(":")),
                None,
            )
            if colon_index is not None:
                parent_intro = buffer[: colon_index + 1]
                item_text = _normalize_text(buffer[colon_index + 1 :])
                buffer = parent_intro[:]
            else:
                item_text = _normalize_text(buffer)
                buffer = []
        else:
            item_text = _normalize_text(parent_intro or buffer) if is_letter else _normalize_text(buffer)
            buffer = []

        if not item_text:
            continue

        if is_letter:
            units.append((marker, "requirement", item_text))
            for child_marker, child_text in pending_roman_children:
                units.append((f"{marker}:{child_marker}", "requirement", child_text))
            pending_roman_children = []
            parent_intro = []
        elif is_roman:
            pending_roman_children.append((marker, item_text))
        elif is_numeric:
            units.append((marker, "compilation_requirement", item_text))
            pending_roman_children = []
            parent_intro = []

    return units


def _requirement_item(requirement: Any, suffix: str, requirement_type: str, text: str) -> Dict[str, Any]:
    return {
        "requirement_id": f"{requirement.manifest_item_id}:{suffix}",
        "parent_requirement_id": requirement.manifest_item_id,
        "canonical_disclosure_id": requirement.canonical_disclosure_id,
        "requirement_text": text,
        "requirement_type": requirement_type,
        "conditional": False,
        "condition_text": "",
        "official_pdf_page": _official_pdf_page(requirement),
        "is_mandatory": True,
        "scoring_role": "hard_score",
        "standard_year": requirement.standard_year,
        "published_at": None,
        "effective_date": requirement.effective_date,
        "analysis_applicability_date": ANALYSIS_APPLICABILITY_DATE,
        "replaced_standard": requirement.related_current_standard,
        "assessment_mode": requirement.analysis_mode.value,
        "standard_profile_id": CURRENT_PROFILE_ID,
        "extraction_review_status": "pending_review",
        "notes": "E2.1-A rule-extracted item from official GRI PDF text; pending manual extraction review.",
    }


def build_p0_requirement_checklist() -> Dict[str, Any]:
    requirement_pack = GRIRequirementPack.model_validate(_load_json(P0_GRI_REQUIREMENT_PACK_PATH))
    reader = PdfReader(str(GRI_REFERENCE_PDF_PATH))
    requirements: List[Dict[str, Any]] = []
    topic_instantiation_required: List[Dict[str, str]] = []
    excluded_items: List[Dict[str, Any]] = []

    for requirement in requirement_pack.requirements:
        if requirement.analysis_mode != AnalysisMode.CURRENT_GAP:
            excluded_items.append(
                {
                    "parent_requirement_id": requirement.manifest_item_id,
                    "assessment_mode": requirement.analysis_mode.value,
                    "canonical_disclosure_id": requirement.canonical_disclosure_id,
                    "reason": "Future readiness/watchlist item is excluded from the 2024 current hard_score checklist.",
                }
            )
            continue

        if requirement.canonical_disclosure_id == GENERIC_3_3_CANONICAL_ID:
            topic_instantiation_required.append(
                {
                    "parent_requirement_id": requirement.manifest_item_id,
                    "canonical_disclosure_id": GENERIC_3_3_CANONICAL_ID,
                    "reason": "GRI 3-3 must be instantiated and assessed per material topic before scoring.",
                }
            )
            continue

        for suffix, requirement_type, text in _extract_requirement_units(_disclosure_text(reader, requirement)):
            requirements.append(_requirement_item(requirement, suffix, requirement_type, text))

    excluded_counts: Dict[str, int] = {}
    for item in excluded_items:
        mode = str(item["assessment_mode"])
        excluded_counts[mode] = excluded_counts.get(mode, 0) + 1

    return {
        "metadata": {
            "manifest_version": "p0_gri_requirement_checklist_v1",
            "standard_profile_id": CURRENT_PROFILE_ID,
            "source_requirement_pack": "data/knowledge_base/manifests/p0_gri_requirement_pack.json",
            "source_disclosure_manifest": "data/knowledge_base/manifests/p0_gri_disclosure_manifest.json",
            "created_at": date.today().isoformat(),
            "generated_by": "scripts/build_p0_requirement_checklist.py",
            "notes": (
                "E2.1-A rule-extracted checklist from official GRI PDF text. Items are "
                "pending_review until manual extraction review confirms leaf boundaries."
            ),
            "excluded_counts_by_mode": dict(sorted(excluded_counts.items())),
            "excluded_items": excluded_items,
        },
        "requirements": requirements,
        "topic_instantiation_required": topic_instantiation_required,
    }


def main() -> int:
    payload = build_p0_requirement_checklist()
    _write_json(P0_GRI_REQUIREMENT_CHECKLIST_PATH, payload)
    print(
        json.dumps(
            {
                "status": "ok",
                "path": str(P0_GRI_REQUIREMENT_CHECKLIST_PATH),
                "requirement_count": len(payload["requirements"]),
                "topic_instantiation_required_count": len(payload["topic_instantiation_required"]),
                "excluded_item_count": len(payload["metadata"]["excluded_items"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())