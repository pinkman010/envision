"""异步PDF提取器模块

支持异步批量处理PDF文件，提高性能。
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Union

from src.esg.extraction.pdf_extractor import PDFExtractor, PDFContent, PDFExtractionError
from src.esg.utils.performance_monitor import get_monitor, PDF_EXTRACTION_DURATION

# 配置日志
logger = logging.getLogger(__name__)


class AsyncPDFExtractor:
    """异步PDF提取器
    
    支持并发批量处理PDF文件，提高提取性能。
    
    Example:
        >>> extractor = AsyncPDFExtractor(max_workers=4)
        >>> 
        >>> # 异步提取单个文件
        >>> content = await extractor.extract_async("report.pdf")
        >>> 
        >>> # 批量提取
        >>> results = await extractor.extract_batch_async([
        ...     "report1.pdf",
        ...     "report2.pdf",
        ...     "report3.pdf"
        ... ])
        >>> 
        >>> # 使用进度回调
        >>> def on_progress(current, total):
        ...     print(f"Progress: {current}/{total}")
        >>> 
        >>> results = await extractor.extract_batch_async(
        ...     files,
        ...     progress_callback=on_progress
        ... )
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        preferred_backend: Optional[str] = None
    ):
        """初始化异步PDF提取器
        
        Args:
            max_workers: 最大并发工作线程数
            preferred_backend: 首选PDF提取后端
        """
        self.max_workers = max_workers
        self.preferred_backend = preferred_backend
        self._sync_extractor = PDFExtractor(preferred_backend)
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._monitor = get_monitor()
    
    async def extract_async(self, pdf_path: Union[str, Path]) -> PDFContent:
        """异步提取单个PDF文件
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            PDFContent: 提取的内容
            
        Raises:
            PDFExtractionError: 提取失败
        """
        loop = asyncio.get_event_loop()
        
        def _extract():
            with self._monitor.track("pdf_extraction_async"):
                return self._sync_extractor.extract(pdf_path)
        
        try:
            # 在线程池中执行同步提取
            content = await loop.run_in_executor(self._executor, _extract)
            
            # 记录指标
            PDF_EXTRACTION_DURATION.labels(
                backend=self.preferred_backend or 'auto'
            ).observe(content.metadata.total_pages * 0.1)  # 估算时间
            
            return content
            
        except Exception as e:
            logger.error(f"异步PDF提取失败 [{pdf_path}]: {e}")
            raise PDFExtractionError(f"异步提取失败: {e}") from e
    
    async def extract_batch_async(
        self,
        pdf_paths: List[Union[str, Path]],
        progress_callback: Optional[callable] = None,
        continue_on_error: bool = True
    ) -> Dict[str, Union[PDFContent, Exception]]:
        """异步批量提取PDF文件
        
        Args:
            pdf_paths: PDF文件路径列表
            progress_callback: 进度回调函数，接收(current, total)参数
            continue_on_error: 遇到错误时是否继续处理其他文件
            
        Returns:
            文件名到内容或异常的映射
        """
        results: Dict[str, Union[PDFContent, Exception]] = {}
        total = len(pdf_paths)
        completed = 0
        
        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def _extract_with_semaphore(path: Union[str, Path]) -> tuple:
            nonlocal completed
            
            async with semaphore:
                filename = Path(path).name
                try:
                    content = await self.extract_async(path)
                    return filename, content
                except Exception as e:
                    if not continue_on_error:
                        raise
                    logger.error(f"提取失败 [{filename}]: {e}")
                    return filename, e
                finally:
                    completed += 1
                    if progress_callback:
                        try:
                            progress_callback(completed, total)
                        except Exception as e:
                            logger.warning(f"进度回调错误: {e}")
        
        # 并发执行所有任务
        tasks = [_extract_with_semaphore(path) for path in pdf_paths]
        
        try:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in task_results:
                if isinstance(result, Exception):
                    logger.error(f"批量提取中的错误: {result}")
                else:
                    filename, content = result
                    results[filename] = content
                    
        except Exception as e:
            logger.error(f"批量提取失败: {e}")
            raise
        
        return results
    
    async def extract_directory_async(
        self,
        directory: Union[str, Path],
        pattern: str = "*.pdf",
        recursive: bool = False,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Union[PDFContent, Exception]]:
        """异步提取目录中的所有PDF文件
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归子目录
            progress_callback: 进度回调函数
            
        Returns:
            文件名到内容或异常的映射
        """
        directory = Path(directory)
        
        if recursive:
            pdf_files = list(directory.rglob(pattern))
        else:
            pdf_files = list(directory.glob(pattern))
        
        if not pdf_files:
            logger.warning(f"在 {directory} 中没有找到PDF文件")
            return {}
        
        logger.info(f"在 {directory} 中找到 {len(pdf_files)} 个PDF文件")
        
        return await self.extract_batch_async(
            pdf_files,
            progress_callback=progress_callback
        )
    
    def close(self):
        """关闭提取器，释放资源"""
        self._executor.shutdown(wait=True)
        logger.info("异步PDF提取器已关闭")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        self.close()
        return False


