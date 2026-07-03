"""
排行榜路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User

router = APIRouter()


@router.get("/ranking")
def get_ranking(limit: int = 20, db: Session = Depends(get_db)):
    """获取排行榜"""
    users = db.query(User).order_by(User.rating.desc()).limit(limit).all()

    return {
        "success": True,
        "ranking": [
            {
                "rank": i + 1,
                "username": user.username,
                "rating": user.rating,
                "wins": user.wins,
                "losses": user.losses
            }
            for i, user in enumerate(users)
        ]
    }
