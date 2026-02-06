"""文件处理工具"""

import os
import hashlib
from typing import Optional

from config import DATA_PATH


def save_uploaded_file(uploaded_file, subfolder: str = "uploads") -> str:
    """保存上传的文件"""
    folder_path = os.path.join(DATA_PATH, subfolder)
    os.makedirs(folder_path, exist_ok=True)
    
    file_path = os.path.join(folder_path, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path


def get_file_hash(file_path: str) -> str:
    """计算文件SHA256哈希"""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()[:32]


def ensure_dir(path: str) -> str:
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)
    return path