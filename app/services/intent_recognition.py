"""
意图识别模块
功能：判断用户问题是"数据查询"还是"闲聊"
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dashscope
import logging
from app.core.config import get_settings
from app.prompts import INTENT_RECOGNITION

logger = logging.getLogger(__name__)


class IntentRecognition:
    def __init__(self):
        settings = get_settings()
        if not settings.dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY is not configured")
        dashscope.api_key = settings.dashscope_api_key
        self.model = settings.model_intent
    
    async def recognize(self, question: str) -> str:
        prompt = INTENT_RECOGNITION.format(question=question)
        
        response = await dashscope.Generation.acall(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}],
            result_format='message',
            temperature=0
        )
        
        result = "chat"
        if response.status_code == 200:
            content = response.output.choices[0].message.content.strip()
            logger.info(f"意图识别原始返回: {content}")
            
            content_lower = content.lower()
            if "query" in content_lower:
                result = "query"
        
        logger.info(f"意图识别最终结果: {result}")
        return result
