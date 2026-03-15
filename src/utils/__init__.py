"""
工具模块导出
"""

from src.utils.file_utils import (
    validate_file,
    extract_text,
    extract_text_from_pdf,
    extract_text_from_docx,
    split_text_into_chunks,
    save_text_to_file,
)
from src.utils.validate_utils import (
    validate_file_suffix,
    clean_and_parse_json,
)
from src.utils.similarity_utils import calculate_similarity
from src.utils.llm_utils import call_llm
from src.utils.audit_utils import (
    write_audit_log,
    query_audit_logs,
    verify_log_integrity,
    export_audit_logs_to_json,
)
from src.utils.hash_utils import (
    generate_sha256_hash,
    verify_sha256_hash,
)
from src.utils.exception_utils import (
    BaseESGException,
    ValidationException,
    FileProcessingException,
    LLMCallException,
    RuleMatchException,
    AuditException,
)
from src.utils.config_utils import (
    load_json_config,
    load_topic_rules,
    load_esg_standards,
    load_match_rules,
    load_prompt_template,
)
from src.utils.rule_match import (
    RuleMatcher,
    get_rule_matcher,
)
from src.utils.chroma_utils import (
    save_corpus_to_db,
    get_corpus_list,
    get_corpus_detail,
    search_corpus,
    get_esg_metrics,
    get_chroma_manager,
)

__all__ = [
    # 文件处理
    "validate_file",
    "extract_text",
    "extract_text_from_pdf",
    "extract_text_from_docx",
    "split_text_into_chunks",
    "save_text_to_file",
    # 校验
    "validate_file_suffix",
    "clean_and_parse_json",
    # 相似度
    "calculate_similarity",
    # LLM
    "call_llm",
    # 审计日志
    "write_audit_log",
    "query_audit_logs",
    "verify_log_integrity",
    "export_audit_logs_to_json",
    # 哈希
    "generate_sha256_hash",
    "verify_sha256_hash",
    # 异常
    "BaseESGException",
    "ValidationException",
    "FileProcessingException",
    "LLMCallException",
    "RuleMatchException",
    "AuditException",
    # 配置
    "load_json_config",
    "load_topic_rules",
    "load_esg_standards",
    "load_match_rules",
    "load_prompt_template",
    # 规则匹配
    "RuleMatcher",
    "get_rule_matcher",
    # Chroma
    "save_corpus_to_db",
    "get_corpus_list",
    "get_corpus_detail",
    "search_corpus",
    "get_esg_metrics",
    "get_chroma_manager",
]
