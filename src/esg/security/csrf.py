"""CSRF防护模块

提供CSRF令牌生成、验证和防护功能。
"""

import hashlib
import hmac
import logging
import secrets
import time
from typing import Optional

# 配置日志
logger = logging.getLogger(__name__)


class CSRFProtection:
    """CSRF防护管理器
    
    提供CSRF令牌生成和验证功能。
    
    Example:
        >>> csrf = CSRFProtection(secret_key="my-secret")
        >>> 
        >>> # 生成令牌
        >>> token = csrf.generate_token("user_session_123")
        >>> 
        >>> # 验证令牌
        >>> if csrf.validate_token(token, "user_session_123"):
        ...     print("CSRF验证通过")
    """
    
    # 令牌有效期（秒）
    TOKEN_EXPIRY = 3600  # 1小时
    
    def __init__(self, secret_key: Optional[str] = None):
        """初始化CSRF防护
        
        Args:
            secret_key: 密钥，None则自动生成
        """
        if secret_key is None:
            secret_key = secrets.token_urlsafe(32)
            logger.debug("自动生成CSRF密钥")
        
        self.secret_key = secret_key.encode()
    
    def generate_token(
        self,
        session_id: str,
        timestamp: Optional[int] = None
    ) -> str:
        """生成CSRF令牌
        
        Args:
            session_id: 会话ID
            timestamp: 时间戳，None则使用当前时间
            
        Returns:
            CSRF令牌
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        # 创建消息
        message = f"{session_id}:{timestamp}"
        
        # 创建HMAC签名
        signature = hmac.new(
            self.secret_key,
            message.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
        
        # 组合令牌
        token = f"{timestamp}:{signature}"
        
        logger.debug(f"生成CSRF令牌 [session={session_id}]")
        return token
    
    def validate_token(
        self,
        token: str,
        session_id: str,
        max_age: Optional[int] = None
    ) -> bool:
        """验证CSRF令牌
        
        Args:
            token: CSRF令牌
            session_id: 会话ID
            max_age: 最大有效期（秒），None使用默认值
            
        Returns:
            是否有效
        """
        if max_age is None:
            max_age = self.TOKEN_EXPIRY
        
        try:
            # 解析令牌
            parts = token.split(':')
            if len(parts) != 2:
                logger.warning("CSRF令牌格式无效")
                return False
            
            timestamp_str, signature = parts
            timestamp = int(timestamp_str)
            
            # 检查是否过期
            current_time = int(time.time())
            if current_time - timestamp > max_age:
                logger.warning("CSRF令牌已过期")
                return False
            
            # 验证签名
            expected_token = self.generate_token(session_id, timestamp)
            expected_parts = expected_token.split(':')
            
            if len(expected_parts) != 2:
                return False
            
            # 使用常量时间比较防止时序攻击
            is_valid = hmac.compare_digest(token, expected_token)
            
            if is_valid:
                logger.debug(f"CSRF验证成功 [session={session_id}]")
            else:
                logger.warning(f"CSRF验证失败 [session={session_id}]")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"CSRF验证错误: {e}")
            return False
    
    def refresh_token(self, token: str, session_id: str) -> Optional[str]:
        """刷新CSRF令牌
        
        Args:
            token: 当前令牌
            session_id: 会话ID
            
        Returns:
            新令牌或None（如果当前令牌无效）
        """
        if self.validate_token(token, session_id):
            return self.generate_token(session_id)
        return None


class DoubleSubmitCookie:
    """双重提交Cookie模式
    
    实现CSRF防护的双重提交Cookie模式。
    
    Example:
        >>> csrf = DoubleSubmitCookie(secret_key="my-secret")
        >>> 
        >>> # 设置Cookie并获取令牌
        >>> cookie_value = csrf.set_cookie()
        >>> 
        >>> # 验证请求
        >>> if csrf.validate_request(cookie_value, request_token):
        ...     print("CSRF验证通过")
    """
    
    COOKIE_NAME = "csrf_token"
    
    def __init__(self, secret_key: Optional[str] = None):
        """初始化双重提交Cookie防护
        
        Args:
            secret_key: 密钥
        """
        self.protection = CSRFProtection(secret_key)
    
    def set_cookie(self) -> str:
        """设置CSRF Cookie
        
        Returns:
            Cookie值
        """
        # 生成随机Cookie值
        cookie_value = secrets.token_urlsafe(32)
        
        # 生成关联的CSRF令牌
        csrf_token = self.protection.generate_token(cookie_value)
        
        logger.debug("设置CSRF Cookie")
        return f"{cookie_value}:{csrf_token}"
    
    def validate_request(self, cookie_value: str, request_token: str) -> bool:
        """验证请求
        
        Args:
            cookie_value: Cookie中的值
            request_token: 请求中的令牌
            
        Returns:
            是否有效
        """
        # 解析Cookie值
        parts = cookie_value.split(':')
        if len(parts) != 2:
            logger.warning("Cookie格式无效")
            return False
        
        token_id, csrf_token = parts
        
        # 验证令牌是否与Cookie匹配
        is_valid = self.protection.validate_token(csrf_token, token_id)
        
        # 额外验证请求中的令牌
        if is_valid and request_token != csrf_token:
            logger.warning("请求令牌与Cookie不匹配")
            return False
        
        return is_valid
    
    def get_html_meta_tag(self, cookie_value: str) -> str:
        """获取HTML meta标签
        
        用于前端获取CSRF令牌。
        
        Args:
            cookie_value: Cookie值
            
        Returns:
            HTML meta标签
        """
        parts = cookie_value.split(':')
        if len(parts) != 2:
            return ""
        
        csrf_token = parts[1]
        return f'<meta name="csrf-token" content="{csrf_token}">'
    
    def get_js_config(self, cookie_value: str) -> dict:
        """获取JavaScript配置
        
        Args:
            cookie_value: Cookie值
            
        Returns:
            JavaScript配置字典
        """
        parts = cookie_value.split(':')
        if len(parts) != 2:
            return {}
        
        return {
            'cookie_name': self.COOKIE_NAME,
            'header_name': 'X-CSRF-Token',
            'token': parts[1]
        }


# 便捷函数

def generate_csrf_token(
    session_id: str,
    secret_key: Optional[str] = None
) -> str:
    """生成CSRF令牌"""
    protection = CSRFProtection(secret_key)
    return protection.generate_token(session_id)


def validate_csrf_token(
    token: str,
    session_id: str,
    secret_key: Optional[str] = None,
    max_age: Optional[int] = None
) -> bool:
    """验证CSRF令牌"""
    protection = CSRFProtection(secret_key)
    return protection.validate_token(token, session_id, max_age)
