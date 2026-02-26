"""
统一异常定义模块
所有业务异常均继承自 BaseESGException，确保异常处理的一致性
"""

from typing import Optional, Dict, Any


class BaseESGException(Exception):
    """所有ESG业务异常的基类"""
    
    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        self.message = message
        self.context = context or {}
        self.original_exception = original_exception
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.context:
            return f"{self.message} (context: {self.context})"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """将异常转换为字典格式，用于API响应"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
        }


class ValidationException(BaseESGException):
    """数据校验异常（格式错误、缺少必填字段等）"""
    pass


class FileProcessingException(BaseESGException):
    """文件处理异常（解析失败、格式不支持等）"""
    pass


class LLMCallException(BaseESGException):
    """大模型调用异常（网络错误、API错误等）"""
    pass


class RuleMatchException(BaseESGException):
    """规则匹配异常"""
    pass


class AuditException(BaseESGException):
    """审计日志异常"""
    pass