class PDFExtractionPipeline:
    """PDF提取管道
    
    提供高级的PDF处理管道，支持预处理、提取、后处理等阶段。
    
    Example:
        >>> pipeline = PDFExtractionPipeline()
        >>> 
        >>> # 添加预处理步骤
        >>> pipeline.add_preprocessor(lambda path: validate_pdf(path))
        >>> 
        >>> # 添加后处理步骤
        >>> pipeline.add_postprocessor(lambda content: clean_text(content))
        >>> 
        >>> # 执行管道
        >>> result = await pipeline.process("report.pdf")
    """
    
    def __init__(self, max_workers: int = 4):
        """初始化PDF提取管道
        
        Args:
            max_workers: 最大并发工作线程数
        """
        self.extractor = AsyncPDFExtractor(max_workers)
        self.preprocessors: List[callable] = []
        self.postprocessors: List[callable] = []
    
    def add_preprocessor(self, processor: callable):
        """添加预处理器
        
        Args:
            processor: 预处理函数，接收文件路径，返回处理后的路径
        """
        self.preprocessors.append(processor)
    
    def add_postprocessor(self, processor: callable):
        """添加后处理器
        
        Args:
            processor: 后处理函数，接收PDFContent，返回处理后的内容
        """
        self.postprocessors.append(processor)
    
    async def process(self, pdf_path: Union[str, Path]) -> PDFContent:
        """处理单个PDF文件
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            处理后的PDFContent
        """
        # 预处理
        processed_path = pdf_path
        for preprocessor in self.preprocessors:
            processed_path = await self._run_sync_or_async(
                preprocessor, processed_path
            )
        
        # 提取
        content = await self.extractor.extract_async(processed_path)
        
        # 后处理
        for postprocessor in self.postprocessors:
            content = await self._run_sync_or_async(postprocessor, content)
        
        return content
    
    async def process_batch(
        self,
        pdf_paths: List[Union[str, Path]],
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Union[PDFContent, Exception]]:
        """批量处理PDF文件
        
        Args:
            pdf_paths: PDF文件路径列表
            progress_callback: 进度回调函数
            
        Returns:
            处理结果
        """
        results: Dict[str, Union[PDFContent, Exception]] = {}
        total = len(pdf_paths)
        
        for i, path in enumerate(pdf_paths):
            try:
                filename = Path(path).name
                content = await self.process(path)
                results[filename] = content
            except Exception as e:
                logger.error(f"管道处理失败 [{path}]: {e}")
                results[filename] = e
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return results
    
    async def _run_sync_or_async(
        self,
        func: callable,
        *args,
        **kwargs
    ) -> Any:
        """运行同步或异步函数"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    def close(self):
        """关闭管道"""
        self.extractor.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
