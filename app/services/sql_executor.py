"""
SQL 执行模块
功能：执行生成的 SQL 并格式化结果
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import TimeoutError as SQLTimeoutError, OperationalError
from app.core.config import get_settings


class SQLExecutor:
    """
    SQL 执行服务类
    
    负责：
    1. 连接业务数据库
    2. 以只读模式执行 SQL
    3. 格式化查询结果
    """
    
    def __init__(self):
        """初始化方法，创建数据库连接"""
        settings = get_settings()
        
        # 创建业务数据库连接引擎
        self.engine = create_engine(
            settings.business_db_url,
            pool_pre_ping=True,    # 每次使用前检查连接
            pool_recycle=3600,    # 连接1小时后回收
            connect_args={"connect_timeout": settings.sql_timeout}  # 连接超时时间
        )
        
        self.timeout = settings.sql_timeout
        self.max_rows = settings.max_sql_rows
    
    async def execute(self, sql: str) -> tuple[bool, str, str]:
        """
        执行 SQL 语句
        
        参数:
            sql: 要执行的 SQL 语句
            
        返回:
            tuple[bool, str, str]:
                - 第一个元素：是否成功
                - 第二个元素：结果或错误信息
                - 第三个元素：实际执行的 SQL
        """
        try:
            # 1. 获取数据库连接
            with self.engine.connect() as conn:
                # 2. 设置为只读事务，防止误修改数据
                conn.execute(text("SET SESSION TRANSACTION READ ONLY"))
                conn.commit()
                
                # 3. 执行 SQL
                result = conn.execute(text(sql))
                
                # 4. 获取列名和结果
                columns = list(result.keys())
                rows = result.fetchall()
                
                # 5. 如果没有结果，返回提示信息
                if not rows:
                    return True, "查询结果为空", sql
                
                # 6. 格式化结果为表格字符串
                formatted = self._format_result(columns, rows)
                return True, formatted, sql
                
        # 处理连接超时
        except OperationalError as e:
            if "timeout" in str(e).lower() or "timeout" in str(e.orig).lower():
                return False, "SQL执行超时，请优化查询条件", sql
            return False, f"SQL执行失败: {str(e)}", sql
        except SQLTimeoutError:
            return False, "SQL执行超时，请优化查询条件", sql
        except Exception as e:
            return False, f"SQL执行失败: {str(e)}", sql
    
    def _format_result(self, columns: list, rows: list) -> str:
        """
        将查询结果格式化为易读的表格字符串
        
        参数:
            columns: 列名列表
            rows: 结果行列表
            
        返回:
            str: 格式化的表格字符串
        """
        # 1. 计算每列的最大宽度
        col_widths = {col: len(str(col)) for col in columns}
        
        for row in rows:
            for i, col in enumerate(columns):
                # 安全地获取值
                try:
                    val = row[i]
                except (TypeError, IndexError):
                    try:
                        val = row._mapping[col]
                    except (AttributeError, KeyError):
                        val = str(row)
                col_widths[col] = max(col_widths[col], len(str(val)))
        
        # 2. 构建表头
        header = " | ".join(str(col).ljust(col_widths[col]) for col in columns)
        separator = "-+-".join("-" * col_widths[col] for col in columns)
        
        # 3. 构建数据行
        lines = [header, separator]
        for row in rows:
            row_data = []
            for i, col in enumerate(columns):
                try:
                    val = row[i]
                except (TypeError, IndexError):
                    try:
                        val = row._mapping[col]
                    except (AttributeError, KeyError):
                        val = str(row)
                row_data.append(str(val).ljust(col_widths[col]))
            lines.append(" | ".join(row_data))
        
        return "\n".join(lines)
