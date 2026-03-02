# 煤炭设计院数据中台AI问答机器人 - 系统实现规范

## 1. 项目概述

本规范基于《AI问答机器人.md》项目方案，详细描述系统实现的技术细节、数据库设计、API规范和核心模块实现方案。

**项目名称**：煤炭设计院数据中台AI问答机器人
**技术栈**：FastAPI + LangChain + 阿里云DashScope + MySQL + Chroma
**核心功能**：自然语言转SQL查询、细粒度权限控制、多轮对话

---

## 2. 数据库设计

### 2.1 权限与历史库（MySQL）

#### 2.1.1 用户表权限表 `user_table_permission`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT AUTO_INCREMENT | 主键 |
| user_id | VARCHAR(64) NOT NULL | 用户标识 |
| table_name | VARCHAR(128) NOT NULL | 有权限的表名 |
| permission_type | VARCHAR(32) DEFAULT 'SELECT' | 权限类型，默认SELECT |
| created_at | DATETIME DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**索引**：
- PRIMARY KEY (id)
- UNIQUE INDEX idx_user_table (user_id, table_name)
- INDEX idx_user_id (user_id)

#### 2.1.2 对话历史表 `conversation_history`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT AUTO_INCREMENT | 主键 |
| session_id | VARCHAR(64) NOT NULL | 会话ID |
| user_id | VARCHAR(64) NOT NULL | 用户标识 |
| role | ENUM('user', 'assistant') NOT NULL | 角色 |
| content | TEXT NOT NULL | 内容 |
| sql_text | TEXT NULL | SQL语句(assistant时) |
| created_at | DATETIME DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**索引**：
- PRIMARY KEY (id)
- INDEX idx_session_user (session_id, user_id)
- INDEX idx_created_at (created_at)

### 2.2 SQLAlchemy 模型定义

```python
# app/models/database.py

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
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index('idx_session_user', 'session_id', 'user_id'),
        Index('idx_created_at', 'created_at'),
    )
```

---

## 3. 配置管理

### 3.1 环境变量 (.env)

```bash
# 阿里云 DashScope
DASHSCOPE_API_KEY=your_api_key_here

# 业务数据库连接 (数据中台原库)
BUSINESS_DB_HOST=localhost
BUSINESS_DB_PORT=3306
BUSINESS_DB_NAME=business_db
BUSINESS_DB_USER=root
BUSINESS_DB_PASSWORD=your_password

# 权限/历史库连接
AUTH_DB_HOST=localhost
AUTH_DB_PORT=3306
AUTH_DB_NAME=ai_robot
AUTH_DB_USER=root
AUTH_DB_PASSWORD=your_password

# Chroma 向量库路径
CHROMA_PERSIST_DIRECTORY=./data/chroma

# 应用配置
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
```

### 3.2 配置类

```python
# app/core/config.py

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # DashScope
    dashscope_api_key: str
    
    # 业务数据库
    business_db_host: str = "localhost"
    business_db_port: int = 3306
    business_db_name: str = "business_db"
    business_db_user: str = "root"
    business_db_password: str = ""
    
    # 权限/历史库
    auth_db_host: str = "localhost"
    auth_db_port: int = 3306
    auth_db_name: str = "ai_robot"
    auth_db_user: str = "root"
    auth_db_password: str = ""
    
    # Chroma
    chroma_persist_directory: str = "./data/chroma"
    
    # 应用
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    
    # 业务配置
    max_history_turns: int = 5
    max_sql_rows: int = 100
    sql_timeout: int = 10
    retrieval_top_k: int = 5
    
    @property
    def business_db_url(self) -> str:
        return f"mysql+pymysql://{self.business_db_user}:{self.business_db_password}@{self.business_db_host}:{self.business_db_port}/{self.business_db_name}"
    
    @property
    def auth_db_url(self) -> str:
        return f"mysql+pymysql://{self.auth_db_user}:{self.auth_db_password}@{self.auth_db_host}:{self.auth_db_port}/{self.auth_db_name}"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

## 4. API 接口定义

### 4.1 数据模型

#### 4.1.1 请求模型

```python
# app/models/request.py

