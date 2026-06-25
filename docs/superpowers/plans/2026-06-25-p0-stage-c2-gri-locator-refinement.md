# P0 阶段 C2：GRI Locator 收敛实施计划

> **给执行代理的说明：** 必须使用 `superpowers:subagent-driven-development` 按任务执行本计划。步骤使用 `- [ ]` 复选框跟踪。执行子代理不得使用 `list_agents`、`wait_agent`、`send_message` 或 `followup_task`。

**目标：** 在不人工编造页码、不调用外部 LLM 的前提下，将阶段 C 产出的 GRI 官方 PDF locator 从大批量 `multiple_candidates` 收敛为可用于阶段 D 的“唯一标题页候选 + 少量人工复核项”。

**架构：** 保持阶段 C 的 `GRIRequirementPack` 与 `ReportEvidenceIndex` 模型不变，增强 GRI PDF 定位算法：先利用 PDF outline 建立标准章节边界，再在章节范围内做 disclosure 标题行锚定和候选页评分。新增一个 locator refinement audit JSON 记录收敛前后统计、章节边界和仍需人工复核的 disclosure，供阶段 D 判断哪些条款可自动引用、哪些条款必须保留人工复核。

**技术栈：** Python 3、Pydantic v2、pypdf、hashlib、json、pathlib、re、项目 Conda 环境 `C:\ProgramData\miniconda3\envs\envision\python.exe`。

---

## 1. 背景与问题

阶段 C 已通过第一阶段门，但当前 `p0_gri_requirement_pack.json` 的 locator 状态为：

```json
{
  "found": 0,
  "multiple_candidates": 114,
  "not_found": 0,
  "requires_topic_instantiation": 1,
  "not_required_for_future_watch": 3,
  "locator_review_required_count": 114
}
```

原因不是标准文件缺失，而是阶段 C 的定位规则过宽：

- `Disclosure {id}` 会命中目录、交叉引用、行业标准中的重复引用。
- `standard_id` 兜底会命中整个标准章节中的大量页。
- GRI 合订本包含通用标准、主题标准和行业标准，同一 disclosure 会在多个章节重复出现。

阶段 C2 的目标是收敛定位，不做披露分析，不改 Agent，不改 Prompt。

## 2. 范围

本计划覆盖：

- 从 GRI PDF outline 中提取 `GRI 2`、`GRI 3`、`GRI 201` 等标准章节边界。
- 按 `standard_id + standard_year` 选择 disclosure 所属官方标准章节。
- 在所属章节内识别 disclosure 标题行。
- 对候选页打分，优先选择正文标题页，排除目录、交叉引用、范围说明和行业标准重复引用。
- 重新生成 `p0_gri_requirement_pack.json`。
- 新增 locator refinement audit JSON。
- 增强验证脚本，确保收敛效果被阶段门约束。

本计划不做：

- 不修改 `src/agent`。
- 不修改 `templates/prompt_templates`。
- 不修改 Streamlit UI。
- 不新增数据库表。
- 不连接外部 dashboard。
- 不人工填写 114 个页码覆盖算法结果。
- 不把中文译文写成权威条款。
- 不调用外部 LLM 解析或翻译 GRI 条款。

## 3. 输入

- `C:\Alvin\SUFE\整合实践\envision\data\knowledge_base\manifests\p0_source_manifest.json`
- `C:\Alvin\SUFE\整合实践\envision\data\knowledge_base\manifests\p0_gri_disclosure_manifest.json`
- `C:\Alvin\SUFE\整合实践\envision\data\knowledge_base\manifests\p0_gri_requirement_pack.json`
- `C:\Alvin\SUFE\整合实践\envision\data\knowledge_base\standards\gri_reference\GRI_Standards_Official_Consolidated_Set_en.pdf`

## 4. 输出

