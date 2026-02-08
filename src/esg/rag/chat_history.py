"""聊天历史管理"""

from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str
    content: str
    timestamp: str
    reasoning: Optional[str] = None
    sources: Optional[List[Dict]] = None
    confidence: Optional[float] = None


class ChatHistory:
    """聊天历史管理器"""
    
    def __init__(self, max_history: int = 50):
        self.messages: List[ChatMessage] = []
        self.max_history = max_history
    
    def add_user_message(self, content: str):
        """添加用户消息"""
        self.messages.append(ChatMessage(
            role="user",
            content=content,
            timestamp=datetime.now().isoformat()
        ))
        self._trim()
    
    def add_assistant_message(self, content: str, reasoning: str = None, 
                             sources: List[Dict] = None, confidence: float = None):
        """添加助手消息"""
        self.messages.append(ChatMessage(
            role="assistant",
            content=content,
            timestamp=datetime.now().isoformat(),
            reasoning=reasoning,
            sources=sources,
            confidence=confidence
        ))
        self._trim()
    
    def clear(self):
        """清空历史"""
        self.messages = []
    
    def _trim(self):
        """修剪历史"""
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
