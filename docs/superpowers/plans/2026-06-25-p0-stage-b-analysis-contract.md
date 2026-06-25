# P0 阶段 B：分析契约实施计划

> **给执行代理的说明：** 必须使用 `superpowers:subagent-driven-development` 按任务执行本计划。步骤使用 `- [ ]` 复选框跟踪。执行子代理不得使用 `list_agents`、`wait_agent`、`send_message` 或 `followup_task`。

**目标：** 将 `p0_gri_disclosure_manifest.json` 落地为后端可读取、可校验、可序列化的 P0 单报告分析领域契约。

**架构：** 保持现有 `OrchestratorAgent -> CorpusAgent -> RetrievalAgent -> AnalystAgent -> AdvisorAgent` 主链路不变。本计划只新增领域模型、manifest 读取器和最小验证脚本，为后续 Agent/Prompt 改造提供稳定数据契约。暂不接数据库、暂不改 Streamlit 页面、暂不改 LLM prompt。

**技术栈：** Python 3、Pydantic v2、标准库 `json/pathlib/collections/datetime/uuid`、项目 Conda 环境 `C:\ProgramData\miniconda3\envs\envision\python.exe`。

---

## 1. 范围

本计划只实现阶段 B 的后端契约基础：

- 读取 `data/knowledge_base/manifests/p0_source_manifest.json`。
- 读取 `data/knowledge_base/manifests/p0_gri_disclosure_manifest.json`。
- 将 manifest 行转换为强类型 `DisclosureManifestItem`。
- 定义 `AnalysisRun`、`DisclosureAssessment`、`Evidence`、`ReviewDecision`。
- 提供可重复运行的验证脚本，证明契约可读、可校验、可序列化。

本计划不做：

- 不修改 `AnalystAgent` 的 LLM 逻辑。
- 不修改 `templates/prompt_templates`。
- 不新增数据库表。
- 不修改 Streamlit 页面。
- 不抽取 GRI 官方条款正文。
- 不把 `readiness_2026` 或 `watchlist_2027` 计入 2024 缺口评分。

## 2. 文件清单

- 修改：`C:\Alvin\SUFE\整合实践\envision\src\config\paths.py`
- 新建：`C:\Alvin\SUFE\整合实践\envision\src\models\__init__.py`
- 新建：`C:\Alvin\SUFE\整合实践\envision\src\models\analysis_contract.py`
- 新建：`C:\Alvin\SUFE\整合实践\envision\src\utils\manifest_utils.py`
- 新建：`C:\Alvin\SUFE\整合实践\envision\scripts\validate_p0_contract.py`

不得 stage、commit 或格式化无关文件，除非用户明确授权 Git 操作。

---

## 任务 1：新增 manifest 路径常量

**文件：**

- 修改：`C:\Alvin\SUFE\整合实践\envision\src\config\paths.py`

- [ ] **步骤 1：新增知识库路径常量**

在 `EXPORT_RESULTS_DIR` 后添加：

```python
KNOWLEDGE_BASE_DIR: Path = DATA_DIR / "knowledge_base"
MANIFESTS_DIR: Path = KNOWLEDGE_BASE_DIR / "manifests"
P0_SOURCE_MANIFEST_PATH: Path = MANIFESTS_DIR / "p0_source_manifest.json"
P0_GRI_DISCLOSURE_MANIFEST_PATH: Path = MANIFESTS_DIR / "p0_gri_disclosure_manifest.json"
```

- [ ] **步骤 2：加入 `ensure_all_paths`**

在 `required_dirs` 中 `EXPORT_RESULTS_DIR` 后添加：

```python
KNOWLEDGE_BASE_DIR,
MANIFESTS_DIR,
```

只创建目录，不创建文件。

- [ ] **步骤 3：验证路径导入**

