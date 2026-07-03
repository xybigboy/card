"""
抽卡路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import UserCard
from utils import get_user_by_token, card_to_response
from game_logic import draw_multiple, DRAW_COST

router = APIRouter()


@router.post("/draw")
def draw_card_api(token: str, count: int = 1, db: Session = Depends(get_db)):
    """抽卡"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    # 计算消耗
    free_used = min(count, user.free_draws)
    paid_count = count - free_used
    cost = paid_count * DRAW_COST

    if user.card_gold < cost:
        raise HTTPException(status_code=400, detail="卡金不足")

    # 扣除免费次数和卡金
    user.free_draws -= free_used
    user.card_gold -= cost

    # 抽卡
    cards = draw_multiple(db, count)

    # 保存卡片
    for card in cards:
        card.user_id = user.id
        db.add(card)

    db.commit()

    # 刷新卡片信息
    for card in cards:
        db.refresh(card)

    return {
        "success": True,
        "free_used": free_used,
        "cost": cost,
        "cards": [card_to_response(card) for card in cards]
    }
