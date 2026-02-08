"""文件操作工具模块

提供常用的文件和目录操作功能，包括保存上传的文件、确保目录存在、
获取文件扩展名等功能。
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Union


def save_uploaded_file(uploaded_file, save_dir: Union[str, Path] = "temp") -> str:
    """保存上传的文件到指定目录

    将上传的文件对象保存到本地文件系统。支持具有 `name` 属性和
    `getbuffer()` 方法的上传文件对象（如 Streamlit 的 UploadedFile）。

    Args:
        uploaded_file: 上传的文件对象，需要具有 name 属性和 getbuffer() 方法
        save_dir: 保存文件的目录路径，默认为 "temp"

    Returns:
        保存后的文件完整路径

    Raises:
        AttributeError: 当 uploaded_file 对象缺少必要的方法或属性时抛出
        IOError: 当文件写入失败时抛出

    Example:
        >>> # 假设 uploaded_file 是 Streamlit 的上传文件对象
        >>> file_path = save_uploaded_file(uploaded_file, save_dir="uploads")
        >>> print(f"文件已保存到: {file_path}")
    """
    # 确保目录存在
    ensure_dir(save_dir)

    # 构建文件路径
    file_path = Path(save_dir) / uploaded_file.name

    # 写入文件内容
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return str(file_path)


def ensure_dir(path: Union[str, Path]) -> Path:
    """确保目录存在，如果不存在则创建

    递归创建目录（包括所有必需的父目录），如果目录已存在则不执行任何操作。

    Args:
        path: 目录路径

    Returns:
        创建后的目录 Path 对象

    Raises:
        PermissionError: 当没有权限创建目录时抛出
        OSError: 当目录创建失败时抛出

    Example:
        >>> ensure_dir("data/raw/2024")
        >>> # 现在 data/raw/2024 目录一定存在
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def get_file_extension(filename: Union[str, Path]) -> str:
    """获取文件扩展名（小写）

    从文件名中提取扩展名部分，并转换为小写。

    Args:
        filename: 文件名或路径

    Returns:
        文件扩展名（包含点，如 ".pdf"），如果没有扩展名则返回空字符串

    Example:
        >>> get_file_extension("document.PDF")
        '.pdf'
        >>> get_file_extension("/path/to/file.txt")
        '.txt'
        >>> get_file_extension("README")
        ''
    """
    return Path(filename).suffix.lower()


def copy_file(src: Union[str, Path], dst: Union[str, Path], overwrite: bool = False) -> str:
    """复制文件

    将源文件复制到目标位置。

    Args:
        src: 源文件路径
        dst: 目标文件路径或目录
        overwrite: 是否覆盖已存在的文件，默认为 False

    Returns:
        目标文件的完整路径

    Raises:
        FileExistsError: 当目标文件已存在且 overwrite=False 时抛出
        FileNotFoundError: 当源文件不存在时抛出

    Example:
        >>> copy_file("data/file.txt", "backup/file.txt", overwrite=True)
        'backup/file.txt'
    """
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        raise FileNotFoundError(f"源文件不存在: {src}")

    # 如果目标是目录，使用源文件名
    if dst_path.is_dir():
        dst_path = dst_path / src_path.name

    # 检查目标文件是否已存在
    if dst_path.exists() and not overwrite:
        raise FileExistsError(f"目标文件已存在: {dst_path}")

    # 确保目标目录存在
    ensure_dir(dst_path.parent)

    # 复制文件
    shutil.copy2(src_path, dst_path)

    return str(dst_path)


def delete_file(path: Union[str, Path], missing_ok: bool = True) -> bool:
    """删除文件

    删除指定路径的文件。可以选择在文件不存在时是否抛出异常。

    Args:
        path: 要删除的文件路径
        missing_ok: 如果为 True，文件不存在时不抛出异常，默认为 True

    Returns:
        如果文件被删除返回 True，如果文件不存在返回 False

    Raises:
        PermissionError: 当没有权限删除文件时抛出
        IsADirectoryError: 当路径是目录时抛出

    Example:
        >>> delete_file("temp/old_file.txt")
        True
    """
    path_obj = Path(path)

    try:
        path_obj.unlink()
        return True
    except FileNotFoundError:
        if not missing_ok:
            raise
        return False


def get_file_size(path: Union[str, Path]) -> int:
    """获取文件大小（字节）

    Args:
        path: 文件路径

    Returns:
        文件大小（字节）

    Raises:
        FileNotFoundError: 当文件不存在时抛出

    Example:
        >>> size = get_file_size("document.pdf")
        >>> print(f"文件大小: {size / 1024:.2f} KB")
    """
    return Path(path).stat().st_size
