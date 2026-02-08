"""安全模块

提供认证、授权、加密、CSRF防护等安全功能。
"""

from src.esg.security.auth import (
    AuthManager,
    Permission,
    Role,
    User,
    authenticate_user,
    create_access_token,
    require_auth,
    require_permission,
    verify_token,
)
from src.esg.security.csrf import CSRFProtection, generate_csrf_token, validate_csrf_token
from src.esg.security.encryption import (
    EncryptionManager,
    decrypt_sensitive_data,
    encrypt_sensitive_data,
    generate_secure_key,
    hash_password,
    verify_password,
)

__all__ = [
    # 认证
    "AuthManager",
    "User",
    "Permission",
    "Role",
    "authenticate_user",
    "create_access_token",
    "verify_token",
    "require_auth",
    "require_permission",
    # 加密
    "EncryptionManager",
    "encrypt_sensitive_data",
    "decrypt_sensitive_data",
    "hash_password",
    "verify_password",
    "generate_secure_key",
    # CSRF
    "CSRFProtection",
    "generate_csrf_token",
    "validate_csrf_token",
]
