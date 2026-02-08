"""加密模块

提供敏感数据加密、密码哈希、密钥管理等功能。
"""

import base64
import hashlib
import logging
import os
import secrets
from dataclasses import dataclass
from typing import Optional, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class EncryptedData:
    """加密数据结构"""

    ciphertext: str
    salt: str
    iterations: int

    def to_dict(self) -> dict:
        return {"ciphertext": self.ciphertext, "salt": self.salt, "iterations": self.iterations}

    @classmethod
    def from_dict(cls, data: dict) -> "EncryptedData":
        return cls(ciphertext=data["ciphertext"], salt=data["salt"], iterations=data["iterations"])


class EncryptionManager:
    """加密管理器

    提供敏感数据加密、解密和密钥管理功能。

    Example:
        >>> # 使用主密钥初始化
        >>> manager = EncryptionManager(master_key="my-secret-key")
        >>>
        >>> # 加密敏感数据
        >>> encrypted = manager.encrypt("sensitive data")
        >>>
        >>> # 解密
        >>> decrypted = manager.decrypt(encrypted)
    """

    # 默认PBKDF2迭代次数（安全性 vs 性能）
    DEFAULT_ITERATIONS = 100000

    def __init__(self, master_key: Optional[str] = None):
        """初始化加密管理器

        Args:
            master_key: 主密钥，None则从环境变量获取
        """
        if master_key is None:
            master_key = os.getenv("ESG_ENCRYPTION_KEY")
            if not master_key:
                logger.warning("未设置主密钥，使用默认密钥（不安全！）")
                master_key = "default_insecure_key_change_immediately"

        self.master_key = master_key.encode()
        self._fernet: Optional[Fernet] = None

    def _get_fernet(self, salt: bytes, iterations: int) -> Fernet:
        """获取或创建Fernet实例

        Args:
            salt: 盐值
            iterations: PBKDF2迭代次数

        Returns:
            Fernet实例
        """
        # 使用PBKDF2派生密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        return Fernet(key)

    def encrypt(
        self, plaintext: str, salt: Optional[bytes] = None, iterations: Optional[int] = None
    ) -> EncryptedData:
        """加密数据

        Args:
            plaintext: 明文数据
            salt: 可选的盐值，None则随机生成
            iterations: PBKDF2迭代次数，None使用默认值

        Returns:
            加密后的数据结构
        """
        if salt is None:
            salt = os.urandom(16)

        if iterations is None:
            iterations = self.DEFAULT_ITERATIONS

        try:
            fernet = self._get_fernet(salt, iterations)
            ciphertext = fernet.encrypt(plaintext.encode())

            encrypted_data = EncryptedData(
                ciphertext=base64.urlsafe_b64encode(ciphertext).decode(),
                salt=base64.urlsafe_b64encode(salt).decode(),
                iterations=iterations,
            )

            logger.debug("数据加密成功")
            return encrypted_data

        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise

    def decrypt(self, encrypted_data: EncryptedData) -> str:
        """解密数据

        Args:
            encrypted_data: 加密数据结构

        Returns:
            解密后的明文
        """
        try:
            salt = base64.urlsafe_b64decode(encrypted_data.salt)
            ciphertext = base64.urlsafe_b64decode(encrypted_data.ciphertext)

            fernet = self._get_fernet(salt, encrypted_data.iterations)
            plaintext = fernet.decrypt(ciphertext)

            logger.debug("数据解密成功")
            return plaintext.decode()

        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise

    def encrypt_dict(self, data: dict, sensitive_fields: list) -> dict:
        """加密字典中的敏感字段

        Args:
            data: 原始数据字典
            sensitive_fields: 需要加密的字段列表

        Returns:
            加密后的字典
        """
        result = data.copy()

        for field in sensitive_fields:
            if field in result and result[field] is not None:
                encrypted = self.encrypt(str(result[field]))
                result[field] = encrypted.to_dict()

        return result

    def decrypt_dict(self, data: dict, encrypted_fields: list) -> dict:
        """解密字典中的加密字段

        Args:
            data: 加密后的数据字典
            encrypted_fields: 已加密的字段列表

        Returns:
            解密后的字典
        """
        result = data.copy()

        for field in encrypted_fields:
            if field in result and isinstance(result[field], dict):
                encrypted = EncryptedData.from_dict(result[field])
                result[field] = self.decrypt(encrypted)

        return result


class PasswordHasher:
    """密码哈希器

    使用PBKDF2+SHA256进行密码哈希。

    Example:
        >>> hasher = PasswordHasher()
        >>>
        >>> # 哈希密码
        >>> hashed = hasher.hash("password123")
        >>>
        >>> # 验证密码
        >>> if hasher.verify("password123", hashed):
        ...     print("密码正确")
    """

    def __init__(self, iterations: int = 100000):
        """初始化密码哈希器

        Args:
            iterations: PBKDF2迭代次数
        """
        self.iterations = iterations

    def hash(self, password: str) -> str:
        """哈希密码

        Args:
            password: 明文密码

        Returns:
            格式为"salt:hash"的字符串
        """
        salt = os.urandom(32)
        pwdhash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, self.iterations)

        return base64.b64encode(salt + pwdhash).decode()

    def verify(self, password: str, hashed: str) -> bool:
        """验证密码

        Args:
            password: 明文密码
            hashed: 哈希值

        Returns:
            是否匹配
        """
        try:
            decoded = base64.b64decode(hashed)
            salt = decoded[:32]
            stored_hash = decoded[32:]

            pwdhash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, self.iterations)

            return pwdhash == stored_hash

        except Exception as e:
            logger.error(f"密码验证失败: {e}")
            return False


def generate_secure_key(length: int = 32) -> str:
    """生成安全的随机密钥

    Args:
        length: 密钥长度（字节）

    Returns:
        Base64编码的密钥
    """
    return base64.urlsafe_b64encode(secrets.token_bytes(length)).decode()


def hash_password(password: str) -> str:
    """便捷函数：哈希密码"""
    hasher = PasswordHasher()
    return hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """便捷函数：验证密码"""
    hasher = PasswordHasher()
    return hasher.verify(password, hashed)


# 全局加密管理器实例
_global_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """获取全局加密管理器"""
    global _global_encryption_manager
    if _global_encryption_manager is None:
        _global_encryption_manager = EncryptionManager()
    return _global_encryption_manager


def encrypt_sensitive_data(plaintext: str, master_key: Optional[str] = None) -> EncryptedData:
    """便捷函数：加密敏感数据"""
    if master_key:
        manager = EncryptionManager(master_key)
    else:
        manager = get_encryption_manager()

    return manager.encrypt(plaintext)


def decrypt_sensitive_data(encrypted_data: EncryptedData, master_key: Optional[str] = None) -> str:
    """便捷函数：解密敏感数据"""
    if master_key:
        manager = EncryptionManager(master_key)
    else:
        manager = get_encryption_manager()

    return manager.decrypt(encrypted_data)
