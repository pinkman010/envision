"""
总控调度Agent（固定流程状态机）
核心职责：按预设的3条固定流程，完成任务分发、状态跟踪、异常上报、结果汇总
无任何业务逻辑、无动态路由、无自然语言解析
"""

from typing import Dict, Any
from enum import Enum

from src.agent.base_agent import BaseAgent, AgentState
from src.core_config import get_logger
from src.utils import write_audit_log, BaseESGException


# 预设的3条固定流程（唯一支持的流程，无动态路由）
class FixedWorkflow(Enum):
    SINGLE_REPORT_ANALYSIS = "single_report_analysis"  # 单报告分析流程
    MULTI_COMPANY_BENCHMARK = "multi_company_benchmark"  # 多企业对标流程
    BATCH_CORPUS_PROCESSING = "batch_corpus_processing"  # 批量语料处理流程


class MasterAgent(BaseAgent):
    """总控调度Agent（固定流程状态机）"""

    def __init__(self):
        super().__init__(
            agent_name="master_agent",
            agent_role="全局固定流程调度器、状态跟踪器、异常上报器",
        )
        # 延迟初始化所有执行Agent（避免循环导入问题）
        self._corpus_agent = None
        self._extract_agent = None
        self._compliance_agent = None
        self._content_agent = None

    @property
    def corpus_agent(self):
        if self._corpus_agent is None:
            from src.agent.corpus_agent import CorpusAgent
            self._corpus_agent = CorpusAgent()
        return self._corpus_agent

    @property
    def extract_agent(self):
        if self._extract_agent is None:
            from src.agent.extract_agent import ExtractAgent
            self._extract_agent = ExtractAgent()
        return self._extract_agent

    @property
    def compliance_agent(self):
        if self._compliance_agent is None:
            from src.agent.compliance_agent import ComplianceAgent
            self._compliance_agent = ComplianceAgent()
        return self._compliance_agent

    @property
    def content_agent(self):
        if self._content_agent is None:
            from src.agent.content_agent import ContentAgent
            self._content_agent = ContentAgent()
        return self._content_agent

    def _execute_single_report_analysis(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单报告分析固定流程（100%写死，无动态路由）
        流程：语料解析 → 信息抽取 → 合规提示 → 等待人工复核
        """
        self.logger.info("开始执行单报告分析固定流程")
        workflow_result = {}

        # 步骤1：调用语料处理Agent
        self.logger.info("流程步骤1/4：调用语料处理Agent")
        corpus_result = self.corpus_agent.run(task_input, task_id=f"{self.current_task_id}_corpus")
        workflow_result["corpus_result"] = corpus_result

        # 步骤2：调用信息抽取Agent
        self.logger.info("流程步骤2/4：调用信息抽取Agent")
        extract_input = {"corpus_result": corpus_result, **task_input}
        extract_result = self.extract_agent.run(extract_input, task_id=f"{self.current_task_id}_extract")
        workflow_result["extract_result"] = extract_result

        # 步骤3：调用合规提示Agent
        self.logger.info("流程步骤3/4：调用合规提示Agent")
        compliance_input = {"extract_result": extract_result, **task_input}
        compliance_result = self.compliance_agent.run(compliance_input, task_id=f"{self.current_task_id}_compliance")
        workflow_result["compliance_result"] = compliance_result

        # 步骤4：流程结束，等待人工复核（不自动进入下一步）
        self.logger.info("流程步骤4/4：单报告分析流程完成，等待人工复核")
        workflow_result["workflow_status"] = "pending_review"
        workflow_result["next_step"] = "人工复核中心"

        return workflow_result

    def _execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行固定流程调度（仅按预设流程分发任务）
        :param task_input: 必须包含 workflow_type 字段（FixedWorkflow枚举值）
        :return: 全流程执行结果
        """
        # 1. 校验流程类型（仅支持预设的3条固定流程）
        workflow_type_str = task_input.get("workflow_type")
        if not workflow_type_str:
            raise BaseESGException("任务输入缺少必填字段: workflow_type")
        
        try:
            workflow_type = FixedWorkflow(workflow_type_str)
        except ValueError:
            raise BaseESGException(
                f"不支持的流程类型: {workflow_type_str}, "
                f"仅支持: {[w.value for w in FixedWorkflow]}"
            )

        # 2. 按预设流程执行（100%写死，无动态路由）
        if workflow_type == FixedWorkflow.SINGLE_REPORT_ANALYSIS:
            return self._execute_single_report_analysis(task_input)
        elif workflow_type == FixedWorkflow.MULTI_COMPANY_BENCHMARK:
            # TODO: MVP阶段先实现单报告分析，多企业对标后续扩展
            raise BaseESGException("多企业对标流程暂未实现（MVP阶段）")
        elif workflow_type == FixedWorkflow.BATCH_CORPUS_PROCESSING:
            # TODO: MVP阶段先实现单报告分析，批量处理后续扩展
            raise BaseESGException("批量语料处理流程暂未实现（MVP阶段）")
        else:
            raise BaseESGException(f"未知流程类型: {workflow_type}")