- 覆盖更新：`C:\Alvin\SUFE\整合实践\envision\data\knowledge_base\manifests\p0_gri_requirement_pack.json`
- 新增：`C:\Alvin\SUFE\整合实践\envision\data\knowledge_base\manifests\p0_gri_locator_refinement_audit.json`

`p0_report_evidence_index.json` 不需要重建，因为 C2 只处理 GRI 官方条款定位，不处理远景报告分块。

## 5. 文件清单

- 修改：`C:\Alvin\SUFE\整合实践\envision\src\config\paths.py`
- 修改：`C:\Alvin\SUFE\整合实践\envision\src\utils\evidence_layer_utils.py`
- 修改：`C:\Alvin\SUFE\整合实践\envision\scripts\build_p0_evidence_layer.py`
- 修改：`C:\Alvin\SUFE\整合实践\envision\scripts\validate_p0_evidence_layer.py`
- 新增：`C:\Alvin\SUFE\整合实践\envision\scripts\inspect_p0_gri_locators.py`
- 新增：`C:\Alvin\SUFE\整合实践\envision\data\knowledge_base\manifests\p0_gri_locator_refinement_audit.json`

不得 stage、commit 或格式化无关文件，除非用户明确授权 Git 操作。

---

## 任务 1：新增 C2 输出路径常量

**文件：**

- 修改：`C:\Alvin\SUFE\整合实践\envision\src\config\paths.py`

- [ ] **步骤 1：新增 audit manifest 路径**

在阶段 C manifest 路径常量附近添加：

```python
P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH: Path = MANIFESTS_DIR / "p0_gri_locator_refinement_audit.json"
```

- [ ] **步骤 2：验证路径导入**

运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe -c "from src.config.paths import P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH; print(P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH.name)"
```

期望输出：

```text
p0_gri_locator_refinement_audit.json
```

---

## 任务 2：新增 GRI PDF 章节边界提取

**文件：**

- 修改：`C:\Alvin\SUFE\整合实践\envision\src\utils\evidence_layer_utils.py`

- [ ] **步骤 1：新增依赖导入**

在文件顶部导入 `dataclass` 和 `PdfReader`：

```python
from dataclasses import dataclass
from pypdf import PdfReader
```

- [ ] **步骤 2：新增章节边界数据结构**

在常量定义后添加：

```python
@dataclass(frozen=True)
class GRIStandardSection:
    standard_id: str
    standard_year: str
    title: str
    start_pdf_page: int
    end_pdf_page: int
```

- [ ] **步骤 3：新增标准 ID 解析函数**

添加函数：

```python
def _standard_id_from_outline_title(title: str) -> Optional[str]:
    match = re.match(r"^(GRI\s+\d+):", title.strip())
    return match.group(1) if match else None
```

- [ ] **步骤 4：新增标准年份解析函数**

添加函数：

```python
def _standard_year_from_outline_title(title: str) -> str:
    match = re.search(r"\b(20\d{2})\b", title)
    return match.group(1) if match else ""
```

- [ ] **步骤 5：新增 outline 扁平化函数**

添加函数：

```python
def _flatten_pdf_outline(reader: PdfReader) -> List[Tuple[int, str, int]]:
    rows: List[Tuple[int, str, int]] = []

    def walk(items: Iterable[Any], depth: int = 0) -> None:
        for item in items:
            if isinstance(item, list):
                walk(item, depth + 1)
                continue
            title = getattr(item, "title", str(item)).strip()
            try:
                page_number = reader.get_destination_page_number(item) + 1
            except Exception:
                continue
            rows.append((depth, title, page_number))

    walk(reader.outline)
    return rows
