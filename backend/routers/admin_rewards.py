"""
管理员 - 发放奖励路由
支持全服/指定玩家发放卡金和卡片
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserCard, CardTemplate
from schemas import RewardRequest
from utils import verify_admin_token
from game_logic import get_random_stars

router = APIRouter()


@router.get("/admin/users")
def list_users(token: str, db: Session = Depends(get_db)):
    """获取所有用户列表（管理员用）"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")

    users = db.query(User).order_by(User.id).all()
    return {
        "success": True,
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "card_gold": u.card_gold,
                "free_draws": u.free_draws,
                "rating": u.rating,
                "wins": u.wins,
                "losses": u.losses,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
    }


@router.post("/admin/send-reward")
def send_reward(token: str, body: RewardRequest, db: Session = Depends(get_db)):
    """发放奖励：卡金 + 卡片"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")

    # 确定目标用户
    if body.target_type == "all":
        users = db.query(User).all()
    elif body.target_type == "user":
        if not body.username:
            raise HTTPException(status_code=400, detail="指定玩家时必须提供用户名")
        user = db.query(User).filter(User.username == body.username).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"用户「{body.username}」不存在")
        users = [user]
    else:
        raise HTTPException(status_code=400, detail="target_type 必须为 all 或 user")

    if not users:
        raise HTTPException(status_code=400, detail="没有目标用户")

    # 发放卡金
    gold_given = 0
    if body.card_gold > 0:
        for u in users:
            u.card_gold += body.card_gold
        gold_given = body.card_gold

    # 发放卡片
    cards_given = 0
    template = None
    if body.template_id:
        template = db.query(CardTemplate).filter(CardTemplate.id == body.template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="卡片模板不存在")

        for u in users:
            for _ in range(body.card_count):
                stars = get_random_stars(template.base_stars)
                star_multiplier = 1 + (stars - 1) * 0.12
                user_card = UserCard(
                    user_id=u.id,
                    template_id=template.id,
                    stars=stars,
                    level=1,
                    attack=round(template.base_attack * star_multiplier, 1),
                    defense=round(template.base_defense * star_multiplier, 1),
                    hp=round(template.base_hp * star_multiplier, 1),
                    speed=round(template.speed * star_multiplier, 1),
                    is_on_battle=False,
                )
                db.add(user_card)
                cards_given += 1

    db.commit()

    return {
        "success": True,
        "message": (
            f"成功向 {'全服' if body.target_type == 'all' else body.username} "
            f"的 {len(users)} 名玩家发放"
            + (f" {gold_given} 卡金" if gold_given else "")
            + (f" {cards_given} 张「{template.name}」" if cards_given else "")
        ),
        "target_count": len(users),
        "gold_given": gold_given,
        "cards_given": cards_given,
        "card_name": template.name if template else None,
    }
