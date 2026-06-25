# P0 阶段 C：GRI 条款与报告证据层实施计划

> **给执行代理的说明：** 必须使用 `superpowers:subagent-driven-development` 按任务执行本计划。步骤使用 `- [ ]` 复选框跟踪。执行子代理不得使用 `list_agents`、`wait_agent`、`send_message` 或 `followup_task`。

**目标：** 构建 P0 GRI 条款定位包与远景 2024 中文 ESG 报告证据层，使每个 P0 disclosure 在进入 Agent 前都有可追溯的标准来源、报告证据候选、页码和文件哈希。

**架构：** 保持阶段 B 的 `AnalysisRun` 领域契约不变，在其下游新增两个可版本化 JSON 资产：`p0_gri_requirement_pack.json` 和 `p0_report_evidence_index.json`。本阶段只做标准/报告证据结构化与验证，不修改 Agent、Prompt、Streamlit、API 或数据库。

**技术栈：** Python 3、Pydantic v2、pypdf、hashlib、json、pathlib、re、项目 Conda 环境 `C:\ProgramData\miniconda3\envs\envision\python.exe`。

---

## 1. 范围

本计划覆盖阶段 C 的第一轮可执行实现：

- 从 `p0_gri_disclosure_manifest.json` 生成 P0 GRI requirement pack。
- 从 GRI 官方英文合订本中为 disclosure 尝试定位英文标准页码候选。
- 从远景能源 2024 中文 ESG 报告中生成带页码、chunk_id、source hash 的报告 evidence chunks。
- 建立验证脚本，证明 requirement pack 与 evidence index 可读、可校验、可供后续 RetrievalAgent/AnalystAgent 使用。

本计划不做：

- 不调用外部 LLM 翻译 GRI 条款。
- 不把中文工作译文写成权威条款。
- 不修改 `src/agent`。
- 不修改 `templates/prompt_templates`。
- 不修改 `src/ui`。
- 不新增 SQLite 表。
- 不连接 `C:\Users\43480\Desktop\esg-dashboard`。
- 不实现多企业对标或舆情监测。

## 2. 输入

- `C:\Alvin\SUFE\整合实践\envision\data\knowledge_base\manifests\p0_source_manifest.json`
- `C:\Alvin\SUFE\整合实践\envision\data\knowledge_base\manifests\p0_gri_disclosure_manifest.json`
- `C:\Alvin\SUFE\整合实践\envision\data\knowledge_base\standards\gri_reference\GRI_Standards_Official_Consolidated_Set_en.pdf`
- `C:\Alvin\SUFE\整合实践\envision\data\knowledge_base\peer_reports\Envision Energy 2024-zh.pdf`

## 3. 输出

- `C:\Alvin\SUFE\整合实践\envision\data\knowledge_base\manifests\p0_gri_requirement_pack.json`
- `C:\Alvin\SUFE\整合实践\envision\data\knowledge_base\manifests\p0_report_evidence_index.json`

这两个输出是 JSON manifest，应该进入 Git，因为 `.gitignore` 已允许 `data/knowledge_base/manifests/*.json`。

## 4. 文件清单

- 修改：`C:\Alvin\SUFE\整合实践\envision\src\config\paths.py`
- 修改：`C:\Alvin\SUFE\整合实践\envision\src\models\__init__.py`
- 新建：`C:\Alvin\SUFE\整合实践\envision\src\models\evidence_layer.py`
- 新建：`C:\Alvin\SUFE\整合实践\envision\src\utils\pdf_text_utils.py`
- 新建：`C:\Alvin\SUFE\整合实践\envision\src\utils\evidence_layer_utils.py`
- 新建：`C:\Alvin\SUFE\整合实践\envision\scripts\build_p0_evidence_layer.py`
- 新建：`C:\Alvin\SUFE\整合实践\envision\scripts\validate_p0_evidence_layer.py`

不得 stage、commit 或格式化无关文件，除非用户明确授权 Git 操作。

---

## 任务 1：新增阶段 C 路径常量

**文件：**

- 修改：`C:\Alvin\SUFE\整合实践\envision\src\config\paths.py`

- [ ] **步骤 1：新增知识库源文件路径**

在现有 manifest 路径常量后添加：