```

- [ ] **步骤 6：新增章节边界提取函数**

添加函数：

```python
def _extract_gri_standard_sections(pdf_path: Path = GRI_REFERENCE_PDF_PATH) -> List[GRIStandardSection]:
    reader = PdfReader(str(pdf_path))
    outline_rows = _flatten_pdf_outline(reader)
    top_level_standards = [
        (title, page)
        for depth, title, page in outline_rows
        if depth == 0 and _standard_id_from_outline_title(title)
    ]
    top_level_standards.sort(key=lambda item: item[1])

    sections: List[GRIStandardSection] = []
    for index, (title, start_page) in enumerate(top_level_standards):
        end_page = top_level_standards[index + 1][1] - 1 if index + 1 < len(top_level_standards) else len(reader.pages)
        standard_id = _standard_id_from_outline_title(title)
        if not standard_id:
            continue
        sections.append(
            GRIStandardSection(
                standard_id=standard_id,
                standard_year=_standard_year_from_outline_title(title),
                title=title,
                start_pdf_page=start_page,
                end_pdf_page=end_page,
            )
        )
    return sections
```

- [ ] **步骤 7：新增章节选择函数**

添加函数：

```python
def _section_for_standard(
    sections: Sequence[GRIStandardSection],
    *,
    standard_id: str,
    standard_year: str,
) -> Optional[GRIStandardSection]:
    matching_id = [section for section in sections if section.standard_id == standard_id]
    matching_year = [section for section in matching_id if section.standard_year == standard_year]
    if matching_year:
        return matching_year[0]
    if matching_id:
        return matching_id[0]
    return None
```

- [ ] **步骤 8：验证 GRI outline 可读**

运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe -c "from src.utils.evidence_layer_utils import _extract_gri_standard_sections; sections=_extract_gri_standard_sections(); print(len(sections)); print(any(s.standard_id == 'GRI 2' and s.standard_year == '2021' for s in sections)); print(any(s.standard_id == 'GRI 306' and s.standard_year == '2020' for s in sections))"
```

期望输出：

```text
大于 20 的整数
True
True
```

---

## 任务 3：将 locator 从宽匹配改为章节内标题页评分

**文件：**

- 修改：`C:\Alvin\SUFE\整合实践\envision\src\utils\evidence_layer_utils.py`

- [ ] **步骤 1：新增标题行识别函数**

添加函数：

```python
def _line_starts_disclosure_heading(line: str, disclosure_id: str) -> bool:
    stripped = line.strip()
    return bool(re.match(rf"^Disclosure\s+{re.escape(disclosure_id)}\b", stripped, flags=re.IGNORECASE))
```

- [ ] **步骤 2：新增短 ID 标题行识别函数**

添加函数：

```python
def _line_starts_short_disclosure_heading(line: str, disclosure_id: str) -> bool:
    stripped = line.strip()
    return bool(re.match(rf"^{re.escape(disclosure_id)}\s+[A-Z][A-Za-z]", stripped))
```

- [ ] **步骤 3：新增交叉引用排除函数**

添加函数：

```python
def _is_cross_reference_line(line: str, disclosure_id: str) -> bool:
    lowered = _norm_text(line).lower()
    compact_double_space = f"disclosure  {disclosure_id}".lower()
    reference_markers = [
        "through disclosure",
        "in this standard",
        "is related to",
        "does not require",
        "see references",
        "referred to in disclosure",
    ]
    return (
        "•" in line
        or compact_double_space in lowered
        or any(marker in lowered for marker in reference_markers)
    )
```

- [ ] **步骤 4：新增候选页评分函数**

添加函数：

```python
def _score_disclosure_candidate_page(page_text: str, disclosure_id: str) -> Tuple[int, List[str]]:
    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    matched_lines: List[str] = []
    best_score = 0

    for line in lines:
        is_full_heading = _line_starts_disclosure_heading(line, disclosure_id)
        is_short_heading = _line_starts_short_disclosure_heading(line, disclosure_id)
        if not is_full_heading and not is_short_heading:
            continue

        matched_lines.append(_norm_text(line)[:240])
        if _is_cross_reference_line(line, disclosure_id):
            best_score = max(best_score, 10)
            continue
        if is_full_heading:
            best_score = max(best_score, 100)
            continue
        if is_short_heading:
            best_score = max(best_score, 80)

    return best_score, matched_lines
```