from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="会话ID，用于多轮对话")
    user_id: str = Field(..., description="用户标识")
    question: str = Field(..., description="用户问题", min_length=1, max_length=1000)

class HistoryRequest(BaseModel):
    session_id: str
    user_id: str
    limit: int = Field(default=20, ge=1, le=100)
```

#### 4.1.2 响应模型

```python
# app/models/response.py

from pydantic import BaseModel
from typing import Optional
from enum import Enum

class ResponseType(str, Enum):
    QUERY = "query"
    CHAT = "chat"
    ERROR = "error"

class ChatResponse(BaseModel):
    session_id: str
    type: ResponseType
    content: str
    sql: Optional[str] = None

class HistoryMessage(BaseModel):
    role: str
    content: str
    sql: Optional[str] = None
    created_at: str

class HistoryResponse(BaseModel):
    session_id: str
    messages: list[HistoryMessage]
```

### 4.2 接口详情

#### 4.2.1 聊天接口

**请求**：
```http
POST /chat
Content-Type: application/json

{
    "session_id": "sess_123456",
    "user_id": "user_001",
    "question": "请帮我查一下2024年有哪些项目"
}
```

**响应**：
```json
{
    "session_id": "sess_123456",
    "type": "query",
    "content": "2024年共有15个项目，包括：\n1. XX项目\n2. YY项目...",
    "sql": "SELECT * FROM project WHERE year = 2024"
}
```

#### 4.2.2 历史查询接口

**请求**：
```http
GET /history?session_id=sess_123456&user_id=user_001&limit=20
```

**响应**：
```json
{
    "session_id": "sess_123456",
    "messages": [
        {
            "role": "user",
            "content": "请帮我查一下2024年有哪些项目",
            "sql": null,
            "created_at": "2024-01-15T10:30:00"
        },
        {
            "role": "assistant",
            "content": "2024年共有15个项目...",
            "sql": "SELECT * FROM project WHERE year = 2024",
            "created_at": "2024-01-15T10:30:05"
        }
    ]
}
```

---

## 5. 核心模块实现

### 5.1 意图识别模块

**功能**：区分用户问题是"数据查询"还是"闲聊"

**实现方案**：
- 使用 LangChain PromptTemplate 构建提示词
- 调用 LLM 判断意图，仅返回 `query` 或 `chat` 标签

**Prompt 模板**：
```
你是一个意图分类器。请判断用户的问题是数据查询还是闲聊。

规则：
- 如果用户询问数据库中的具体数据、信息、统计等，返回 "query"
- 如果用户只是打招呼、闲聊、问候等，返回 "chat"

用户问题：{question}

请只返回一个词：query 或 chat
```

**代码实现**：
```python
# app/services/intent_recognition.py

from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from langchain_qwq import ChatQwen
from app.core.config import get_settings

INTENT_PROMPT = PromptTemplate(
    template="""你是一个意图分类器。请判断用户的问题是数据查询还是闲聊。

规则：
- 如果用户询问数据库中的具体数据、信息、统计等，返回 "query"
- 如果用户只是打招呼、闲聊、问候等，返回 "chat"

用户问题：{question}

请只返回一个词：query 或 chat""",
    input_variables=["question"]
)

class IntentRecognition:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatQwen(
            model="qwen-max-latest",
            api_key=settings.dashscope_api_key
        )
    
    async def recognize(self, question: str) -> str:
        prompt = INTENT_PROMPT.format(question=question)
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        result = response.content.strip().lower()
        
        if "query" in result:
            return "query"
        return "chat"