```python
STANDARDS_DIR: Path = KNOWLEDGE_BASE_DIR / "standards"
PEER_REPORTS_DIR: Path = KNOWLEDGE_BASE_DIR / "peer_reports"
GRI_REFERENCE_DIR: Path = STANDARDS_DIR / "gri_reference"
GRI_REFERENCE_PDF_PATH: Path = GRI_REFERENCE_DIR / "GRI_Standards_Official_Consolidated_Set_en.pdf"
ENVISION_2024_ZH_REPORT_PATH: Path = PEER_REPORTS_DIR / "Envision Energy 2024-zh.pdf"
P0_GRI_REQUIREMENT_PACK_PATH: Path = MANIFESTS_DIR / "p0_gri_requirement_pack.json"
P0_REPORT_EVIDENCE_INDEX_PATH: Path = MANIFESTS_DIR / "p0_report_evidence_index.json"
```

- [ ] **步骤 2：加入 `ensure_all_paths`**

在 `required_dirs` 中 `MANIFESTS_DIR` 后添加：

```python
STANDARDS_DIR,
PEER_REPORTS_DIR,
GRI_REFERENCE_DIR,
```

这些目录创建是安全的。不得创建或覆盖 PDF。

- [ ] **步骤 3：验证路径导入**

运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe -c "from src.config.paths import P0_GRI_REQUIREMENT_PACK_PATH, P0_REPORT_EVIDENCE_INDEX_PATH; print(P0_GRI_REQUIREMENT_PACK_PATH.name); print(P0_REPORT_EVIDENCE_INDEX_PATH.name)"
```

期望输出：

```text
p0_gri_requirement_pack.json
p0_report_evidence_index.json
```

---

## 任务 2：新增证据层领域模型

**文件：**

- 新建：`C:\Alvin\SUFE\整合实践\envision\src\models\evidence_layer.py`
- 修改：`C:\Alvin\SUFE\整合实践\envision\src\models\__init__.py`

- [ ] **步骤 1：创建证据层模型**

`src/models/evidence_layer.py` 必须包含：

```text
RequirementLocatorStatus
TranslationStatus
GRIRequirement
ReportEvidenceChunk
EvidenceLayerMetadata
GRIRequirementPack
ReportEvidenceIndex
```

模型要求：

- 使用 Pydantic v2。
- `GRIRequirement` 记录 disclosure 对应的 GRI 条款定位状态、官方 PDF 页码候选、英文标题候选、英文摘录、中文工作译文状态、source hash。
- `ReportEvidenceChunk` 记录报告证据片段，必须包含 `chunk_id`、`source_document_relative_path`、`source_document_sha256`、`pdf_page`、`char_start`、`char_end`、`text`。
- `EvidenceLayerMetadata` 记录构建时间、source manifest hash、disclosure manifest hash、报告 PDF hash、GRI PDF hash、chunk 参数。
- `GRIRequirementPack` 保存 `requirements`。
- `ReportEvidenceIndex` 保存 `chunks`。

- [ ] **步骤 2：导出模型**

更新 `src/models/__init__.py`，在保留阶段 B 导出的基础上，新增导出：

```text
EvidenceLayerMetadata
GRIRequirement
GRIRequirementPack
ReportEvidenceChunk
ReportEvidenceIndex
RequirementLocatorStatus
TranslationStatus
```

- [ ] **步骤 3：验证模型导入**

运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe -c "from src.models import GRIRequirement, ReportEvidenceChunk, RequirementLocatorStatus; print(RequirementLocatorStatus.FOUND.value)"
```

期望输出：

```text
found
```

---

## 任务 3：新增 PDF 文本抽取工具

**文件：**

- 新建：`C:\Alvin\SUFE\整合实践\envision\src\utils\pdf_text_utils.py`

- [ ] **步骤 1：创建 PDF 工具模块**

必须提供：

```python
sha256_file(path: Path) -> str
extract_pdf_pages(path: Path) -> List[Dict[str, object]]
chunk_text_by_page(...) -> List[Dict[str, object]]
```

要求：

