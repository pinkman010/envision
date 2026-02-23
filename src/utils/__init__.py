"""
工具模块 - 各类通用工具函数
"""
# 异常类
from src.utils.exception_utils import (
    BaseESGException,
    ValidationException,
    FileProcessingException,
    LLMCallException,
    RuleMatchException,
    AuditException,
)

# 文件处理
from src.utils.file_utils import (
    validate_file,
    extract_text,
    extract_text_from_pdf,
    extract_text_from_docx,
    split_text_into_chunks,
    save_text_to_file,
)

# 配置加载
from src.utils.config_utils import (
    load_json_config,
    load_topic_rules,
    load_esg_standards,
    load_match_rules,
    load_prompt_template,
)

# 校验工具
from src.utils.validate_utils import (
    validate_json_format,
    validate_extraction_result,
    validate_file_suffix,
    clean_and_parse_json,
)

# 相似度校验
from src.utils.similarity_utils import (
    calculate_similarity,
    validate_similarity,
    validate_similarity_by_line,
)

# 审计日志
from src.utils.audit_utils import (
    init_audit_db,
    write_audit_log,
    query_audit_logs,
)

# 哈希工具
from src.utils.hash_utils import (
    generate_sha256_hash,
    verify_sha256_hash,
)

# LLM调用
from src.utils.llm_utils import call_llm

# 规则匹配
from src.utils.rule_match import RuleMatcher, get_rule_matcher

# Chroma向量数据库
from src.utils.chroma_utils import (
    ChromaManager,
    get_chroma_manager,
    save_corpus_to_db,
    get_corpus_list,
    get_corpus_detail,
    search_corpus,
    get_esg_metrics,
    ESG_INDICATORS,
    UNIT_CONVERSION,
)

__all__ = [
    # 异常类
    "BaseESGException",
    "ValidationException",
    "FileProcessingException",
    "LLMCallException",
    "RuleMatchException",
    "AuditException",
    # 文件处理
    "validate_file",
    "extract_text",
    "extract_text_from_pdf",
    "extract_text_from_docx",
    "split_text_into_chunks",
    "save_text_to_file",
    # 配置加载
    "load_json_config",
    "load_topic_rules",
    "load_esg_standards",
    "load_match_rules",
    "load_prompt_template",
    # 校验工具
    "validate_json_format",
    "validate_extraction_result",
    "validate_file_suffix",
    "clean_and_parse_json",
    # 相似度校验
    "calculate_similarity",
    "validate_similarity",
    "validate_similarity_by_line",
    # 审计日志
    "init_audit_db",
    "write_audit_log",
    "query_audit_logs",
    # 哈希工具
    "generate_sha256_hash",
    "verify_sha256_hash",
    # LLM调用
    "call_llm",
    # 规则匹配
    "RuleMatcher",
    "get_rule_matcher",
    # Chroma向量数据库
    "ChromaManager",
    "get_chroma_manager",
    "save_corpus_to_db",
    "get_corpus_list",
    "get_corpus_detail",
    "search_corpus",
    "get_esg_metrics",
    "ESG_INDICATORS",
    "UNIT_CONVERSION",
]
