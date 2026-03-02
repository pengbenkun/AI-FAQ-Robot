from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    dashscope_api_key: str = ""
    
    # 大模型配置
    model_intent: str = "qwen-turbo"        # 意图识别模型（便宜）
    model_query_rewrite: str = "qwen2.5-32b-instruct" # 查询改写模型（便宜）
    model_nl2sql: str = "qwen-max-latest"   # NL2SQL 模型（推荐保持最强）
    model_summary: str = "qwen-turbo"        # 结果总结模型（便宜）
    
    business_db_host: str = "localhost"
    business_db_port: int = 3306
    business_db_name: str = "business_db"
    business_db_user: str = "root"
    business_db_password: str = ""
    
    auth_db_host: str = "localhost"
    auth_db_port: int = 3306
    auth_db_name: str = "ai_robot"
    auth_db_user: str = "root"
    auth_db_password: str = ""
    
    chroma_persist_directory: str = "./data/chroma"
    
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    
    max_history_turns: int = 10
    max_sql_rows: int = 100
    sql_timeout: int = 10
    retrieval_top_k: int = 5
    
    @property
    def business_db_url(self) -> str:
        password = self.business_db_password
        if '@' in password or '/' in password:
            from urllib.parse import quote_plus
            password = quote_plus(password)
        return f"mysql+pymysql://{self.business_db_user}:{password}@{self.business_db_host}:{self.business_db_port}/{self.business_db_name}"
    
    @property
    def auth_db_url(self) -> str:
        password = self.auth_db_password
        if '@' in password or '/' in password:
            from urllib.parse import quote_plus
            password = quote_plus(password)
        return f"mysql+pymysql://{self.auth_db_user}:{password}@{self.auth_db_host}:{self.auth_db_port}/{self.auth_db_name}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