- [ ] **步骤 5：新增章节内候选页收敛函数**

添加函数：

```python
def _rank_disclosure_pages_within_section(
    *,
    canonical_disclosure_id: str,
    section: GRIStandardSection,
    gri_pages: Sequence[Dict[str, object]],
) -> Tuple[List[int], List[str], List[str]]:
    scored_pages: List[Tuple[int, int, str, str]] = []
    for page in gri_pages:
        page_number = int(page["pdf_page"])
        if page_number < section.start_pdf_page or page_number > section.end_pdf_page:
            continue
        text = str(page.get("text") or "")
        score, matched_lines = _score_disclosure_candidate_page(text, canonical_disclosure_id)
        if score <= 0:
            continue
        title = matched_lines[0] if matched_lines else _title_candidate(text, canonical_disclosure_id, section.standard_id)
        excerpt = _candidate_excerpt(text, matched_lines or [canonical_disclosure_id])
        scored_pages.append((score, page_number, title, excerpt))

    if not scored_pages:
        return [], [], []

    best_score = max(score for score, _, _, _ in scored_pages)
    best_pages = [(page, title, excerpt) for score, page, title, excerpt in scored_pages if score == best_score]
    unique_pages = sorted({page for page, _, _ in best_pages})
    titles = list(dict.fromkeys(title for _, title, _ in best_pages if title))[:8]
    excerpts = list(dict.fromkeys(excerpt for _, _, excerpt in best_pages if excerpt))[:8]
    return unique_pages, titles, excerpts
```

- [ ] **步骤 6：修改 `_locate_gri_requirement` 函数签名**

将签名改为：

```python
def _locate_gri_requirement(
    *,
    analysis_mode: str,
    canonical_disclosure_id: Optional[str],
    standard_id: str,
    standard_year: str,
    gri_pages: Sequence[Dict[str, object]],
    sections: Sequence[GRIStandardSection],
) -> Tuple[RequirementLocatorStatus, List[int], List[str], List[str], bool, Optional[str]]:
```

- [ ] **步骤 7：修改 `_locate_gri_requirement` 主逻辑**

保留 `3-3_generic` 与 future watch 的早返回逻辑。其后替换为：

```python
    if not canonical_disclosure_id:
        return (
            RequirementLocatorStatus.NOT_FOUND,
            [],
            [],
            [],
            True,
            "No canonical disclosure ID is available for locator refinement.",
        )

    section = _section_for_standard(sections, standard_id=standard_id, standard_year=standard_year)
    if not section:
        return (
            RequirementLocatorStatus.NOT_FOUND,
            [],
            [],
            [],
            True,
            f"No official GRI PDF section found for {standard_id} {standard_year}.",
        )

    pages, titles, excerpts = _rank_disclosure_pages_within_section(
        canonical_disclosure_id=canonical_disclosure_id,
        section=section,
        gri_pages=gri_pages,
    )

    if len(pages) == 1:
        return RequirementLocatorStatus.FOUND, pages, titles, excerpts, False, None
    if len(pages) > 1:
        return (
            RequirementLocatorStatus.MULTIPLE_CANDIDATES,
            pages,
            titles,
            excerpts,
            True,
            f"Multiple title-page candidates remain within {section.title}; manual locator review is required.",
        )
    return (
        RequirementLocatorStatus.NOT_FOUND,
        [],
        [],
        [],
        True,
        f"No disclosure heading candidate found within {section.title}.",
    )
```

- [ ] **步骤 8：修改 `_requirement_payloads` 调用**

将 `_requirement_payloads` 签名改为：

```python
def _requirement_payloads(
    gri_pages: Sequence[Dict[str, object]],
    sections: Sequence[GRIStandardSection],
) -> List[Dict[str, Any]]:
```

调用 `_locate_gri_requirement` 时新增：

```python
standard_year=item.standard_year,
sections=sections,
```

- [ ] **步骤 9：修改 `build_p0_gri_requirement_pack`**

