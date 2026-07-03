"""
管理员认证路由
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import AdminUser
from schemas import AdminLoginRequest, AdminChangePasswordRequest
from utils import hash_password, verify_admin_token

router = APIRouter()


@router.post("/admin/login")
def admin_login(request: AdminLoginRequest, db: Session = Depends(get_db)):
    """管理员登录（数据库验证）"""
    admin = db.query(AdminUser).filter(
        AdminUser.username == request.username
    ).first()

    if not admin or admin.password_hash != hash_password(request.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = f"admin_{uuid.uuid4().hex}"
    admin.token = token
    db.commit()

    return {
        "success": True,
        "token": token,
        "username": admin.username
    }


@router.post("/admin/logout")
def admin_logout(token: str, db: Session = Depends(get_db)):
    """管理员登出"""
    admin = verify_admin_token(token, db)
    if admin:
        admin.token = None
        db.commit()
    return {"success": True}


@router.get("/admin/profile")
def admin_profile(token: str, db: Session = Depends(get_db)):
    """获取管理员资料"""
    admin = verify_admin_token(token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="无效的管理员token")

    return {
        "success": True,
        "profile": {
            "id": admin.id,
            "username": admin.username,
            "created_at": admin.created_at.isoformat() if admin.created_at else None
        }
    }


@router.post("/admin/change-password")
def admin_change_password(token: str, request: AdminChangePasswordRequest, db: Session = Depends(get_db)):
    """修改管理员密码"""
    admin = verify_admin_token(token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="无效的管理员token")

    if admin.password_hash != hash_password(request.old_password):
        raise HTTPException(status_code=400, detail="旧密码错误")

    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度不能少于6位")

    admin.password_hash = hash_password(request.new_password)
    db.commit()

    return {
        "success": True,
        "message": "密码修改成功"
    }
