"""文件工具"""

import os
from pathlib import Path


def save_uploaded_file(uploaded_file, save_dir: str = "temp") -> str:
    """保存上传的文件"""
    os.makedirs(save_dir, exist_ok=True)
    
    file_path = Path(save_dir) / uploaded_file.name
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return str(file_path)


def ensure_dir(path: str):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)