在抽取 GRI 页文本后新增章节提取，并传入 `_requirement_payloads`：

```python
    gri_pages = extract_pdf_pages(GRI_REFERENCE_PDF_PATH)
    sections = _extract_gri_standard_sections(GRI_REFERENCE_PDF_PATH)
    requirements = [GRIRequirement(**payload) for payload in _requirement_payloads(gri_pages, sections)]
```

- [ ] **步骤 10：运行构建脚本验证收敛效果**

运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe scripts\build_p0_evidence_layer.py
```

期望：

```text
退出码为 0
requirements_written 为 118
locator_counts 中 found 大于等于 100
locator_counts 中 not_found 等于 0
locator_review_required 数量小于等于 18
```

---

## 任务 4：新增 locator audit 输出

**文件：**

- 修改：`C:\Alvin\SUFE\整合实践\envision\src\utils\evidence_layer_utils.py`
- 修改：`C:\Alvin\SUFE\整合实践\envision\scripts\build_p0_evidence_layer.py`
- 新增输出：`C:\Alvin\SUFE\整合实践\envision\data\knowledge_base\manifests\p0_gri_locator_refinement_audit.json`

- [ ] **步骤 1：导入 audit 路径**

在 `src/utils/evidence_layer_utils.py` 的路径导入中加入：

```python
P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH,
```

- [ ] **步骤 2：新增 audit 构建函数**

添加函数：

```python
def build_p0_gri_locator_refinement_audit(
    pack: GRIRequirementPack,
    sections: Sequence[GRIStandardSection],
) -> Dict[str, Any]:
    locator_counts = Counter(req.requirement_locator_status.value for req in pack.requirements)
    review_items = [
        {
            "manifest_item_id": req.manifest_item_id,
            "standard_id": req.standard_id,
            "standard_year": req.standard_year,
            "canonical_disclosure_id": req.canonical_disclosure_id,
            "requirement_locator_status": req.requirement_locator_status.value,
            "official_pdf_page_candidates": req.official_pdf_page_candidates,
            "locator_review_reason": req.locator_review_reason,
        }
        for req in pack.requirements
        if req.locator_review_required
    ]
    return {
        "metadata": pack.metadata.model_dump(mode="json"),
        "locator_counts": dict(sorted(locator_counts.items())),
        "locator_review_required_count": len(review_items),
        "sections": [
            {
                "standard_id": section.standard_id,
                "standard_year": section.standard_year,
                "title": section.title,
                "start_pdf_page": section.start_pdf_page,
                "end_pdf_page": section.end_pdf_page,
            }
            for section in sections
        ],
        "locator_review_required": review_items,
    }
```

- [ ] **步骤 3：新增 audit 写出函数**

添加函数：

```python
def write_gri_locator_refinement_audit(
    audit: Dict[str, Any],
    path: Path = P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH,
) -> None:
    _write_json(path, audit)
```

- [ ] **步骤 4：修改 `build_and_write_p0_evidence_layer`**

在 `build_and_write_p0_evidence_layer` 中复用 `build_p0_gri_requirement_pack()` 的结果后，重新提取 sections 并写出 audit：

```python
    sections = _extract_gri_standard_sections(GRI_REFERENCE_PDF_PATH)
    locator_audit = build_p0_gri_locator_refinement_audit(requirement_pack, sections)
    write_gri_locator_refinement_audit(locator_audit)
```

同时在返回摘要中加入：

```python
"locator_refinement_audit_path": str(P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH),
"locator_review_required_count": len(requirement_pack.locator_review_required),
```

- [ ] **步骤 5：运行构建脚本并检查 audit 文件存在**

运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe scripts\build_p0_evidence_layer.py
C:\ProgramData\miniconda3\envs\envision\python.exe -c "from src.config.paths import P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH; import json; data=json.loads(P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH.read_text(encoding='utf-8')); print(data['locator_review_required_count']); print(len(data['sections']) > 20)"
```

