"""
语料处理Agent
核心职责：PDF/Word解析、文本分块、元数据标注
AI仅做乱码/表格识别异常修复，无任何业务判断
"""

from pathlib import Path
from typing import Dict, Any

from src.agent.base_agent import BaseAgent
from src.core_config import get_logger, settings
from src.utils import (
    validate_file,
    extract_text,
    split_text_into_chunks,
    FileProcessingException,
    call_llm,
    load_prompt_template,
    save_corpus_to_db,
)


class CorpusAgent(BaseAgent):
    """语料处理Agent"""

    def __init__(self):
        super().__init__(
            agent_name="corpus_agent",
            agent_role="PDF/Word解析、文本分块、元数据标注工具（AI仅修复异常）",
        )
        # 加载AI修复异常的固定Prompt（仅1条，无需调试）
        try:
            self.fix_prompt = load_prompt_template("corpus_fix_prompt")
        except Exception as e:
            self.logger.warning(f"加载语料修复Prompt失败，将跳过AI修复: {str(e)}")
            self.fix_prompt = None

    def _fix_text_with_ai(self, raw_text: str, file_name: str) -> str:
        """
        用AI修复乱码/表格识别异常（仅1条固定Prompt）
        :param raw_text: 原始解析文本
        :param file_name: 文件名
        :return: 修复后的文本
        """
        if not self.fix_prompt or not settings.LLM_API_KEY:
            self.logger.debug("跳过AI修复（无Prompt或无API密钥）")
            return raw_text
        
        try:
            self.logger.debug(f"开始用AI修复文本异常: {file_name}")
            prompt = self.fix_prompt.render(raw_text=raw_text[:5000])  # 仅取前5000字符修复
            messages = [{"role": "user", "content": prompt}]
            fixed_text = call_llm(messages)
            self.logger.debug(f"AI文本修复完成: {file_name}")
            return fixed_text
        except Exception as e:
            self.logger.warning(f"AI文本修复失败，将使用原始文本: {str(e)}")
            return raw_text

    def _execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行语料处理任务
        :param task_input: 必须包含 file_path 字段（文件绝对路径或Path对象）
        :return: 语料处理结果（文本、分块、元数据）
        """
        # 1. 解析任务输入
        file_path_str = task_input.get("file_path")
        if not file_path_str:
            raise FileProcessingException("任务输入缺少必填字段: file_path")
        file_path = Path(file_path_str)

        # 2. 校验文件合法性
        self.logger.debug(f"开始校验文件: {file_path.name}")
        validate_file(file_path)

        # 3. 提取纯文本
        self.logger.debug(f"开始提取文本: {file_path.name}")
        raw_text = extract_text(file_path)
        if not raw_text:
            raise FileProcessingException(f"文件文本提取失败（空文本）: {file_path.name}")

        # 4. 用AI修复乱码/表格异常（可选）
        fixed_text = self._fix_text_with_ai(raw_text, file_path.name)

        # 5. 按固定规则分块
        self.logger.debug(f"开始文本分块: {file_path.name}")
        chunks = split_text_into_chunks(
            fixed_text,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

        # 6. 生成元数据
        metadata = {
            "file_name": file_path.name,
            "file_suffix": file_path.suffix.lower(),
            "file_size": file_path.stat().st_size,
            "text_length": len(fixed_text),
            "chunk_count": len(chunks),
            "processed_at": self.start_time.isoformat() if self.start_time else None,
        }

        # 7. 保存到 Chroma 数据库
        self.logger.debug(f"开始保存语料到数据库: {file_path.name}")
        try:
            corpus_id = save_corpus_to_db(
                file_name=file_path.name,
                file_suffix=file_path.suffix.lower(),
                file_size=file_path.stat().st_size,
                raw_text=raw_text,
                fixed_text=fixed_text,
                chunks=chunks,
                esg_metrics=None,  # 暂不自动提取，后续可扩展
            )
            metadata["corpus_id"] = corpus_id
            self.logger.info(f"语料保存成功，ID: {corpus_id}")
        except Exception as e:
            self.logger.error(f"语料保存到数据库失败: {str(e)}")
            # 保存失败不影响返回结果，但会记录错误
            metadata["corpus_id"] = None
            metadata["save_error"] = str(e)

        # 8. 返回结果
        self.logger.debug(f"语料处理完成: {file_path.name}, 分块数: {len(chunks)}")
        return {
            "file_path": str(file_path),
            "metadata": metadata,
            "raw_text": raw_text,
            "fixed_text": fixed_text,
            "chunks": chunks,  # 每个块为（起始位置, 结束位置, 文本内容）
            "corpus_id": metadata.get("corpus_id"),
        }
