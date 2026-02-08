"""Ollama客户端单元测试

覆盖OllamaClient的各种使用场景、异常处理和边界条件。
使用Mock对象模拟HTTP请求。
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.esg.utils.ollama_client import (
    OllamaClient,
    OllamaConnectionError,
    OllamaError,
    OllamaResponseError,
    OllamaTimeoutError,
    retry_with_backoff,
)


class TestRetryWithBackoff(unittest.TestCase):
    """重试装饰器测试"""

    def test_successful_call_no_retry(self):
        """测试成功调用不重试"""
        call_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = success_func()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 1)

    def test_retry_on_exception(self):
        """测试异常时重试"""
        call_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            return "success"

        result = fail_then_succeed()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)

    def test_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        call_count = 0

        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent error")

        with self.assertRaises(Exception) as context:
            always_fail()

        self.assertEqual(call_count, 3)  # 初始 + 2次重试
        self.assertIn("Persistent error", str(context.exception))

    def test_specific_exception_types(self):
        """测试特定异常类型重试"""
        call_count = 0

        @retry_with_backoff(max_retries=2, initial_delay=0.01, exceptions=(ValueError,))
        def raise_different_errors():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Should retry")
            return "success"

        result = raise_different_errors()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 2)


class TestOllamaClientInit(unittest.TestCase):
    """Ollama客户端初始化测试"""

    def test_default_init(self):
        """测试默认初始化"""
        client = OllamaClient()
        self.assertIsNone(client.model)
        self.assertEqual(client.url, "http://localhost:11434")
        self.assertEqual(client.timeout, 120)
        self.assertEqual(client.max_retries, 3)

    def test_custom_init(self):
        """测试自定义参数初始化"""
        client = OllamaClient(model="llama2", url="http://custom:11434", timeout=60, max_retries=5)
        self.assertEqual(client.model, "llama2")
        self.assertEqual(client.url, "http://custom:11434")
        self.assertEqual(client.timeout, 60)
        self.assertEqual(client.max_retries, 5)

    def test_url_trailing_slash_removal(self):
        """测试URL尾部斜杠移除"""
        client = OllamaClient(url="http://localhost:11434/")
        self.assertEqual(client.url, "http://localhost:11434")

    def test_session_creation(self):
        """测试会话创建"""
        client = OllamaClient()
        self.assertIsNotNone(client.session)
        self.assertEqual(client.session.headers["Content-Type"], "application/json")


class TestOllamaClientEmbed(unittest.TestCase):
    """嵌入向量生成测试"""

    def setUp(self):
        """测试前置"""
        self.client = OllamaClient(model="nomic-embed-text")

    def tearDown(self):
        """测试后置"""
        self.client.close()

    @patch.object(OllamaClient, "_make_request")
    def test_embed_success(self, mock_make_request):
        """测试成功生成嵌入向量"""
        mock_make_request.return_value = {"embedding": [0.1, 0.2, 0.3]}

        result = self.client.embed("测试文本")

        self.assertEqual(len(result), 3)
        self.assertEqual(result, [0.1, 0.2, 0.3])
        mock_make_request.assert_called_once()

    @patch.object(OllamaClient, "_make_request")
    def test_embed_no_model(self, mock_make_request):
        """测试未指定模型"""
        client = OllamaClient()  # 无模型

        with self.assertRaises(ValueError) as context:
            client.embed("测试文本")

        self.assertIn("必须先指定模型名称", str(context.exception))

    @patch.object(OllamaClient, "_make_request")
    def test_embed_empty_text(self, mock_make_request):
        """测试空文本"""
        result = self.client.embed("   ")

        self.assertEqual(len(result), 768)
        self.assertEqual(sum(result), 0.0)  # 零向量

    @patch.object(OllamaClient, "_make_request")
    def test_embed_missing_embedding(self, mock_make_request):
        """测试响应缺少embedding字段"""
        mock_make_request.return_value = {"other_field": "value"}

        with self.assertRaises(OllamaResponseError) as context:
            self.client.embed("测试文本")

        self.assertIn("缺少 embedding 字段", str(context.exception))

    @patch.object(OllamaClient, "_make_request")
    def test_embed_api_error(self, mock_make_request):
        """测试API错误"""
        mock_make_request.side_effect = OllamaError("API错误")

        with self.assertRaises(OllamaError):
            self.client.embed("测试文本")


class TestOllamaClientGenerate(unittest.TestCase):
    """文本生成测试"""

    def setUp(self):
        """测试前置"""
        self.client = OllamaClient(model="llama2")

    def tearDown(self):
        """测试后置"""
        self.client.close()

    @patch.object(OllamaClient, "_make_request")
    def test_generate_success(self, mock_make_request):
        """测试成功生成文本"""
        mock_make_request.return_value = {"response": "生成的回答"}

        result = self.client.generate("提示词")

        self.assertEqual(result, "生成的回答")

    @patch.object(OllamaClient, "_make_request")
    def test_generate_with_options(self, mock_make_request):
        """测试带选项生成"""
        mock_make_request.return_value = {"response": "回答"}

        result = self.client.generate("提示词", temperature=0.7, top_p=0.9, max_tokens=100)

        self.assertEqual(result, "回答")
        # 验证调用参数 - _make_request(method, endpoint, json_data)
        call_args = mock_make_request.call_args
        json_data = call_args[0][2]  # 第三个位置参数
        self.assertIn("options", json_data)
        self.assertIn("temperature", json_data["options"])

    def test_generate_no_model(self):
        """测试未指定模型"""
        client = OllamaClient()

        with self.assertRaises(ValueError):
            client.generate("提示词")

    def test_generate_empty_prompt(self):
        """测试空提示词"""
        result = self.client.generate("")
        self.assertEqual(result, "")

    @patch.object(OllamaClient, "_make_request")
    def test_generate_missing_response(self, mock_make_request):
        """测试响应缺少response字段"""
        mock_make_request.return_value = {"other": "value"}

        with self.assertRaises(OllamaResponseError):
            self.client.generate("提示词")

    @patch.object(OllamaClient, "_make_request")
    def test_generate_with_none_options(self, mock_make_request):
        """测试带None值的选项"""
        mock_make_request.return_value = {"response": "回答"}

        result = self.client.generate("提示词", temperature=0.7, top_p=None, max_tokens=100)

        # None值应该被过滤掉
        call_args = mock_make_request.call_args
        json_data = call_args[0][2]  # 第三个位置参数
        options = json_data["options"]
        self.assertNotIn("top_p", options)


class TestOllamaClientChat(unittest.TestCase):
    """对话测试"""

    def setUp(self):
        """测试前置"""
        self.client = OllamaClient(model="llama2")

    def tearDown(self):
        """测试后置"""
        self.client.close()

    @patch.object(OllamaClient, "_make_request")
    def test_chat_success(self, mock_make_request):
        """测试成功对话"""
        mock_make_request.return_value = {"message": {"content": "助手回答"}}

        messages = [{"role": "system", "content": "你是助手"}, {"role": "user", "content": "你好"}]
        result = self.client.chat(messages)

        self.assertEqual(result, "助手回答")

    def test_chat_no_model(self):
        """测试未指定模型"""
        client = OllamaClient()

        with self.assertRaises(ValueError):
            client.chat([{"role": "user", "content": "你好"}])

    def test_chat_empty_messages(self):
        """测试空消息列表"""
        with self.assertRaises(ValueError):
            self.client.chat([])

    def test_chat_invalid_message_format(self):
        """测试无效消息格式"""
        with self.assertRaises(ValueError):
            self.client.chat([{"invalid": "message"}])

    def test_chat_invalid_role(self):
        """测试无效角色"""
        with self.assertRaises(ValueError):
            self.client.chat([{"role": "invalid", "content": "你好"}])

    @patch.object(OllamaClient, "_make_request")
    def test_chat_missing_content(self, mock_make_request):
        """测试响应缺少content字段"""
        mock_make_request.return_value = {"message": {}}

        with self.assertRaises(OllamaResponseError):
            self.client.chat([{"role": "user", "content": "你好"}])


class TestOllamaClientCheck(unittest.TestCase):
    """健康检查测试"""

    @patch("src.esg.utils.ollama_client.requests.Session.get")
    def test_check_success(self, mock_get):
        """测试健康检查成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = OllamaClient()
        result = client.check()

        self.assertTrue(result)

    @patch("src.esg.utils.ollama_client.requests.Session.get")
    def test_check_failure(self, mock_get):
        """测试健康检查失败"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        client = OllamaClient()
        result = client.check()

        self.assertFalse(result)

    @patch("src.esg.utils.ollama_client.requests.Session.get")
    def test_check_connection_error(self, mock_get):
        """测试连接错误"""
        import requests

        mock_get.side_effect = requests.ConnectionError("Connection failed")

        client = OllamaClient()
        result = client.check()

        self.assertFalse(result)


class TestOllamaClientExceptions(unittest.TestCase):
    """异常类测试"""

    def test_ollama_error(self):
        """测试基础异常"""
        error = OllamaError("基础错误")
        self.assertEqual(str(error), "基础错误")

    def test_connection_error(self):
        """测试连接异常"""
        error = OllamaConnectionError("连接失败")
        self.assertEqual(str(error), "连接失败")
        self.assertIsInstance(error, OllamaError)

    def test_timeout_error(self):
        """测试超时异常"""
        error = OllamaTimeoutError("请求超时")
        self.assertEqual(str(error), "请求超时")
        self.assertIsInstance(error, OllamaError)

    def test_response_error_with_details(self):
        """测试响应异常带详情"""
        error = OllamaResponseError(
            "响应错误", status_code=500, response_text="Internal Server Error"
        )
        self.assertEqual(error.status_code, 500)
        self.assertEqual(error.response_text, "Internal Server Error")


class TestOllamaClientContextManager(unittest.TestCase):
    """上下文管理器测试"""

    def test_context_manager(self):
        """测试上下文管理器"""
        with OllamaClient() as client:
            self.assertIsNotNone(client.session)
        # 退出上下文后应该关闭

    @patch.object(OllamaClient, "close")
    def test_context_manager_calls_close(self, mock_close):
        """测试上下文管理器调用close"""
        with OllamaClient() as client:
            pass

        mock_close.assert_called_once()


class TestOllamaClientEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def test_very_long_prompt(self):
        """测试超长提示词"""
        client = OllamaClient(model="test")
        long_prompt = "A" * 100000

        with patch.object(client, "_make_request") as mock_make_request:
            mock_make_request.return_value = {"response": "回答"}
            result = client.generate(long_prompt)

            self.assertEqual(result, "回答")

    def test_unicode_content(self):
        """测试Unicode内容"""
        client = OllamaClient(model="test")

        with patch.object(client, "_make_request") as mock_make_request:
            mock_make_request.return_value = {"response": "🌱 回答"}
            result = client.generate("🌍 提示词")

            self.assertIn("🌱", result)

    def test_special_characters_in_prompt(self):
        """测试特殊字符"""
        client = OllamaClient(model="test")
        special_prompt = "<script>alert('xss')</script>"

        with patch.object(client, "_make_request") as mock_make_request:
            mock_make_request.return_value = {"response": "回答"}
            result = client.generate(special_prompt)

            self.assertEqual(result, "回答")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestRetryWithBackoff,
        TestOllamaClientInit,
        TestOllamaClientEmbed,
        TestOllamaClientGenerate,
        TestOllamaClientChat,
        TestOllamaClientCheck,
        TestOllamaClientExceptions,
        TestOllamaClientContextManager,
        TestOllamaClientEdgeCases,
    ]

    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
