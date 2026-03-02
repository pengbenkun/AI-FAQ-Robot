from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, BigInteger, Enum, UniqueConstraint, Index
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import enum

Base = declarative_base()


class PermissionType(enum.Enum):
    SELECT = "SELECT"


class UserTablePermission(Base):
    __tablename__ = "user_table_permission"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False)
    table_name = Column(String(128), nullable=False)
    permission_type = Column(String(32), default="SELECT")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'table_name', name='uq_user_table'),
        Index('idx_user_id', 'user_id'),
    )


class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False)
    user_id = Column(String(64), nullable=False)
    role = Column(Enum('user', 'assistant'), nullable=False)
    content = Column(Text, nullable=False)
    sql_text = Column(Text, nullable=True)
    created_at = Column(BigInteger, default=lambda: int(datetime.now().timestamp() * 1000))
    
    __table_args__ = (
        Index('idx_session_user', 'session_id', 'user_id'),
        Index('idx_created_at', 'created_at'),
    )


def get_auth_engine(auth_db_url: str):
    return create_engine(auth_db_url, pool_pre_ping=True, pool_recycle=3600)


def get_auth_session(auth_db_url: str):
    engine = get_auth_engine(auth_db_url)
    Session = sessionmaker(bind=engine)
    return Session()


def init_auth_db(auth_db_url: str):
    engine = get_auth_engine(auth_db_url)
    Base.metadata.create_all(engine)