期望：

```text
第一行小于等于 18
第二行 True
```

---

## 任务 5：新增 locator 检查脚本

**文件：**

- 新增：`C:\Alvin\SUFE\整合实践\envision\scripts\inspect_p0_gri_locators.py`

- [ ] **步骤 1：创建检查脚本**

脚本内容：

```python
"""Inspect Stage C2 GRI locator refinement results."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config.paths import P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH, P0_GRI_REQUIREMENT_PACK_PATH
from src.models import GRIRequirementPack


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    pack = GRIRequirementPack.model_validate(_load_json(P0_GRI_REQUIREMENT_PACK_PATH))
    audit = _load_json(P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH)
    review_items = audit.get("locator_review_required", [])
    result = {
        "requirements": len(pack.requirements),
        "locator_counts": audit.get("locator_counts", {}),
        "locator_review_required_count": len(review_items),
        "locator_review_required_sample": review_items[:20],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **步骤 2：运行检查脚本**

运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe scripts\inspect_p0_gri_locators.py
```

期望：

```text
退出码为 0
requirements 为 118
locator_review_required_count 小于等于 18
```

---

## 任务 6：增强阶段 C 验证脚本

**文件：**

- 修改：`C:\Alvin\SUFE\整合实践\envision\scripts\validate_p0_evidence_layer.py`

- [ ] **步骤 1：导入 audit 路径**

在路径导入中加入：

```python
P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH,
```

- [ ] **步骤 2：新增 C2 阈值常量**

在导入后添加：

```python
MIN_FOUND_LOCATORS_AFTER_REFINEMENT = 100
MAX_LOCATOR_REVIEW_ITEMS_AFTER_REFINEMENT = 18
```

- [ ] **步骤 3：加载 audit JSON**

在 `validate_p0_evidence_layer()` 中新增：

```python
    locator_audit: Dict[str, Any] = {}
    if not P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH.exists():
        errors.append(f"Missing locator refinement audit: {P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH}")
    else:
        try:
            locator_audit = _load_json(P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH)
        except Exception as exc:
            errors.append(f"Could not load locator refinement audit: {exc}")
```

- [ ] **步骤 4：新增 C2 收敛阈值校验**

在 `locator_counts` 计算后添加：

```python
    found_count = locator_counts.get(RequirementLocatorStatus.FOUND.value, 0)
    review_count = len(pack.locator_review_required) if pack else 0
    not_found_count = locator_counts.get(RequirementLocatorStatus.NOT_FOUND.value, 0)
    if found_count < MIN_FOUND_LOCATORS_AFTER_REFINEMENT:
        errors.append(
            f"found locators expected >= {MIN_FOUND_LOCATORS_AFTER_REFINEMENT}, got {found_count}"
        )
    if review_count > MAX_LOCATOR_REVIEW_ITEMS_AFTER_REFINEMENT:
        errors.append(
            f"locator_review_required expected <= {MAX_LOCATOR_REVIEW_ITEMS_AFTER_REFINEMENT}, got {review_count}"
        )
    if not_found_count != 0:
        errors.append(f"not_found locators expected 0 after refinement, got {not_found_count}")
```

- [ ] **步骤 5：新增 audit 与 pack 一致性校验**

在 `pack` 存在时添加：

```python
    if pack and locator_audit:
        audit_review_count = int(locator_audit.get("locator_review_required_count", -1))
        if audit_review_count != len(pack.locator_review_required):
            errors.append(
                f"locator audit review count {audit_review_count} does not match pack review count {len(pack.locator_review_required)}"
            )
        audit_counts = locator_audit.get("locator_counts", {})
        for status in RequirementLocatorStatus:
            if int(audit_counts.get(status.value, 0)) != locator_counts.get(status.value, 0):
                errors.append(f"locator audit count for {status.value} does not match requirement pack")
```

- [ ] **步骤 6：运行验证脚本**

