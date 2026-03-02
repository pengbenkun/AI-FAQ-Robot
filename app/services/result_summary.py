"""
结果总结模块
功能：将 SQL 查询结果发送给大模型，生成友好的自然语言回答
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dashscope
from app.core.config import get_settings
from app.prompts import RESULT_SUMMARY


class ResultSummaryService:
    def __init__(self):
        settings = get_settings()
        if not settings.dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY is not configured")
        dashscope.api_key = settings.dashscope_api_key
        self.model = settings.model_summary
    
    async def summarize(self, question: str, sql_result: str) -> str:
        prompt = RESULT_SUMMARY.format(question=question, sql_result=sql_result)
        
        response = await dashscope.Generation.acall(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}],
            result_format='message',
            temperature=0.7
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content.strip()
        
        return sql_result
