"""RAG引擎单元测试

覆盖RAGEngine的各种使用场景，使用Mock对象模拟向量存储和LLM服务。
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import json

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.engine import RAGEngine, RAGResponse


class MockChromaDBStore:
    """Mock向量存储类"""
    
    def __init__(self, documents=None):
        self.documents = documents or []
    
    def search(self, query, top_k=5):
        """模拟搜索"""
        return self.documents[:top_k]


class TestRAGEngine(unittest.TestCase):
    """RAG引擎测试类"""
    
    def setUp(self):
        """测试前置设置"""
        self.sample_documents = [
            {
                "text": "ESG代表环境、社会和治理。环境方面包括碳排放、能源使用等。",
                "metadata": {"source": "ESG指南.pdf", "page": 1},
                "score": 0.85
            },
            {
                "text": "企业社会责任(CSR)是公司对社会和环境的责任。",
                "metadata": {"source": "CSR报告.pdf", "page": 3},
                "score": 0.75
            },
            {
                "text": "公司治理涉及董事会结构、审计和风险管理。",
                "metadata": {"source": "治理手册.pdf", "page": 5},
                "score": 0.65
            }
        ]
    
    def test_init_default(self):
        """测试默认初始化"""
        with patch('src.rag.engine.ChromaDBStore') as mock_store:
            mock_store.return_value = MockChromaDBStore()
            engine = RAGEngine()
            self.assertIsNotNone(engine.store)
            self.assertIsNotNone(engine.model)
    
    def test_init_with_custom_model(self):
        """测试自定义模型初始化"""
        with patch('src.rag.engine.ChromaDBStore'):
            engine = RAGEngine(model="custom-model")
            self.assertEqual(engine.model, "custom-model")
    
    def test_init_with_custom_store(self):
        """测试自定义存储初始化"""
        mock_store = MockChromaDBStore()
        engine = RAGEngine(store=mock_store)
        self.assertEqual(engine.store, mock_store)
    
    @patch('src.rag.engine.requests.post')
    def test_query_normal_flow(self, mock_post):
        """测试正常查询流程"""
        # 设置mock响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": """<thinking>
1. 用户询问ESG是什么
2. 从文档中找到ESG定义
3. ESG代表环境、社会和治理
</thinking>