运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe -c "from src.config.paths import P0_GRI_DISCLOSURE_MANIFEST_PATH; print(P0_GRI_DISCLOSURE_MANIFEST_PATH.name)"
```

期望输出：

```text
p0_gri_disclosure_manifest.json
```

---

## 任务 2：创建 P0 分析领域模型

**文件：**

- 新建：`C:\Alvin\SUFE\整合实践\envision\src\models\analysis_contract.py`
- 新建：`C:\Alvin\SUFE\整合实践\envision\src\models\__init__.py`

- [ ] **步骤 1：创建 `analysis_contract.py`**

模型必须定义：

```text
AnalysisMode
CanonicalStatus
AssessmentVerdict
ReviewStatus
AnalysisRunStatus
SourceDocumentRef
DisclosureManifestItem
Evidence
DisclosureAssessment
ReviewDecision
AnalysisRun
```

要求：

- 使用 Pydantic v2。
- `AnalysisMode` 包含 `current_gap`、`readiness_2026`、`watchlist_2027`。
- `CanonicalStatus` 包含 `confirmed_from_report_index`、`source_typo_confirmed`、`requires_topic_instantiation`、`future_standard_not_current_gap`。
- `DisclosureManifestItem` 对 `current_gap` 行要求 `canonical_disclosure_id` 非空。
- `Evidence.relevance` 限定在 `0.0` 到 `1.0`。
- `DisclosureAssessment.confidence` 限定在 `0.0` 到 `1.0`。
- `AnalysisRun` 能保存 `source_documents`、`assessments`、`review_decisions` 和 `summary`。

- [ ] **步骤 2：创建 `src/models/__init__.py`**

导出任务 2 中的全部模型，保持后续 import 统一从 `src.models` 进入。

- [ ] **步骤 3：验证模型导入与序列化**

运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe -c "from src.models import AnalysisRun; r=AnalysisRun(report_id='envision_2024_zh', standard_profile_id='p0_gri_disclosure_manifest', manifest_version='0.1'); print(r.model_dump()['status'])"
```

期望输出：

```text
AnalysisRunStatus.CREATED
```

---

## 任务 3：创建 manifest 读取与契约校验工具

**文件：**

- 新建：`C:\Alvin\SUFE\整合实践\envision\src\utils\manifest_utils.py`

- [ ] **步骤 1：实现读取函数**

必须提供：

```python
load_p0_source_manifest
load_p0_gri_disclosure_manifest
load_p0_source_documents
load_p0_embedded_source_documents
load_p0_disclosure_items
count_disclosures_by_mode
validate_p0_manifest_contract
build_empty_p0_analysis_run
```

- [ ] **步骤 2：实现基础计数校验**

`validate_p0_manifest_contract()` 必须校验：

```text
total_disclosures = 118
current_gap = 115
readiness_2026 = 1
watchlist_2027 = 2
```

- [ ] **步骤 3：实现 source manifest 漂移校验**

比较 `p0_source_manifest.json` 的 sources 投影结果，与 `p0_gri_disclosure_manifest.json` 内嵌 `source_documents` 是否完全一致。

比较字段：

```text
relative_path
document_type
sha256
provenance_status
```

不一致时返回 `status = failed` 并写入 `errors`。

- [ ] **步骤 4：实现 disclosure 身份校验**

必须校验：

- 所有 `manifest_item_id` 唯一。
- 所有 `current_gap` 行的 `(analysis_mode, canonical_disclosure_id)` 唯一。
- 所有 `current_gap` 行的 `canonical_disclosure_id` 非空。

重复或缺失时返回 `status = failed`。

- [ ] **步骤 5：实现 405/414 强校验**

`405-2` 必须且只能有一条，并满足：

```text
standard_id = GRI 405
source_disclosure_id = 405-1
canonical_disclosure_id = 405-2
canonical_status = source_typo_confirmed
report_index_pdf_page = 75
report_index_report_page = 74
known_source_issues 中存在对应记录
```

`414-2` 必须且只能有一条，并满足：

```text
standard_id = GRI 414
source_disclosure_id = 414-1
canonical_disclosure_id = 414-2
canonical_status = source_typo_confirmed
report_index_pdf_page = 76
report_index_report_page = 75
known_source_issues 中存在对应记录
```

- [ ] **步骤 6：验证工具导入**