```

### 5.2 查询改写模块

**功能**：将口语化问题改写为规范问题，结合历史上下文

**实现方案**：
- 从 MySQL 获取最近 N 轮对话历史
- 使用 LLM 结合历史上下文改写问题

**Prompt 模板**：
```
你是一个查询改写助手。请根据对话历史，将用户口语化的问题改写为完整、清晰的查询问题。

对话历史：
{history}

当前问题：{question}

请只输出改写后的问题，不要添加任何解释。
```

**代码实现**：
```python
# app/services/query_rewrite.py

from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from langchain_qwq import ChatQwen
from app.core.config import get_settings
from app.services.history import HistoryService

REWRITE_PROMPT = PromptTemplate(
    template="""你是一个查询改写助手。请根据对话历史，将用户口语化的问题改写为完整、清晰的查询问题。

对话历史：
{history}

当前问题：{question}

请只输出改写后的问题，不要添加任何解释。""",
    input_variables=["history", "question"]
)

class QueryRewrite:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatQwen(
            model="qwen-max-latest",
            api_key=settings.dashscope_api_key
        )
        self.history_service = HistoryService()
        self.max_turns = settings.max_history_turns
    
    async def rewrite(self, session_id: str, user_id: str, question: str) -> str:
        history = await self.history_service.get_recent_history(
            session_id, user_id, self.max_turns
        )
        
        if not history:
            return question
        
        history_text = "\n".join([
            f"用户：{h['content']}" if h['role'] == 'user' 
            else f"助手：{h['content']}"
            for h in history
        ])
        
        prompt = REWRITE_PROMPT.format(history=history_text, question=question)
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        
        return response.content.strip()
```

### 5.3 表结构向量检索模块

**功能**：从 Chroma 召回与问题相关的表结构

**实现方案**：
- 使用 `text-embedding-v3` 嵌入模型
- Chroma 向量数据库存储表结构描述

**索引构建**：
```python
# scripts/build_index.py

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma
from sqlalchemy import create_engine, inspect
from app.core.config import get_settings

def get_table_descriptions(engine) -> list[str]:
    inspector = inspect(engine)
    descriptions = []
    
    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        comment = inspector.get_table_comment(table_name)
        
        col_str = ", ".join([
            f"{col['name']}({col['type']}, {col.get('comment', '')})"
            for col in columns
        ])
        
        desc = f"表名：{table_name}，表注释：{comment.get('text', '')}，列：{col_str}"
        descriptions.append(desc)
    
    return descriptions

def build_index():
    settings = get_settings()
    engine = create_engine(settings.business_db_url)
    
    descriptions = get_table_descriptions(engine)
    
    embeddings = DashScopeEmbeddings(
        model="text-embedding-v3",
        dashscope_api_key=settings.dashscope_api_key
    )
    
    vectorstore = Chroma.from_texts(
        texts=descriptions,
        embedding=embeddings,
        persist_directory=settings.chroma_persist_directory
    )
    vectorstore.persist()
```

**检索服务**：
```python
# app/services/table_retrieval.py

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma
from app.core.config import get_settings

class TableRetrieval:
    def __init__(self):
        settings = get_settings()
        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v3",
            dashscope_api_key=settings.dashscope_api_key
        )
        self.vectorstore = Chroma(
            persist_directory=settings.chroma_persist_directory,
            embedding_function=self.embeddings
        )
        self.top_k = settings.retrieval_top_k
    
    async def retrieve(self, question: str) -> list[str]:
        docs = self.vectorstore.similarity_search(question, k=self.top_k)
        return [doc.page_content for doc in docs]
```

### 5.4 权限管理模块

**功能**：确保用户只能访问有权限的表

**实现方案**：
- 预检：从权限库获取用户有权限的表列表
- 细粒度校验：解析 SQL 中涉及的表，与权限列表比对

**代码实现**：
```python
# app/services/permission.py

import sqlparse
from sqlalchemy import create_engine, text
from app.core.config import get_settings
from app.models.database import UserTablePermission, Base
from sqlalchemy.orm import sessionmaker

