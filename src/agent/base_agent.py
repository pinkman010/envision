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


class AgentState(Enum):
    """统一Agent状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class BaseAgent(abc.ABC):
    """所有Agent的抽象基类"""

    def __init__(self, agent_name: str, agent_role: str):
        """
        初始化Agent
        :param agent_name: Agent唯一名称
        :param agent_role: Agent明确角色描述
        """
        self.agent_name = agent_name
        self.agent_role = agent_role
        self.state = AgentState.IDLE
        self.current_task_id: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.error_info: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        
        self.logger = get_logger(f"agent.{agent_name}")
        self.logger.info(f"Agent初始化完成: {agent_name} ({agent_role})")

    def reset(self) -> None:
        """重置Agent状态"""
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
        抽象方法：执行具体任务逻辑
        :param task_input: 任务输入参数
        :return: 任务执行结果
        """
        pass

    def run(self, task_input: Dict[str, Any], task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        统一任务执行入口
        :param task_input: 任务输入参数
        :param task_id: 任务唯一ID
        :return: 任务执行结果
        """
        self.reset()
        self.current_task_id = task_id or f"{self.agent_name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        self.start_time = datetime.utcnow()
        self.state = AgentState.RUNNING
        self.logger.info(f"开始执行任务: {self.current_task_id}")

        write_audit_log(
            operation_type=f"{self.agent_name.upper()}_START",
            operator=self.agent_name,
            operation_detail={"task_id": self.current_task_id},
            status="running",
        )

        try:
            self.result = self._execute(task_input)
            
            self.state = AgentState.SUCCESS
            self.end_time = datetime.utcnow()
            self.logger.info(f"任务执行成功: {self.current_task_id}")
            
            write_audit_log(
                operation_type=f"{self.agent_name.upper()}_SUCCESS",
                operator=self.agent_name,
                operation_detail={"task_id": self.current_task_id},
                status="success",
            )
            
            return self.result

        except BaseESGException as e:
            self.state = AgentState.FAILED
            self.error_info = e.message
            self.end_time = datetime.utcnow()
            self.logger.error(f"任务执行失败: {self.current_task_id}, 错误: {self.error_info}")
            
            write_audit_log(
                operation_type=f"{self.agent_name.upper()}_FAILED",
                operator=self.agent_name,
                operation_detail={"task_id": self.current_task_id},
                status="failed",
                error_info=self.error_info,
            )
            
            raise

        except Exception as e:
            self.state = AgentState.FAILED
            self.error_info = f"未知错误: {str(e)}"
            self.end_time = datetime.utcnow()
            self.logger.critical(f"任务执行未知错误: {self.current_task_id}")
            
            write_audit_log(
                operation_type=f"{self.agent_name.upper()}_FAILED",
                operator=self.agent_name,
                operation_detail={"task_id": self.current_task_id},
                status="failed",
                error_info=self.error_info,
            )
            
            raise BaseESGException(self.error_info, original_exception=e) from e
