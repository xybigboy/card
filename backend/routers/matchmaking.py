"""
匹配队列路由 + 大乱斗统计
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from utils import get_user_by_token
from ws.pvp import match_manager

router = APIRouter()


@router.get("/matchmaking/queue-size")
def get_queue_size(token: str, db: Session = Depends(get_db)):
    """获取当前匹配队列等待人数"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")
    return {"queue_size": match_manager.get_queue_size()}


@router.get("/brawl/stats")
def get_brawl_stats(token: str, db: Session = Depends(get_db)):
    """获取大乱斗历史统计"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")
    return {
        "success": True,
        "stats": {
            "wins": user.wins,
            "losses": user.losses,
            "rating": user.rating,
            "card_gold": user.card_gold,
        }
    }
