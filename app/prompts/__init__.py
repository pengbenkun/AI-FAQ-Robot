"""
提示词统一管理模块
"""

from app.prompts.intent import INTENT_RECOGNITION
from app.prompts.query_rewrite import QUERY_REWRITE
from app.prompts.nl2sql import NL2SQL, NL2SQL_FEWSHOT_EXAMPLE, MANDATORY_CONDITIONS
from app.prompts.result_summary import RESULT_SUMMARY

__all__ = [
    "INTENT_RECOGNITION",
    "QUERY_REWRITE",
    "NL2SQL",
    "NL2SQL_FEWSHOT_EXAMPLE",
    "MANDATORY_CONDITIONS",
    "RESULT_SUMMARY",
]
