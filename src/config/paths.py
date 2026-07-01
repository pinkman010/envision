"""
项目全局路径统一配置（避免硬编码路径）
所有路径均为Path对象，支持跨平台
"""

from pathlib import Path
from typing import List

# ------------------------------
# 核心根目录
# ------------------------------
ROOT_DIR: Path = Path(__file__).parent.parent.parent.resolve()  # 项目根目录（绝对路径）
SRC_DIR: Path = ROOT_DIR / "src"  # 核心源码目录

# ------------------------------
# 外置配置目录（业务规则、模板）
# ------------------------------
CONFIG_DIR: Path = ROOT_DIR / "templates"
PROMPT_TEMPLATES_DIR: Path = CONFIG_DIR / "prompt_templates"
PROMPT_DIR: Path = PROMPT_TEMPLATES_DIR  # 别名，用于兼容测试
RULE_TEMPLATES_DIR: Path = CONFIG_DIR / "rule_templates"

# ------------------------------
# 数据存储目录（运行时生成，敏感内容不上传Git）
# ------------------------------
DATA_DIR: Path = ROOT_DIR / "data"
CHROMA_DB_DIR: Path = DATA_DIR / "chroma_db"
SQLITE_DB_DIR: Path = DATA_DIR / "sqlite_db"
RAW_CORPUS_DIR: Path = DATA_DIR / "raw_corpus"
EXPORT_RESULTS_DIR: Path = DATA_DIR / "export_results"
KNOWLEDGE_BASE_DIR: Path = DATA_DIR / "knowledge_base"
MANIFESTS_DIR: Path = KNOWLEDGE_BASE_DIR / "manifests"
P0_SOURCE_MANIFEST_PATH: Path = MANIFESTS_DIR / "p0_source_manifest.json"
P0_GRI_DISCLOSURE_MANIFEST_PATH: Path = MANIFESTS_DIR / "p0_gri_disclosure_manifest.json"
STANDARDS_DIR: Path = KNOWLEDGE_BASE_DIR / "standards"
PEER_REPORTS_DIR: Path = KNOWLEDGE_BASE_DIR / "peer_reports"
GRI_REFERENCE_DIR: Path = STANDARDS_DIR / "gri_reference"
GRI_REFERENCE_PDF_PATH: Path = GRI_REFERENCE_DIR / "GRI_Standards_Official_Consolidated_Set_en.pdf"
ENVISION_2024_ZH_REPORT_PATH: Path = PEER_REPORTS_DIR / "Envision Energy 2024-zh.pdf"
P0_GRI_REQUIREMENT_PACK_PATH: Path = MANIFESTS_DIR / "p0_gri_requirement_pack.json"
P0_GRI_REQUIREMENT_CHECKLIST_PATH: Path = MANIFESTS_DIR / "p0_gri_requirement_checklist.json"
P0_REPORT_EVIDENCE_INDEX_PATH: Path = MANIFESTS_DIR / "p0_report_evidence_index.json"
P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH: Path = MANIFESTS_DIR / "p0_gri_locator_refinement_audit.json"

# ------------------------------
# UI页面目录
# ------------------------------
UI_PAGES_DIR: Path = SRC_DIR / "ui" / "pages"

# ------------------------------
# 普通运行日志目录（区分审计日志，.gitignore完全忽略）
# ------------------------------
LOGS_DIR: Path = ROOT_DIR / "logs"
APP_LOG_DIR: Path = LOGS_DIR / "app"  # 应用运行日志
API_LOG_DIR: Path = LOGS_DIR / "api"  # API请求日志


# ------------------------------
# 确保所有必要的目录存在
# ------------------------------
def ensure_all_paths() -> None:
    """
    确保项目所有必要的目录存在，不存在则自动创建
    仅创建目录，不创建文件
    """
    required_dirs: List[Path] = [
        # 配置目录
        CONFIG_DIR,
        PROMPT_TEMPLATES_DIR,
        RULE_TEMPLATES_DIR,
        # 数据目录
        DATA_DIR,
        CHROMA_DB_DIR,
        SQLITE_DB_DIR,
        RAW_CORPUS_DIR,
        EXPORT_RESULTS_DIR,
        KNOWLEDGE_BASE_DIR,
        MANIFESTS_DIR,
        STANDARDS_DIR,
        PEER_REPORTS_DIR,
        GRI_REFERENCE_DIR,
        # UI目录
        UI_PAGES_DIR,
        # 日志目录
        LOGS_DIR,
        APP_LOG_DIR,
        API_LOG_DIR,
    ]
    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
