import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine, text
from app.core.config import get_settings
from app.models.database import UserTablePermission
from sqlalchemy.orm import sessionmaker

settings = get_settings()
engine = create_engine(settings.auth_db_url)
Session = sessionmaker(bind=engine)
session = Session()

perms = session.query(UserTablePermission).all()
print("权限表数据:")
for p in perms:
    print(f"  user_id: {p.user_id}, table_name: {p.table_name}, permission_type: {p.permission_type}")

session.close()