class PermissionService:
    def __init__(self):
        settings = get_settings()
        self.engine = create_engine(settings.auth_db_url)
        self.Session = sessionmaker(bind=self.engine)
        self._cache = {}
    
    def get_user_tables(self, user_id: str) -> set[str]:
        if user_id in self._cache:
            return self._cache[user_id]
        
        session = self.Session()
        try:
            perms = session.query(UserTablePermission).filter(
                UserTablePermission.user_id == user_id
            ).all()
            tables = {p.table_name for p in perms}
            self._cache[user_id] = tables
            return tables
        finally:
            session.close()
    
    def check_permission(self, user_id: str, sql: str) -> tuple[bool, str]:
        user_tables = self.get_user_tables(user_id)
        
        parsed = sqlparse.parse(sql)
        sql_tables = set()
        
        for stmt in parsed:
            for token in stmt.tokens:
                if token.ttype is None and token.value.upper() in user_tables:
                    sql_tables.add(token.value.lower())
        
        unauthorized = sql_tables - user_tables
        if unauthorized:
            return False, f"无权限访问表: {', '.join(unauthorized)}"
        
        return True, ""
    
    def clear_cache(self, user_id: str = None):
        if user_id:
            self._cache.pop(user_id, None)
        else:
            self._cache.clear()
```

### 5.5 NL2SQL 模块

**功能**：根据表结构和用户问题生成 SQL

**实现方案**：
- 检索相关表结构描述
- 动态选择 Few-shot 示例
- 调用 LLM 生成 SQL

**Prompt 模板**：
```
你是一个SQL生成专家。请根据以下表结构和用户问题生成SQL查询语句。

表结构：
{table_descriptions}

用户问题：{question}

要求：
1. 只生成 SELECT 查询语句，不要生成 INSERT、UPDATE、DELETE
2. 只返回SQL语句，不要添加任何解释
3. 确保SQL语法正确
4. 如果需要限制结果数量，使用 LIMIT

SQL：
```

**代码实现**：
```python
# app/services/nl2sql.py

from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from langchain_qwq import ChatQwen
from app.core.config import get_settings
import re

NL2SQL_PROMPT = PromptTemplate(
    template="""你是一个SQL生成专家。请根据以下表结构和用户问题生成SQL查询语句。

表结构：
{table_descriptions}

用户问题：{question}

要求：
1. 只生成 SELECT 查询语句，不要生成 INSERT、UPDATE、DELETE
2. 只返回SQL语句，不要添加任何解释
3. 确保SQL语法正确
4. 如果需要限制结果数量，使用 LIMIT

SQL：""",
    input_variables=["table_descriptions", "question"]
)

class NL2SQLService:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatQwen(
            model="qwen-max-latest",
            api_key=settings.dashscope_api_key
        )
        self.max_rows = settings.max_sql_rows
    
    async def generate(self, table_descriptions: list[str], question: str) -> str:
        tables_text = "\n\n".join(table_descriptions)
        
        prompt = NL2SQL_PROMPT.format(
            table_descriptions=tables_text,
            question=question
        )
        
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        
        sql = self._extract_sql(response.content)
        
        if "LIMIT" not in sql.upper():
            sql = f"{sql.rstrip(';')} LIMIT {self.max_rows}"
        
        return sql
    
    def _extract_sql(self, text: str) -> str:
        sql_match = re.search(r'```sql\s*(.*?)\s*```', text, re.DOTALL)
        if sql_match:
            return sql_match.group(1).strip()
        
        lines = text.strip().split('\n')
        for i, line in enumerate(lines):
            if line.strip().upper().startswith('SELECT'):
                return '\n'.join(lines[i:]).strip()
        
        return text.strip()
```

### 5.6 SQL 执行模块

**功能**：执行生成的 SQL 并返回结果

**实现方案**：
- 使用 SQLAlchemy 连接业务数据库
- 设置只读事务和超时
- 结果转换为易读格式

**代码实现**：
```python
# app/services/sql_executor.py

