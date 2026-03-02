"""
查询改写模块
功能：根据对话历史，将口语化问题改写为规范问题
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import dashscope
from app.core.config import get_settings
from app.services.history import HistoryService
from app.prompts import QUERY_REWRITE

logger = logging.getLogger(__name__)


class QueryRewrite:
    def __init__(self):
        settings = get_settings()
        if not settings.dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY is not configured")
        dashscope.api_key = settings.dashscope_api_key
        self.model = settings.model_query_rewrite
        self.history_service = HistoryService()
        self.max_turns = settings.max_history_turns
    
    async def rewrite(self, session_id: str, user_id: str, question: str) -> str:
        history = await self.history_service.get_recent_history(
            session_id, user_id, self.max_turns
        )
        
        if not history:
            logger.info(f"查询改写：无历史记录，直接返回原问题: {question}")
            return question
        
        history_text = "\n".join([
            f"用户：{h['content']}" if h['role'] == 'user' 
            else f"助手：{h['content']}"
            for h in history
        ])
        
        logger.info(f"查询改写 - 历史记录: {history_text}")
        logger.info(f"查询改写 - 原始问题: {question}")
        
        prompt = QUERY_REWRITE.format(history=history_text, question=question)
        
        response = await dashscope.Generation.acall(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}],
            result_format='message',
            temperature=0
        )
        
        if response.status_code == 200:
            rewritten = response.output.choices[0].message.content.strip()
            logger.info(f"查询改写 - 改写后: {rewritten}")
            return rewritten
        
        logger.warning(f"查询改写失败，返回原问题: {question}")
        return question