运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe scripts\validate_p0_evidence_layer.py
```

期望：

```text
退出码为 0
status 为 ok
errors 为空数组
found 大于等于 100
locator_review_required_count 小于等于 18
not_found 等于 0
```

---

## 任务 7：阶段 C2 阶段门复核

**文件：**

- 只读：`C:\Alvin\SUFE\整合实践\envision\AGENTS.md`
- 只读：`C:\Alvin\SUFE\整合实践\envision\docs\ESG项目全生命周期实施计划.md`

- [ ] **步骤 1：运行语法检查**

运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe -m py_compile src\utils\evidence_layer_utils.py scripts\build_p0_evidence_layer.py scripts\validate_p0_evidence_layer.py scripts\inspect_p0_gri_locators.py
```

期望：

```text
退出码为 0
```

- [ ] **步骤 2：运行构建、检查、验证三件套**

运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe scripts\build_p0_evidence_layer.py
C:\ProgramData\miniconda3\envs\envision\python.exe scripts\inspect_p0_gri_locators.py
C:\ProgramData\miniconda3\envs\envision\python.exe scripts\validate_p0_evidence_layer.py
```

期望：

```text
三个命令退出码均为 0
validate 输出 status 为 ok
validate 输出 errors 为空数组
```

- [ ] **步骤 3：检查变更范围**

运行：

```powershell
git -C C:\Alvin\SUFE\整合实践\envision status --short --untracked-files=all
```

阶段 C2 预期新增或修改：

```text
 M src/config/paths.py
 M src/utils/evidence_layer_utils.py
 M scripts/build_p0_evidence_layer.py
 M scripts/validate_p0_evidence_layer.py
 M data/knowledge_base/manifests/p0_gri_requirement_pack.json
?? scripts/inspect_p0_gri_locators.py
?? data/knowledge_base/manifests/p0_gri_locator_refinement_audit.json
```

阶段 A/B/C 已有文件可能同时出现。不得删除或覆盖。

- [ ] **步骤 4：确认阶段 C2 通过标准**

阶段 C2 通过条件：

```text
1. build_p0_evidence_layer.py 退出码为 0。
2. inspect_p0_gri_locators.py 退出码为 0。
3. validate_p0_evidence_layer.py 退出码为 0。
4. requirement pack 仍为 118 条。
5. report evidence index 仍可通过模型校验。
6. found locator 数量大于等于 100。
7. not_found locator 数量等于 0。
8. locator_review_required_count 小于等于 18。
9. 405-2 和 414-2 源表错误映射继续保留。
10. hash 校验仍覆盖 source manifest、disclosure manifest、远景 PDF、GRI PDF。
11. 不修改 Agent、Prompt、UI、API 或数据库文件。
```

- [ ] **步骤 5：交接给阶段 D**

阶段 C2 通过后，阶段 D 可以按以下规则使用 locator：

```text
requirement_locator_status == found：允许作为自动分析的 GRI 官方页码候选。
requirement_locator_status == multiple_candidates：只能作为候选页集合，输出必须保留 manual_review 标记。
requirement_locator_status == requires_topic_instantiation：不能直接评分，必须结合具体实质性议题实例化。
requirement_locator_status == not_required_for_future_watch：只能进入 readiness/watchlist 叙事，不进入 2024 当前差距评分。
```

---

## 自检

- 范围覆盖：已覆盖 GRI locator 收敛、章节边界、标题页评分、audit 输出、验证阈值和阶段门。
- 边界检查：不触碰 Agent、Prompt、UI、API、数据库、benchmark、monitoring 或外部 dashboard。
- 技术可行性：只读原型验证显示该策略可将 locator 收敛到约 `found=106 / multiple_candidates=8 / not_found=0`。
- 风险控制：剩余多候选不会被隐藏，会继续进入 `locator_review_required` 和 audit JSON。
- 阶段衔接：C2 完成后再进入阶段 D 的 RetrievalAgent/AnalystAgent 对齐。