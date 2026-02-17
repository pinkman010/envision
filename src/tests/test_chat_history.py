"""聊天历史单元测试

覆盖ChatHistory的各种使用场景。
"""

import pytest

# 模块不存在时跳过整个测试文件
pytest.importorskip("src.esg.rag.chat_history", reason="src.esg.rag.chat_history 模块不存在")

from src.esg.rag.chat_history import ChatHistory


class TestChatHistory:
    """聊天历史测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.history = ChatHistory()

    def test_chat_history_init(self):
        """测试初始化"""
        assert self.history is not None
        assert len(self.history.messages) == 0

    def test_add_user_message(self):
        """测试添加用户消息"""
        self.history.add_user_message("你好")
        assert len(self.history.messages) == 1
        # messages是ChatMessage对象列表
        assert self.history.messages[0].role == "user"

    def test_add_assistant_message(self):
        """测试添加助手消息"""
        self.history.add_assistant_message("你好，我是ESG助手")
        assert len(self.history.messages) == 1
        assert self.history.messages[0].role == "assistant"

    def test_add_multiple_messages(self):
        """测试添加多条消息"""
        self.history.add_user_message("问题1")
        self.history.add_assistant_message("回答1")
        self.history.add_user_message("问题2")
        assert len(self.history.messages) == 3

    def test_clear(self):
        """测试清除历史"""
        self.history.add_user_message("你好")
        self.history.add_assistant_message("你好")
        self.history.clear()
        assert len(self.history.messages) == 0