- `sha256_file` 以大写十六进制返回 SHA-256。
- `extract_pdf_pages` 使用 `pypdf.PdfReader`，返回每页 `pdf_page` 与 `text`。
- `chunk_text_by_page` 按页切分，不跨页合并。
- 每个 chunk 的 `chunk_id` 必须稳定，基于 source hash、页码、char range 和文本片段生成。
- `chunk_overlap` 必须小于 `chunk_size`，否则抛出 `ValueError`。

- [ ] **步骤 2：验证 PDF 可读性**

运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe -c "from src.config.paths import ENVISION_2024_ZH_REPORT_PATH; from src.utils.pdf_text_utils import extract_pdf_pages; pages=extract_pdf_pages(ENVISION_2024_ZH_REPORT_PATH); print(len(pages)); print(bool(pages[0]['text']))"
```

期望输出：

```text
78
True
```

---

## 任务 4：新增证据层构建工具

**文件：**

- 新建：`C:\Alvin\SUFE\整合实践\envision\src\utils\evidence_layer_utils.py`

- [ ] **步骤 1：创建 GRI 定位与证据层构建模块**

该模块职责：

- 通过 `load_p0_gri_disclosure_manifest()` 和 `load_p0_disclosure_items()` 读取阶段 B manifest。
- 从 `p0_source_manifest.json` 读取 source hash。
- 抽取 GRI 官方 PDF 页文本。
- 根据 disclosure ID 和 standard ID 搜索 GRI 页码候选。
- 构建 `GRIRequirementPack`。
- 构建 `ReportEvidenceIndex`。
- 以 UTF-8 无 BOM 写出两个 JSON 文件。

GRI 定位搜索规则：

```text
canonical_disclosure_id 精确短语：Disclosure {canonical_disclosure_id}
紧凑短语：{canonical_disclosure_id} 后跟空格
标准兜底：去掉 GRI 前缀后的 standard_id，例如 GRI 305 -> 305
```

定位状态规则：

- `canonical_disclosure_id == "3-3_generic"` 时为 `requires_topic_instantiation`。
- `analysis_mode != current_gap` 且没有 disclosure ID 时为 `not_required_for_future_watch`。
- 找到一个候选页时为 `found`。
- 找到多个候选页时为 `multiple_candidates`。
- 当前缺口 disclosure 找不到候选页时为 `not_found`。

写出前必须使用：

```python
GRIRequirementPack.model_validate(...)
ReportEvidenceIndex.model_validate(...)
```

- [ ] **步骤 2：验证工具导入**

运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe -c "import src.utils.evidence_layer_utils as u; print(hasattr(u, 'build_p0_gri_requirement_pack')); print(hasattr(u, 'build_p0_report_evidence_index'))"
```

期望输出：

```text
True
True
```

---

## 任务 5：新增阶段 C 构建脚本

**文件：**

- 新建：`C:\Alvin\SUFE\整合实践\envision\scripts\build_p0_evidence_layer.py`

- [ ] **步骤 1：创建构建脚本**

脚本必须：

1. 将项目根目录加入 `sys.path`。
2. 调用 `build_p0_gri_requirement_pack()`。
3. 调用 `build_p0_report_evidence_index()`。
4. 写出：
   - `P0_GRI_REQUIREMENT_PACK_PATH`
   - `P0_REPORT_EVIDENCE_INDEX_PATH`
5. 输出 JSON 摘要：

```json
{
  "status": "ok",
  "requirements_written": 118,
  "report_chunks_written": "positive integer",
  "requirement_pack_path": "...p0_gri_requirement_pack.json",
  "report_evidence_index_path": "...p0_report_evidence_index.json"
}
```

任一输出无法通过模型校验时，脚本必须非 0 退出。

- [ ] **步骤 2：运行构建脚本**

