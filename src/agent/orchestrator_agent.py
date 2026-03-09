"""
总控调度Agent（固定流程状态机）v2.0
核心职责：按预设流程，完成：语料处理→议题检索→差距分析→生成建议

变化点（v2.0）：
- 类名 MasterAgent → OrchestratorAgent
- agent_name="master_agent" → agent_name="orchestrator_agent"
- 子Agent引用替换：extract→retrieval, compliance→analyst, content→advisor
- 流程4步改为：corpus → retrieval → analyst → advisor
"""

from typing import Dict, Any
from enum import Enum

from src.agent.base_agent import BaseAgent, AgentState
from src.core_config import get_logger
from src.utils import write_audit_log, BaseESGException


# 预设的固定流程（唯一支持的流程，无动态路由）
class FixedWorkflow(Enum):
    SINGLE_REPORT_ANALYSIS = "single_report_analysis"  # 单报告分析流程
    MULTI_COMPANY_BENCHMARK = "multi_company_benchmark"  # 多企业对标流程
    BATCH_CORPUS_PROCESSING = "batch_corpus_processing"  # 批量语料处理流程


class OrchestratorAgent(BaseAgent):
    """总控调度Agent（固定流程状态机）v2.0"""

    def __init__(self):
        super().__init__(
            agent_name="orchestrator_agent",
            agent_role="全局固定流程调度器、状态跟踪器、异常上报器",
        )
        # 延迟初始化所有执行Agent（避免循环导入问题）
        self._corpus_agent = None
        self._retrieval_agent = None
        self._analyst_agent = None
        self._advisor_agent = None

    @property
    def corpus_agent(self):
        if self._corpus_agent is None:
            from src.agent.corpus_agent import CorpusAgent
            self._corpus_agent = CorpusAgent()
        return self._corpus_agent

    @property
    def retrieval_agent(self):
        if self._retrieval_agent is None:
            from src.agent.retrieval_agent import RetrievalAgent
            self._retrieval_agent = RetrievalAgent()
        return self._retrieval_agent

    @property
    def analyst_agent(self):
        if self._analyst_agent is None:
            from src.agent.analyst_agent import AnalystAgent
            self._analyst_agent = AnalystAgent()
        return self._analyst_agent

    @property
    def advisor_agent(self):
        if self._advisor_agent is None:
            from src.agent.advisor_agent import AdvisorAgent
            self._advisor_agent = AdvisorAgent()
        return self._advisor_agent

    def _execute_single_report_analysis(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单报告分析固定流程（100%写死，无动态路由）
        流程：语料解析 → 议题检索 → 差距分析 → 生成建议
        """
        self.logger.info("开始执行单报告分析固定流程（v2.0）")
        workflow_result = {}

        # 步骤1：调用语料处理Agent（不变）
        self.logger.info("流程步骤1/4：调用语料处理Agent")
        corpus_result = self.corpus_agent.run(task_input, task_id=f"{self.current_task_id}_corpus")
        workflow_result["corpus_result"] = corpus_result

        # 步骤2：调用议题检索Agent（原ExtractAgent）
        self.logger.info("流程步骤2/4：调用议题检索Agent")
        retrieval_input = {"corpus_result": corpus_result, **task_input}
        retrieval_result = self.retrieval_agent.run(retrieval_input, task_id=f"{self.current_task_id}_retrieval")
        workflow_result["retrieval_result"] = retrieval_result

        # 步骤3：调用差距分析Agent（原ComplianceAgent）
        self.logger.info("流程步骤3/4：调用差距分析Agent")
        analyst_input = {"retrieval_result": retrieval_result, **task_input}
        analyst_result = self.analyst_agent.run(analyst_input, task_id=f"{self.current_task_id}_analyst")
        workflow_result["analyst_result"] = analyst_result

        # 步骤4：调用优化建议Agent（原ContentAgent）
        self.logger.info("流程步骤4/4：调用优化建议Agent")
        advisor_input = {"analyst_result": analyst_result, **task_input}
        advisor_result = self.advisor_agent.run(advisor_input, task_id=f"{self.current_task_id}_advisor")
        workflow_result["advisor_result"] = advisor_result

        # 流程结束
        self.logger.info("单报告分析流程完成")
        workflow_result["workflow_status"] = "completed"

        return workflow_result

    def _execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行固定流程调度（仅按预设流程分发任务）
        :param task_input: 必须包含 workflow_type 字段（FixedWorkflow枚举值）
        :return: 全流程执行结果
        """
        # 1. 校验流程类型（仅支持预设的固定流程）
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
            # TODO[P2]: 多企业对标流程 - 预留接口，待后续迭代实现
            raise BaseESGException("多企业对标流程暂未实现（预留接口）")
        elif workflow_type == FixedWorkflow.BATCH_CORPUS_PROCESSING:
            # TODO[P2]: 批量语料处理流程 - 预留接口，待后续迭代实现
            raise BaseESGException("批量语料处理流程暂未实现（预留接口）")
        else:
            raise BaseESGException(f"未知流程类型: {workflow_type}")
