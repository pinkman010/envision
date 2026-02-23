"""
哈希校验工具：SHA-256算法，防止审计日志篡改
ESG合规细节工具：审计日志不可篡改
"""

import hashlib
from typing import Union


def generate_sha256_hash(content: Union[str, bytes]) -> str:
    """
    生成SHA-256哈希值
    :param content: 字符串或字节内容
    :return: 64位十六进制哈希值
    """
    if isinstance(content, str):
        content = content.encode("utf-8")
    sha256 = hashlib.sha256()
    sha256.update(content)
    return sha256.hexdigest()


def verify_sha256_hash(content: Union[str, bytes], expected_hash: str) -> bool:
    """
    校验SHA-256哈希值
    :param content: 原始内容
    :param expected_hash: 预期哈希值
    :return: 是否匹配
    """
    actual_hash = generate_sha256_hash(content)
    return actual_hash == expected_hash.lower()
