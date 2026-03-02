"""
权限管理模块
功能：检查用户是否有权限访问 SQL 中涉及的表
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入正则表达式，用于解析 SQL 中的表名
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models.database import UserTablePermission


class PermissionService:
    """
    权限管理服务类
    
    职责：
    1. 从数据库获取用户的表权限列表
    2. 解析 SQL 语句中涉及的表名
    3. 检查用户是否有权限访问这些表
    """
    
    def __init__(self):
        """初始化方法，创建数据库连接"""
        settings = get_settings()
        # 创建数据库连接引擎
        self.engine = create_engine(
            settings.auth_db_url, 
            pool_pre_ping=True,    # 每次使用前检查连接是否有效
            pool_recycle=3600      # 连接1小时后回收
        )
        self.Session = sessionmaker(bind=self.engine)
        
        # 权限缓存，避免频繁查询数据库
        self._cache = {}
    
    def get_user_tables(self, user_id: str) -> set[str]:
        """
        获取用户有权限的表列表
        
        参数:
            user_id: 用户ID
            
        返回:
            set[str]: 用户有权限的表名集合（小写）
        """
        # 如果缓存中有，直接返回
        if user_id in self._cache:
            return self._cache[user_id]
        
        # 从数据库查询用户的权限
        session = self.Session()
        try:
            perms = session.query(UserTablePermission).filter(
                UserTablePermission.user_id == user_id
            ).all()
            
            # 提取表名，转换为小写
            tables = {p.table_name.lower() for p in perms}
            
            # 存入缓存
            self._cache[user_id] = tables
            return tables
        finally:
            session.close()
    
    def extract_tables_from_sql(self, sql: str) -> set[str]:
        """
        从 SQL 语句中提取涉及的表名
        
        使用正则表达式匹配 FROM、JOIN 等关键词后面的表名
        
        参数:
            sql: SQL 语句
            
        返回:
            set[str]: 涉及的表名集合（小写）
        """
        tables = set()
        
        # 正则表达式匹配表名
        # 匹配 FROM table_name 或 JOIN table_name 等模式
        pattern = r'\b(?:FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        
        for match in matches:
            # 处理 table.column 或 schema.table 的情况，只取表名
            table_name = match.split('.')[-1].strip('`"[]')
            tables.add(table_name.lower())
        
        return tables
    
    def check_permission(self, user_id: str, sql: str) -> tuple[bool, str]:
        """
        检查用户是否有权限执行该 SQL
        
        参数:
            user_id: 用户ID
            sql: SQL 语句
            
        返回:
            tuple[bool, str]: 
                - 第一个元素：是否有权限 (True/False)
                - 第二个元素：错误信息（如果有）
        """
        # 1. 获取用户有权限的表
        user_tables = self.get_user_tables(user_id)
        
        # 2. 如果用户没有任何权限，直接拒绝
        if not user_tables:
            return False, f"用户 {user_id} 没有配置任何表权限，请联系管理员"
        
        # 3. 提取 SQL 中涉及的表
        sql_tables = self.extract_tables_from_sql(sql)
        
        # 4. 如果没有提取到表名，直接通过
        if not sql_tables:
            return True, ""
        
        # 5. 检查是否有未授权的表
        unauthorized = sql_tables - user_tables
        if unauthorized:
            return False, f"无权限访问表: {', '.join(unauthorized)}"
        
        return True, ""
    
    def clear_cache(self, user_id: str = None):
        """
        清除权限缓存
        
        参数:
            user_id: 如果指定，则只清除该用户的缓存；否则清除所有缓存
        """
        if user_id:
            self._cache.pop(user_id, None)
        else:
            self._cache.clear()