<answer>
ESG代表环境(Environmental)、社会(Social)和治理(Governance)。
</answer>"""
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # 创建引擎
        mock_store = MockChromaDBStore(self.sample_documents)
        engine = RAGEngine(model="test-model", store=mock_store)
        
        # 执行查询
        result = engine.query("什么是ESG？")
        
        # 验证结果
        self.assertIsInstance(result, RAGResponse)
        self.assertIn("环境", result.answer)
        self.assertIn("社会", result.answer)
        self.assertIn("治理", result.answer)
        self.assertGreater(len(result.reasoning), 0)
        self.assertEqual(len(result.sources), 3)
        self.assertGreater(result.confidence, 0)
    
    def test_query_empty_knowledge_base(self):
        """测试空知识库场景"""
        mock_store = MockChromaDBStore([])  # 空文档列表
        engine = RAGEngine(model="test-model", store=mock_store)
        
        result = engine.query("什么是ESG？")
        
        self.assertIsInstance(result, RAGResponse)
        self.assertIn("未找到相关信息", result.answer)
        self.assertEqual(result.confidence, 0.0)
        self.assertEqual(len(result.sources), 0)
    
    @patch('src.rag.engine.requests.post')
    def test_query_llm_service_unavailable(self, mock_post):
        """测试LLM服务不可用场景"""
        # 模拟请求异常
        mock_post.side_effect = Exception("Connection refused")
        
        mock_store = MockChromaDBStore(self.sample_documents)
        engine = RAGEngine(model="test-model", store=mock_store)
        
        result = engine.query("什么是ESG？")
        
        self.assertIsInstance(result, RAGResponse)
        self.assertIn("生成失败", result.answer)
    
    @patch('src.rag.engine.requests.post')
    def test_query_llm_timeout(self, mock_post):
        """测试LLM服务超时"""
        from requests.exceptions import Timeout
        mock_post.side_effect = Timeout("Request timeout")
        
        mock_store = MockChromaDBStore(self.sample_documents)
        engine = RAGEngine(model="test-model", store=mock_store)
        
        result = engine.query("什么是ESG？")
        
        self.assertIsInstance(result, RAGResponse)
        self.assertIn("生成失败", result.answer)
    
    @patch('src.rag.engine.requests.post')
    def test_query_llm_http_error(self, mock_post):
        """测试LLM返回HTTP错误"""
        from requests.exceptions import HTTPError
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError("500 Server Error")
        mock_post.return_value = mock_response
        
        mock_store = MockChromaDBStore(self.sample_documents)
        engine = RAGEngine(model="test-model", store=mock_store)
        
        result = engine.query("什么是ESG？")
        
        self.assertIsInstance(result, RAGResponse)
        self.assertIn("生成失败", result.answer)
    
    def test_build_prompt(self):
        """测试提示词构建"""
        mock_store = MockChromaDBStore()
        engine = RAGEngine(model="test-model", store=mock_store)
        
        documents = [
            {"text": "文档1内容" * 100, "metadata": {"source": "doc1.pdf"}},
            {"text": "文档2内容", "metadata": {"source": "doc2.pdf"}}
        ]
        
        prompt = engine._build_prompt("测试问题", documents)
        
        # 验证提示词结构
        self.assertIn("ESG领域", prompt)
        self.assertIn("测试问题", prompt)
        self.assertIn("文档1", prompt)
        self.assertIn("文档2", prompt)
        self.assertIn("<thinking>", prompt)
        self.assertIn("<answer>", prompt)
    
    def test_build_prompt_truncation(self):
        """测试长文档截断"""
        mock_store = MockChromaDBStore()
        engine = RAGEngine(model="test-model", store=mock_store)
        
        # 创建超长文档
        long_text = "A" * 1000
        documents = [{"text": long_text, "metadata": {"source": "long.pdf"}}]
        
        prompt = engine._build_prompt("测试问题", documents)
        
        # 验证长文档被截断到500字符
        self.assertLess(len(prompt), 2000)
    
    @patch('src.rag.engine.requests.post')
    def test_extract_thinking_thinking_tag(self, mock_post):
        """测试<thinking>标签提取"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": """<thinking>
思考过程在这里
多行内容
</thinking>

<answer>
最终答案
</answer>"""
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        mock_store = MockChromaDBStore(self.sample_documents)
        engine = RAGEngine(model="test-model", store=mock_store)
        
        result = engine.query("测试")
        
        self.assertIn("思考过程在这里", result.reasoning)
        self.assertIn("最终答案", result.answer)
    
    @patch('src.rag.engine.requests.post')
    def test_extract_thinking_think_tag(self, mock_post):
        """测试<think>标签提取"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": """<think>
这是思考内容
</think>

