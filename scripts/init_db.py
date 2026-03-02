import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from app.models.database import Base, UserTablePermission
from app.core.config import get_settings


def init_database():
    settings = get_settings()
    
    print("正在连接 MySQL 服务器...")
    
    password = settings.auth_db_password
    if '@' in password or '/' in password:
        from urllib.parse import quote_plus
        password = quote_plus(password)
    
    base_url = f"mysql+pymysql://{settings.auth_db_user}:{password}@{settings.auth_db_host}:{settings.auth_db_port}"
    engine = create_engine(base_url, pool_pre_ping=True)
    
    try:
        with engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{settings.auth_db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            conn.commit()
            print(f"数据库 {settings.auth_db_name} 创建成功")
    except SQLAlchemyError as e:
        print(f"创建数据库时出错: {e}")
        print("尝试直接连接已有数据库...")
    
    print("正在创建表结构...")
    auth_engine = create_engine(settings.auth_db_url, pool_pre_ping=True)
    Base.metadata.create_all(auth_engine)
    print("表结构创建成功")
    
    print("正在检查初始权限数据...")
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=auth_engine)
    session = Session()
    
    try:
        existing = session.query(UserTablePermission).filter_by(user_id="test_user").first()
        if not existing:
            print("正在插入测试用户权限数据...")
            test_permissions = [
                UserTablePermission(user_id="test_user", table_name="project", permission_type="SELECT"),
                UserTablePermission(user_id="test_user", table_name="employee", permission_type="SELECT"),
                UserTablePermission(user_id="test_user", table_name="department", permission_type="SELECT"),
            ]
            session.add_all(test_permissions)
            session.commit()
            print("测试用户权限数据插入成功")
        else:
            print("权限数据已存在，跳过插入")
    finally:
        session.close()
    
    print("\n数据库初始化完成！")
    print(f"数据库地址: {settings.auth_db_host}:{settings.auth_db_port}/{settings.auth_db_name}")
    print("测试用户: test_user")
    print("请在 .env 文件中配置正确的数据库连接信息")


if __name__ == "__main__":
    init_database()
