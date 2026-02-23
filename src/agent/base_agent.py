"""
所有Agent的统一基类
定义Agent的核心三要素：明确角色与目标、可自主执行的动作集合、闭环状态管理
无业务逻辑，仅做框架定义
"""

import abc
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime

from src.core_config import get_logger
from src.utils import write_audit_log, BaseESGException


# 统一Agent状态枚举
class AgentState(Enum):
    IDLE = "idle"          # 空闲，等待任务
    RUNNING = "running"    # 正在执行任务
    SUCCESS = "success"    # 任务执行成功
    FAILED = "failed"      # 任务执行失败
    PENDING = "pending"    # 等待人工介入（复核/修复）


class BaseAgent(abc.ABC):
    """所有Agent的抽象基类"""

    def __init__(self, agent_name: str, agent_role: str):
        """
        初始化Agent
        :param agent_name: Agent唯一名称（如corpus_agent）
        :param agent_role: Agent明确角色描述（如语料解析与分块工具）
        """
        self.agent_name = agent_name
        self.agent_role = agent_role
        self.state = AgentState.IDLE
        self.current_task_id: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.error_info: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        
        # 初始化logger
        self.logger = get_logger(f"agent.{agent_name}")
        self.logger.info(f"Agent初始化完成: {agent_name} ({agent_role})")

    def reset(self) -> None:
        """重置Agent状态（每次执行新任务前调用）"""
        self.state = AgentState.IDLE
        self.current_task_id = None
        self.start_time = None
        self.end_time = None
        self.error_info = None
        self.result = None
        self.logger.debug("Agent状态已重置")

    @abc.abstractmethod
    def _execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        抽象方法：执行具体任务逻辑（子类必须实现）
        :param task_input: 任务输入参数
        :return: 任务执行结果
        :raises BaseESGException: 执行失败时抛出统一异常
        """
        pass

    def run(self, task_input: Dict[str, Any], task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        统一任务执行入口（闭环管理、状态跟踪、审计日志）
        :param task_input: 任务输入参数
        :param task_id: 任务唯一ID（可选，自动生成）
        :return: 任务执行结果
        :raises BaseESGException: 执行失败时抛出统一异常
        """
        # 1. 初始化任务
        self.reset()
        self.current_task_id = task_id or f"{self.agent_name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        self.start_time = datetime.utcnow()
        self.state = AgentState.RUNNING
        self.logger.info(f"开始执行任务: {self.current_task_id}, 输入: {task_input}")

        # 2. 写入审计日志（任务开始）
        write_audit_log(
            operation_type=f"{self.agent_name.upper()}_START",
            operator=self.agent_name,
            operation_detail={"task_id": self.current_task_id, "task_input": task_input},
            status="running",
        )

        try:
            # 3. 执行具体任务逻辑（子类实现）
            self.result = self._execute(task_input)
            
            # 4. 任务成功闭环
            self.state = AgentState.SUCCESS
            self.end_time = datetime.utcnow()
            self.logger.info(
                f"任务执行成功: {self.current_task_id}, "
                f"耗时: {(self.end_time - self.start_time).total_seconds():.2f}s"
            )
            
            # 5. 写入审计日志（任务成功）
            write_audit_log(
                operation_type=f"{self.agent_name.upper()}_SUCCESS",
                operator=self.agent_name,
                operation_detail={"task_id": self.current_task_id, "result": self.result},
                status="success",
            )
            
            return self.result

        except BaseESGException as e:
            # 6. 任务失败闭环（业务异常）
            self.state = AgentState.FAILED
            self.error_info = e.message
            self.end_time = datetime.utcnow()
            self.logger.error(
                f"任务执行失败: {self.current_task_id}, 错误: {self.error_info}",
                exc_info=True,
            )
            
            # 7. 写入审计日志（任务失败）
            write_audit_log(
                operation_type=f"{self.agent_name.upper()}_FAILED",
                operator=self.agent_name,
                operation_detail={"task_id": self.current_task_id, "task_input": task_input},
                status="failed",
                error_info=self.error_info,
            )
            
            raise

        except Exception as e:
            # 8. 任务失败闭环（未知异常）
            self.state = AgentState.FAILED
            self.error_info = f"未知错误: {str(e)}"
            self.end_time = datetime.utcnow()
            self.logger.critical(
                f"任务执行未知错误: {self.current_task_id}, 错误: {self.error_info}",
                exc_info=True,
            )
            
            # 9. 写入审计日志（任务失败）
            write_audit_log(
                operation_type=f"{self.agent_name.upper()}_FAILED",
                operator=self.agent_name,
                operation_detail={"task_id": self.current_task_id, "task_input": task_input},
                status="failed",
                error_info=self.error_info,
            )
            
            raise BaseESGException(self.error_info, original_exception=e) from e
