"""
用户认证路由
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import RegisterRequest, LoginRequest, UserResponse
from utils import hash_password, get_user_by_token

router = APIRouter()


@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """注册"""
    # 检查用户名是否存在
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 创建用户
    user = User(
        username=request.username,
        password_hash=hash_password(request.password),
        card_gold=0,
        free_draws=10  # 新用户10次免费抽卡
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 生成token（简化版）
    token = f"token_{user.id}_{uuid.uuid4().hex[:8]}"

    return {
        "success": True,
        "token": token,
        "user": UserResponse.model_validate(user)
    }


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """登录"""
    user = db.query(User).filter(User.username == request.username).first()
    if not user or user.password_hash != hash_password(request.password):
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    token = f"token_{user.id}_{uuid.uuid4().hex[:8]}"

    return {
        "success": True,
        "token": token,
        "user": UserResponse.model_validate(user)
    }


@router.get("/user")
def get_user_info(token: str, db: Session = Depends(get_db)):
    """获取用户信息"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    return UserResponse.model_validate(user)