from sqlalchemy import create_engine, text
from sqlalchemy.exc import TimeoutError as SQLTimeoutError
from app.core.config import get_settings

class SQLExecutor:
    def __init__(self):
        settings = get_settings()
        self.engine = create_engine(
            settings.business_db_url,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.timeout = settings.sql_timeout
        self.max_rows = settings.max_sql_rows
    
    async def execute(self, sql: str) -> tuple[bool, str, str]:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SET SESSION TRANSACTION READ ONLY"))
                
                result = conn.execute(text(sql))
                columns = result.keys()
                rows = result.fetchall()
                
                if not rows:
                    return True, "查询结果为空", sql
                
                formatted = self._format_result(columns, rows)
                return True, formatted, sql
                
        except SQLTimeoutError:
            return False, "SQL执行超时，请优化查询条件", sql
        except Exception as e:
            return False, f"SQL执行失败: {str(e)}", sql
    
    def _format_result(self, columns, rows) -> str:
        col_widths = {col: len(str(col)) for col in columns}
        
        for row in rows:
            for i, col in enumerate(columns):
                col_widths[col] = max(col_widths[col], len(str(row[i])))
        
        header = " | ".join(str(col).ljust(col_widths[col]) for col in columns)
        separator = "-+-".join("-" * col_widths[col] for col in columns)
        
        lines = [header, separator]
        for row in rows:
            line = " | ".join(str(row[i]).ljust(col_widths[columns[i]]) for i in range(len(columns)))
            lines.append(line)
        
        return "\n".join(lines)
```

### 5.7 历史记录模块

**功能**：存储和获取对话历史

**代码实现**：
```python
# app/services/history.py

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, desc
from app.core.config import get_settings
from app.models.database import ConversationHistory, Base
from datetime import datetime

class HistoryService:
    def __init__(self):
        settings = get_settings()
        self.engine = create_engine(settings.auth_db_url)
        self.Session = sessionmaker(bind=self.engine)
    
    def _ensure_tables(self):
        Base.metadata.create_all(self.engine)
    
    async def add_message(self, session_id: str, user_id: str, role: str, content: str, sql_text: str = None):
        self._ensure_tables()
        session = self.Session()
        try:
            msg = ConversationHistory(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                sql_text=sql_text
            )
            session.add(msg)
            session.commit()
        finally:
            session.close()
    
    async def get_recent_history(self, session_id: str, user_id: str, limit: int = 5) -> list[dict]:
        self._ensure_tables()
        session = self.Session()
        try:
            msgs = session.query(ConversationHistory).filter(
                ConversationHistory.session_id == session_id,
                ConversationHistory.user_id == user_id
            ).order_by(desc(ConversationHistory.created_at)).limit(limit).all()
            
            msgs = list(reversed(msgs))
            return [
                {
                    "role": m.role,
                    "content": m.content,
                    "sql": m.sql_text,
                    "created_at": m.created_at.isoformat()
                }
                for m in msgs
            ]
        finally:
            session.close()
```

---

## 6. 主流程编排

### 6.1 LangChain LCEL 编排

```python
# app/api/routes.py

from fastapi import APIRouter, HTTPException
from app.models.request import ChatRequest
from app.models.response import ChatResponse, ResponseType
from app.services.intent_recognition import IntentRecognition
from app.services.query_rewrite import QueryRewrite
from app.services.table_retrieval import TableRetrieval
from app.services.permission import PermissionService
from app.services.nl2sql import NL2SQLService
from app.services.sql_executor import SQLExecutor
from app.services.history import HistoryService

router = APIRouter()

intent_recognition = IntentRecognition()
query_rewrite = QueryRewrite()
table_retrieval = TableRetrieval()
permission_service = PermissionService()
nl2sql_service = NL2SQLService()
sql_executor = SQLExecutor()
history_service = HistoryService()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # 1. 意图识别
    intent = await intent_recognition.recognize(request.question)
    
    if intent == "chat":
        await history_service.add_message(
            request.session_id, request.user_id, "user", request.question
        )
        response = ChatResponse(
            session_id=request.session_id,
            type=ResponseType.CHAT,
            content="您好！我是AI问答助手，可以帮您查询数据库中的数据。请告诉我您想查询什么信息？"
        )
        await history_service.add_message(
            request.session_id, request.user_id, "assistant", response.content
        )
        return response
    
    # 2. 查询改写
    rewritten_question = await query_rewrite.rewrite(
        request.session_id, request.user_id, request.question
    )
    
    # 3. 表结构检索
    table_descriptions = await table_retrieval.retrieve(rewritten_question)
    
    # 4. NL2SQL 生成
    sql = await nl2sql_service.generate(table_descriptions, rewritten_question)
    
    # 5. 权限校验
    has_permission, error_msg = permission_service.check_permission(request.user_id, sql)
    if not has_permission:
        await history_service.add_message(
            request.session_id, request.user_id, "user", request.question
        )
        await history_service.add_message(
            request.session_id, request.user_id, "assistant", error_msg, sql
        )
        return ChatResponse(
            session_id=request.session_id,
            type=ResponseType.ERROR,
            content=error_msg,
            sql=sql
        )
    
    # 6. SQL 执行
    success, result, executed_sql = await sql_executor.execute(sql)
    
    # 7. 记录历史
    await history_service.add_message(
        request.session_id, request.user_id, "user", request.question
    )
    await history_service.add_message(
        request.session_id, request.user_id, "assistant", result, executed_sql
    )
    
    return ChatResponse(
        session_id=request.session_id,
        type=ResponseType.QUERY,
        content=result,
        sql=executed_sql
    )
```

### 6.2 FastAPI 主入口

```python
# app/main.py

from fastapi import FastAPI
from app.api.routes import router
from app.core.config import get_settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="煤炭设计院数据中台AI问答机器人",
    description="自然语言转SQL查询系统",
    version="1.0.0"
)

