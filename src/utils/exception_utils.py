"""
全局异常处理工具：统一异常类、错误码定义
无业务耦合，仅做异常管理
"""

from typing import Optional, Any


# 全局错误码定义
ERROR_CODES = {
    # 通用错误
    "UNKNOWN_ERROR": "E0001",
    "VALIDATION_ERROR": "E0002",
    # 文件处理错误
    "FILE_PROCESSING_ERROR": "E1001",
    # 大模型调用错误
    "LLM_CALL_ERROR": "E2001",
    # 规则匹配错误
    "RULE_MATCH_ERROR": "E3001",
    # 审计日志错误
    "AUDIT_ERROR": "E4001",
}


class BaseESGException(Exception):
    """项目基础异常类"""
    def __init__(
        self,
        message: str,
        error_code: str = ERROR_CODES["UNKNOWN_ERROR"],
        original_exception: Optional[Exception] = None,
        context: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.original_exception = original_exception
        self.context = context or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典，用于API返回、审计日志"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "original_exception": str(self.original_exception) if self.original_exception else None,
        }


class ValidationException(BaseESGException):
    """数据校验异常"""
    def __init__(self, message: str, original_exception: Optional[Exception] = None, context: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ERROR_CODES["VALIDATION_ERROR"],
            original_exception=original_exception,
            context=context,
        )


class FileProcessingException(BaseESGException):
    """文件处理异常"""
    def __init__(self, message: str, original_exception: Optional[Exception] = None, context: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ERROR_CODES["FILE_PROCESSING_ERROR"],
            original_exception=original_exception,
            context=context,
        )


class LLMCallException(BaseESGException):
    """大模型调用异常"""
    def __init__(self, message: str, original_exception: Optional[Exception] = None, context: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ERROR_CODES["LLM_CALL_ERROR"],
            original_exception=original_exception,
            context=context,
        )


class RuleMatchException(BaseESGException):
    """规则匹配异常"""
    def __init__(self, message: str, original_exception: Optional[Exception] = None, context: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ERROR_CODES["RULE_MATCH_ERROR"],
            original_exception=original_exception,
            context=context,
        )


class AuditException(BaseESGException):
    """审计日志异常"""
    def __init__(self, message: str, original_exception: Optional[Exception] = None, context: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ERROR_CODES["AUDIT_ERROR"],
            original_exception=original_exception,
            context=context,
        )
