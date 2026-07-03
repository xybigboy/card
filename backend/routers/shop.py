"""
商店路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from utils import get_user_by_token
from game_logic import DRAW_COST

router = APIRouter()


@router.get("/shop/info")
def get_shop_info():
    """获取商店信息"""
    return {
        "success": True,
        "draw_cost": DRAW_COST,
        "items": [
            {
                "id": "draw_1",
                "name": "单抽",
                "description": "抽取1张卡片",
                "cost": DRAW_COST,
                "type": "draw",
                "count": 1
            },
            {
                "id": "draw_10",
                "name": "十连抽",
                "description": "抽取10张卡片",
                "cost": DRAW_COST * 10,
                "type": "draw",
                "count": 10
            }
        ]
    }


@router.post("/shop/buy-draws")
def buy_draws(token: str, count: int = 1, db: Session = Depends(get_db)):
    """购买抽卡次数（花费卡金换取免费抽卡次数）"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    if count < 1 or count > 100:
        raise HTTPException(status_code=400, detail="购买数量必须在1-100之间")

    cost = count * DRAW_COST
    if user.card_gold < cost:
        raise HTTPException(status_code=400, detail="卡金不足")

    user.card_gold -= cost
    user.free_draws += count
    db.commit()

    return {
        "success": True,
        "message": f"成功购买 {count} 次抽卡",
        "cost": cost,
        "free_draws": user.free_draws,
        "card_gold": user.card_gold
    }