app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    logger.info("AI问答机器人服务启动")

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(app, host=settings.app_host, port=settings.app_port)
```

---

## 7. 依赖管理

```txt
# requirements.txt

fastapi>=0.109.0
uvicorn>=0.27.0
langchain>=0.3.0
langchain-qwq>=0.1.0
langchain-community>=0.3.0
sqlalchemy>=2.0.0
pymysql>=1.1.0
chromadb>=0.5.0
sqlparse>=0.5.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
```

---

## 8. 初始化脚本

### 8.1 创建数据库和表

```python
# scripts/init_db.py

from sqlalchemy import create_engine
from app.core.config import get_settings
from app.models.database import Base

def init_database():
    settings = get_settings()
    
    engine = create_engine(settings.auth_db_url.replace('/ai_robot', ''))
    
    with engine.connect() as conn:
        conn.execute(f"CREATE DATABASE IF NOT EXISTS {settings.auth_db_name}")
        conn.commit()
    
    auth_engine = create_engine(settings.auth_db_url)
    Base.metadata.create_all(auth_engine)
    
    print(f"数据库 {settings.auth_db_name} 初始化完成")

if __name__ == "__main__":
    init_database()
```

---

## 9. 启动说明

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量**：
   复制 `.env.example` 为 `.env`，填写配置

3. **初始化数据库**：
   ```bash
   python scripts/init_db.py
   ```

4. **构建向量索引**：
   ```bash
   python scripts/build_index.py
   ```

5. **启动服务**：
   ```bash
   uvicorn app.main:app --reload
   ```

6. **测试接口**：
   ```bash
   curl -X POST http://localhost:8000/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"session_id":"test","user_id":"user001","question":"查询2024年的项目"}'
   ```