在项目根目录运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe scripts\build_p0_evidence_layer.py
```

期望关键输出：

```json
{
  "status": "ok",
  "requirements_written": 118
}
```

`report_chunks_written` 必须大于 0。

---

## 任务 6：新增阶段 C 验证脚本

**文件：**

- 新建：`C:\Alvin\SUFE\整合实践\envision\scripts\validate_p0_evidence_layer.py`

- [ ] **步骤 1：创建验证脚本**

脚本必须校验：

- requirement pack JSON 存在且可加载。
- report evidence index JSON 存在且可加载。
- requirement 数量为 118。
- requirement 模式计数为 115 / 1 / 2。
- requirement 的 `manifest_item_id` 唯一。
- requirement 保留 `405-2` 与 `414-2` 的源表错误映射。
- 报告 evidence chunk 数量大于 0。
- 每个 chunk 有 `chunk_id`、`pdf_page`、`source_document_sha256` 和非空 `text`。
- report evidence index 使用的报告 SHA-256 与 `p0_source_manifest.json` 一致。
- requirement pack 使用的 GRI PDF SHA-256 与 `p0_source_manifest.json` 一致。
- 输出 locator 统计：
  - `found`
  - `multiple_candidates`
  - `not_found`
  - `requires_topic_instantiation`
  - `not_required_for_future_watch`

验证输出必须包含：

```json
{
  "status": "ok or failed",
  "requirements": 118,
  "report_chunks": "positive integer",
  "mode_counts": {
    "current_gap": 115,
    "readiness_2026": 1,
    "watchlist_2027": 2
  },
  "locator_counts": {},
  "errors": []
}
```

- [ ] **步骤 2：运行验证脚本**

运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe scripts\validate_p0_evidence_layer.py
```

期望：

```text
当 status 为 ok 时，退出码为 0
```

如果 `not_found` locator 数量不为 0，脚本仍可返回 `ok` 的前提是每个 `not_found` 项都被明确列入 `locator_review_required`。这保证阶段 C 可以带着已披露的人工复核项前进，但不能隐藏标准页码未定位的问题。

---

## 任务 7：阶段 C 阶段门复核

**文件：**

- 只读：`C:\Alvin\SUFE\整合实践\envision\docs\ESG项目全生命周期实施计划.md`
- 只读：`C:\Alvin\SUFE\整合实践\envision\AGENTS.md`

- [ ] **步骤 1：检查变更范围**

运行：

```powershell
git -C C:\Alvin\SUFE\整合实践\envision status --short --untracked-files=all
```

阶段 C 预期变更：

```text
 M src/config/paths.py
 M src/models/__init__.py
?? src/models/evidence_layer.py
?? src/utils/pdf_text_utils.py
?? src/utils/evidence_layer_utils.py
?? scripts/build_p0_evidence_layer.py
?? scripts/validate_p0_evidence_layer.py
?? data/knowledge_base/manifests/p0_gri_requirement_pack.json
?? data/knowledge_base/manifests/p0_report_evidence_index.json
```

阶段 A/B 已有文件可能同时出现。不得删除或覆盖。

- [ ] **步骤 2：确认阶段 C 第一阶段门**

阶段 C 第一阶段门通过条件：

```text
1. build_p0_evidence_layer.py 退出码为 0。
2. validate_p0_evidence_layer.py 退出码为 0。
3. requirement pack 有 118 行。
4. report evidence index 的 chunk 数量大于 0。
5. source hash 与 p0_source_manifest.json 一致。
6. 405-2 和 414-2 源表错误映射继续保留。
7. 缺失 GRI locator 的项目如存在，必须明确列入人工复核清单。
8. 不修改 Agent、Prompt、UI、API 或数据库文件。
```

- [ ] **步骤 3：交接给阶段 D**

阶段 C 通过后，下一阶段目标是：

```text
AnalystAgent input = retrieval_result + GRIRequirementPack + ReportEvidenceIndex + DisclosureManifestItem
AnalystAgent output = DisclosureAssessment-compatible dicts
Prompt rule = no evidence -> manual_review; future requirements -> readiness/watchlist narrative only
```

不要在阶段 C 内启动 Agent/Prompt 改造。

---

## 自检

- 范围覆盖：已覆盖 GRI requirement pack、报告 evidence chunks、source hash、页码/chunk 可追溯、验证脚本和阶段 C 阶段门。
- 边界检查：不触碰 Agent、Prompt、UI、API、数据库、benchmark、monitoring 或外部 dashboard。
- 类型一致性：requirement/evidence 模型与阶段 B 的 `AnalysisRun` 模型分离，但可被后续 Agent/Prompt 使用。
- 验证环境：全部使用 `C:\ProgramData\miniconda3\envs\envision\python.exe`。