运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe -c "from src.utils.manifest_utils import validate_p0_manifest_contract; print(validate_p0_manifest_contract()['status'])"
```

期望输出：

```text
ok
```

---

## 任务 4：新增可重复运行的契约验证脚本

**文件：**

- 新建：`C:\Alvin\SUFE\整合实践\envision\scripts\validate_p0_contract.py`

- [ ] **步骤 1：创建验证脚本**

脚本必须：

1. 将项目根目录加入 `sys.path`。
2. 调用 `validate_p0_manifest_contract()`。
3. 调用 `load_p0_disclosure_items(AnalysisMode.CURRENT_GAP)`。
4. 调用 `load_p0_source_documents()`。
5. 构造 `build_empty_p0_analysis_run()`。
6. 用 `model_dump(mode="json")` 和 `AnalysisRun.model_validate()` 验证可序列化。
7. 输出 JSON 验证摘要。
8. 当 `status != ok` 或关键布尔字段为 false 时返回非 0。

输出必须包含：

```json
{
  "status": "ok",
  "manifest_version": "0.1",
  "total_disclosures": 118,
  "current_gap": 115,
  "readiness_2026": 1,
  "watchlist_2027": 2,
  "current_gap_items_loaded": 115,
  "source_documents_loaded": 2,
  "source_documents_match_manifest": true,
  "manifest_item_ids_unique": true,
  "current_gap_canonical_ids_unique": true,
  "has_405_2_typo": true,
  "has_414_2_typo": true,
  "has_3_3_scope_marker": true,
  "analysis_run_serializable": true,
  "analysis_run_id_startswith_expected_prefix": true,
  "errors": []
}
```

- [ ] **步骤 2：运行验证脚本**

在项目根目录运行：

```powershell
C:\ProgramData\miniconda3\envs\envision\python.exe scripts\validate_p0_contract.py
```

期望：退出码为 `0`，且 `status = ok`。

---

## 任务 5：阶段 B 阶段门复核

**文件：**

- 只读：`C:\Alvin\SUFE\整合实践\envision\docs\ESG项目全生命周期实施计划.md`
- 只读：`C:\Alvin\SUFE\整合实践\envision\AGENTS.md`

- [ ] **步骤 1：检查变更范围**

运行：

```powershell
git -C C:\Alvin\SUFE\整合实践\envision status --short --untracked-files=all
```

本计划相关变更应只包括：

```text
 M src/config/paths.py
?? src/models/__init__.py
?? src/models/analysis_contract.py
?? src/utils/manifest_utils.py
?? scripts/validate_p0_contract.py
```

前序阶段遗留的 `AGENTS.md`、manifest JSON、生命周期计划、prompt schema 文档可能同时出现。不得删除或覆盖。

- [ ] **步骤 2：确认阶段门**

阶段 B 技术通过条件：

```text
1. validate_p0_contract.py 返回 status ok。
2. 118 条 disclosure 可加载。
3. current_gap 数量为 115。
4. readiness_2026 数量为 1。
5. watchlist_2027 数量为 2。
6. source manifest 与 disclosure manifest 内嵌 source documents 一致。
7. manifest_item_id 唯一。
8. current_gap canonical_disclosure_id 唯一。
9. 405-2 与 414-2 源表错误映射被保留。
10. AnalysisRun 可序列化并可由 Pydantic 回读。
```

- [ ] **步骤 3：交接给阶段 C**

阶段 B 通过后，下一阶段目标是：

```text
GRI requirement pack
Report evidence index
Source hash consistency
Page/chunk traceability
```

不要在阶段 B 中启动 Agent/Prompt 改造。

---

## 自检

- 范围覆盖：已覆盖阶段 B 领域契约、manifest 读取、`AnalysisRun` 构造、source typo 保留、机器验证。
- 边界检查：不触碰 LLM prompt、Streamlit、SQLite、GRI 条款抽取、benchmark 或 monitoring。
- 类型一致性：`AnalysisMode`、`CanonicalStatus`、`DisclosureManifestItem`、`AnalysisRun` 在模型、工具和验证脚本中命名一致。
- 验证环境：全部使用 `C:\ProgramData\miniconda3\envs\envision\python.exe`。