这是答案内容"""
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        mock_store = MockChromaDBStore(self.sample_documents)
        engine = RAGEngine(model="test-model", store=mock_store)
        
        result = engine.query("测试")
        
        self.assertIn("这是思考内容", result.reasoning)
        self.assertIn("这是答案内容", result.answer)
    
    @patch('src.rag.engine.requests.post')
    def test_extract_thinking_chinese_markers(self, mock_post):
        """测试中文标记提取"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": """思考：
1. 分析问题
2. 查找资料

答案：
这是最终答案"""
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        mock_store = MockChromaDBStore(self.sample_documents)
        engine = RAGEngine(model="test-model", store=mock_store)
        
        result = engine.query("测试")
        
        self.assertIn("分析问题", result.reasoning)
        self.assertIn("最终答案", result.answer)
    
    @patch('src.rag.engine.requests.post')
    def test_extract_thinking_no_format(self, mock_post):
        """测试无格式输出处理"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "这是一个没有特定格式的简单回答"
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        mock_store = MockChromaDBStore(self.sample_documents)
        engine = RAGEngine(model="test-model", store=mock_store)
        
        result = engine.query("测试")
        
        # 验证返回了reasoning和answer
        self.assertGreater(len(result.reasoning), 0)
        self.assertIn("简单回答", result.answer)
    
    def test_calculate_confidence(self):
        """测试置信度计算"""
        mock_store = MockChromaDBStore()
        engine = RAGEngine(model="test-model", store=mock_store)
        
        # 测试高置信度文档
        high_conf_docs = [
            {"score": 0.9},
            {"score": 0.8},
            {"score": 0.85}
        ]
        confidence = engine._calculate_confidence(high_conf_docs)
        self.assertGreater(confidence, 0.5)
        self.assertLessEqual(confidence, 1.0)
        
        # 测试低置信度文档
        low_conf_docs = [
            {"score": 0.5},
            {"score": 0.6}
        ]
        confidence = engine._calculate_confidence(low_conf_docs)
        self.assertLess(confidence, 0.5)
        
        # 测试空文档
        confidence = engine._calculate_confidence([])
        self.assertEqual(confidence, 0.0)
        
        # 测试无分数文档
        no_score_docs = [{}, {}]
        confidence = engine._calculate_confidence(no_score_docs)
        self.assertEqual(confidence, 0.0)
    
    def test_calculate_confidence_boundary(self):
        """测试置信度边界值"""
        mock_store = MockChromaDBStore()
        engine = RAGEngine(model="test-model", store=mock_store)
        
        # 测试最高可能置信度
        max_docs = [{"score": 1.0}]
        confidence = engine._calculate_confidence(max_docs)
        self.assertEqual(confidence, 1.0)
        
        # 测试最低可能置信度（非零）
        min_docs = [{"score": 0.5}]
        confidence = engine._calculate_confidence(min_docs)
        self.assertEqual(confidence, 0.0)
        
        # 测试低于0.5的分数应该返回0
        below_threshold = [{"score": 0.4}]
        confidence = engine._calculate_confidence(below_threshold)
        self.assertEqual(confidence, 0.0)
    
    @patch('src.rag.engine.requests.post')
    def test_deepseek_r1_options(self, mock_post):
        """测试deepseek-r1模型特殊选项"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "测试回答"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        mock_store = MockChromaDBStore(self.sample_documents)
        engine = RAGEngine(model="deepseek-r1:7b", store=mock_store)
        
        result = engine.query("测试")
        
        # 验证请求参数中包含特殊选项
        call_args = mock_post.call_args
        json_data = call_args[1]['json']
        self.assertIn('options', json_data)
        self.assertIn('num_predict', json_data['options'])
    
    def test_rag_response_dataclass(self):
        """测试RAGResponse数据类"""
        response = RAGResponse(
            answer="测试答案",
            reasoning="测试推理",
            sources=[{"text": "来源1"}],
            confidence=0.85
        )
        
        self.assertEqual(response.answer, "测试答案")
        self.assertEqual(response.reasoning, "测试推理")
        self.assertEqual(len(response.sources), 1)
        self.assertEqual(response.confidence, 0.85)


class TestRAGEngineEdgeCases(unittest.TestCase):
    """RAG引擎边界情况测试"""
    
    @patch('src.rag.engine.requests.post')
    def test_query_special_characters(self, mock_post):
        """测试特殊字符查询"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "<answer>答案</answer>"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        mock_store = MockChromaDBStore([
            {"text": "文档", "metadata": {}, "score": 0.8}
        ])
        engine = RAGEngine(model="test-model", store=mock_store)
        
        # 测试包含特殊字符的查询
        special_queries = [
            "ESG < 环境",
            "CSR > 社会责任",
            "ESG & CSR",
            "ESG 'OR' CSR",
            'ESG "AND" CSR',
        ]
        
        for query in special_queries:
            result = engine.query(query)
            self.assertIsInstance(result, RAGResponse)
    
    @patch('src.rag.engine.requests.post')
    def test_query_very_long_question(self, mock_post):
        """测试超长问题"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "<answer>答案</answer>"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        mock_store = MockChromaDBStore([
            {"text": "文档", "metadata": {}, "score": 0.8}
        ])
        engine = RAGEngine(model="test-model", store=mock_store)
        
        long_query = "ESG " * 1000
        result = engine.query(long_query)
        
        self.assertIsInstance(result, RAGResponse)
    
    @patch('src.rag.engine.requests.post')
    def test_query_unicode_content(self, mock_post):
        """测试Unicode内容"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "<thinking>思考</thinking><answer>🌱 ESG很重要</answer>"
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        mock_store = MockChromaDBStore([
            {"text": "🌍 环境内容", "metadata": {}, "score": 0.8}
        ])
        engine = RAGEngine(model="test-model", store=mock_store)
        
        result = engine.query("ESG含义？")
        
        self.assertIsInstance(result, RAGResponse)
        self.assertIn("🌱", result.answer)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestRAGEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestRAGEngineEdgeCases))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
