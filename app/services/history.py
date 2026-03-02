"""
历史记录模块
功能：存储和获取用户的对话历史
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models.database import ConversationHistory, Base


class HistoryService:
    def __init__(self):
        settings = get_settings()
        
        self.engine = create_engine(
            settings.auth_db_url, 
            pool_pre_ping=True, 
            pool_recycle=3600
        )
        self.Session = sessionmaker(bind=self.engine)
    
    def _ensure_tables(self):
        Base.metadata.create_all(self.engine)
    
    async def add_message(self, session_id: str, user_id: str, role: str, 
                         content: str, sql_text: str = None):
        self._ensure_tables()
        
        session = self.Session()
        try:
            from datetime import datetime
            timestamp = int(datetime.now().timestamp() * 1000)
            
            msg = ConversationHistory(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                sql_text=sql_text,
                created_at=timestamp
            )
            session.add(msg)
            session.commit()
        finally:
            session.close()
    
    async def get_recent_history(self, session_id: str, user_id: str, 
                                 limit: int = 20) -> list[dict]:
        self._ensure_tables()
        
        session = self.Session()
        try:
            msgs = session.query(ConversationHistory).filter(
                ConversationHistory.session_id == session_id,
                ConversationHistory.user_id == user_id
            ).order_by(
                ConversationHistory.created_at.desc()
            ).limit(limit).all()
            
            msgs = list(reversed(msgs))
            
            return [
                {
                    "role": m.role,
                    "content": m.content,
                    "sql": m.sql_text,
                    "created_at": str(m.created_at)
                }
                for m in msgs
            ]
        finally:
            session.close()
    
    async def get_history(self, session_id: str, user_id: str, 
                         limit: int = 20) -> list[dict]:
        self._ensure_tables()
        
        session = self.Session()
        try:
            msgs = session.query(ConversationHistory).filter(
                ConversationHistory.session_id == session_id,
                ConversationHistory.user_id == user_id
            ).order_by(
                ConversationHistory.created_at
            ).limit(limit).all()
            
            return [
                {
                    "role": m.role,
                    "content": m.content,
                    "sql": m.sql_text,
                    "created_at": str(m.created_at)
                }
                for m in msgs
            ]
        finally:
            session.close()
