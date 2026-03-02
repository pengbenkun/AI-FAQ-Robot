"""
权限管理 API
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models.database import UserTablePermission
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class PermissionAddRequest(BaseModel):
    user_id: str
    table_name: str
    permission_type: str = "SELECT"


@router.get("/permissions")
async def list_permissions():
    """获取权限列表"""
    settings = get_settings()
    engine = create_engine(settings.auth_db_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        perms = session.query(UserTablePermission).all()
        return {
            "success": True,
            "data": [
                {
                    "id": p.id,
                    "user_id": p.user_id,
                    "table_name": p.table_name,
                    "permission_type": p.permission_type,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "updated_at": p.updated_at.isoformat() if p.updated_at else None
                }
                for p in perms
            ]
        }
    except Exception as e:
        logger.error(f"Error listing permissions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.get("/permissions/tables")
async def get_table_names():
    """获取业务数据库的表名列表"""
    settings = get_settings()
    engine = create_engine(settings.business_db_url, pool_pre_ping=True)
    
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        return {
            "success": True,
            "data": table_names
        }
    except Exception as e:
        logger.error(f"Error getting table names: {str(e)}")
        return {
            "success": True,
            "data": []
        }


@router.post("/permissions")
async def add_permission(request: PermissionAddRequest):
    """新增权限"""
    settings = get_settings()
    engine = create_engine(settings.auth_db_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        existing = session.query(UserTablePermission).filter(
            UserTablePermission.user_id == request.user_id,
            UserTablePermission.table_name == request.table_name
        ).first()
        
        if existing:
            return {
                "success": False,
                "message": "记录已存在，不能重复添加"
            }
        
        new_perm = UserTablePermission(
            user_id=request.user_id,
            table_name=request.table_name,
            permission_type=request.permission_type
        )
        session.add(new_perm)
        session.commit()
        
        return {
            "success": True,
            "message": "添加成功",
            "data": {
                "id": new_perm.id,
                "user_id": new_perm.user_id,
                "table_name": new_perm.table_name,
                "permission_type": new_perm.permission_type
            }
        }
    except Exception as e:
        logger.error(f"Error adding permission: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.delete("/permissions/{perm_id}")
async def delete_permission(perm_id: int):
    """删除权限"""
    settings = get_settings()
    engine = create_engine(settings.auth_db_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        perm = session.query(UserTablePermission).filter(
            UserTablePermission.id == perm_id
        ).first()
        
        if not perm:
            return {
                "success": False,
                "message": "记录不存在"
            }
        
        session.delete(perm)
        session.commit()
        
        return {
            "success": True,
            "message": "删除成功"
        }
    except Exception as e:
        logger.error(f"Error deleting permission: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
