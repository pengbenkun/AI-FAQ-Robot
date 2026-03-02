"""
闲聊回复模块
功能：当用户问题是闲聊时，调用大模型给出友好回答
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dashscope
from app.core.config import get_settings


CHAT_PROMPT = """你是一个友好的AI问答助手。用户正在向你打招呼或进行闲聊。请给出友好、简洁的回答。

用户说：{question}

请给出一个友好的回答（1-2句话）："""


class ChatService:
    def __init__(self):
        settings = get_settings()
        if not settings.dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY is not configured")
        dashscope.api_key = settings.dashscope_api_key
        self.model = settings.model_summary
    
    async def chat(self, question: str) -> str:
        prompt = CHAT_PROMPT.format(question=question)
        
        response = await dashscope.Generation.acall(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}],
            result_format='message',
            temperature=0.7,
            max_tokens=100
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content.strip()
        
        return "您好！我是AI问答助手，可以帮您查询数据库中的数据。请告诉我您想查询什么信息？"
