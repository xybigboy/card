"""
仓库/卡片管理路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import UserCard, CardTemplate
from schemas import CardResponse, ConsumeCardsRequest, BulkSellRequest
from utils import get_user_by_token, card_to_response
from game_logic import upgrade_card, get_upgrade_cost, get_card_sell_value

router = APIRouter()


@router.get("/cards")
def get_user_cards(token: str, db: Session = Depends(get_db)):
    """获取用户所有卡片"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    cards = db.query(UserCard).filter(UserCard.user_id == user.id).order_by(
        UserCard.stars.desc(), UserCard.level.desc()
    ).all()

    return {
        "success": True,
        "cards": [card_to_response(card) for card in cards]
    }


@router.post("/cards/{card_id}/set-battle")
def set_battle_card(card_id: int, token: str, db: Session = Depends(get_db)):
    """设置出战卡片"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    card = db.query(UserCard).filter(
        UserCard.id == card_id, UserCard.user_id == user.id
    ).first()

    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")

    # 取消其他卡片的出战状态
    db.query(UserCard).filter(UserCard.user_id == user.id).update(
        {UserCard.is_on_battle: False}
    )

    # 设置当前卡片出战
    card.is_on_battle = True
    db.commit()

    return {
        "success": True,
        "message": "出战卡片已设置"
    }


@router.get("/cards/collection")
def get_collection(token: str, db: Session = Depends(get_db)):
    """获取图鉴收集进度"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    # Get all templates
    all_templates = db.query(CardTemplate).all()

    # Get user's owned template_ids
    owned_cards = db.query(
        UserCard.template_id,
        func.count(UserCard.id).label('count')
    ).filter(
        UserCard.user_id == user.id
    ).group_by(UserCard.template_id).all()

    owned_map = {tid: cnt for tid, cnt in owned_cards}

    collection = []
    for t in all_templates:
        collection.append({
            "template_id": t.id,
            "name": t.name,
            "rarity": t.rarity,
            "base_stars": t.base_stars,
            "base_attack": t.base_attack,
            "base_defense": t.base_defense,
            "base_hp": t.base_hp,
            "speed": t.speed,
            "skill_name": t.skill_name,
            "skill_desc": t.skill_desc,
            "skills_json": getattr(t, 'skills_json', None),
            "category": t.category,
            "image": t.image,
            "owned": t.id in owned_map,
            "owned_count": owned_map.get(t.id, 0)
        })

    total = len(collection)
    owned_total = sum(1 for c in collection if c["owned"])

    return {
        "success": True,
        "collection": collection,
        "total": total,
        "owned": owned_total,
        "completion": round(owned_total / total * 100, 1) if total > 0 else 0
    }


@router.post("/cards/{card_id}/sell")
def sell_card(card_id: int, token: str, db: Session = Depends(get_db)):
    """兑换卡片为卡金"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    card = db.query(UserCard).filter(
        UserCard.id == card_id, UserCard.user_id == user.id
    ).first()

    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")

    if card.is_on_battle:
        raise HTTPException(status_code=400, detail="出战中的卡片不能兑换")

    # 计算价值
    sell_value = get_card_sell_value(card)

    # 增加卡金
    user.card_gold += sell_value

    # 删除卡片
    db.delete(card)
    db.commit()

    return {
        "success": True,
        "gold_earned": sell_value,
        "current_gold": user.card_gold
    }


@router.post("/cards/bulk-sell")
def bulk_sell_cards(body: BulkSellRequest, token: str, db: Session = Depends(get_db)):
    """按稀有度批量出售卡片"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    valid_rarities = ['普通', '高级', '史诗', '典藏']
    if body.rarity not in valid_rarities:
        raise HTTPException(status_code=400, detail="无效的稀有度")

    # Find cards to sell
    query = db.query(UserCard).join(CardTemplate).filter(
        UserCard.user_id == user.id,
        CardTemplate.rarity == body.rarity
    )
    if body.exclude_on_battle:
        query = query.filter(UserCard.is_on_battle == False)

    cards_to_sell = query.all()

    if not cards_to_sell:
        raise HTTPException(status_code=400, detail="没有可出售的卡片")

    # Calculate total value
    total_gold = 0
    rarity_values = {'普通': 20, '高级': 50, '史诗': 150, '典藏': 500}
    base = rarity_values.get(body.rarity, 20)

    for card in cards_to_sell:
        star_bonus = (card.stars - 1) * 20
        level_bonus = (card.level - 1) * 10
        total_gold += base + star_bonus + level_bonus
        db.delete(card)

    user.card_gold += total_gold
    db.commit()

    return {
        "success": True,
        "sold_count": len(cards_to_sell),
        "gold_earned": total_gold,
        "current_gold": user.card_gold
    }


@router.post("/cards/{card_id}/upgrade")
def upgrade_card_api(card_id: int, token: str, db: Session = Depends(get_db)):
    """升级卡片"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    card = db.query(UserCard).filter(
        UserCard.id == card_id, UserCard.user_id == user.id
    ).first()

    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")

    # 计算升级费用
    cost = get_upgrade_cost(card.level)

    if user.card_gold < cost:
        raise HTTPException(status_code=400, detail="卡金不足")

    # 扣除卡金
    user.card_gold -= cost

    # 升级卡片
    upgrade_card(card)
    db.commit()
    db.refresh(card)

    return {
        "success": True,
        "cost": cost,
        "card": card_to_response(card)
    }


@router.post("/cards/{card_id}/consume")
def consume_cards_api(card_id: int, body: ConsumeCardsRequest, token: str, db: Session = Depends(get_db)):
    """融合重复卡片获取属性加成"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    # 查找目标卡片
    target = db.query(UserCard).filter(
        UserCard.id == card_id, UserCard.user_id == user.id
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="目标卡片不存在")

    # 查找材料卡片
    materials = db.query(UserCard).filter(
        UserCard.id.in_(body.material_card_ids),
        UserCard.user_id == user.id,
        UserCard.template_id == target.template_id,
        UserCard.id != card_id
    ).all()

    if len(materials) != len(body.material_card_ids):
        raise HTTPException(status_code=400, detail="部分材料卡片无效（必须为同名卡片）")

    # 检查材料卡片是否出战中
    for mat in materials:
        if mat.is_on_battle:
            raise HTTPException(status_code=400, detail="出战中的卡片不能作为材料")

    # 计算属性加成: 普通=5%, 高级=10%, 史诗=20%, 典藏=40%, 每级额外+2%
    rarity_bonus = {'普通': 5, '高级': 10, '史诗': 20, '典藏': 40}
    total_bonus = 0
    for mat in materials:
        base = rarity_bonus.get(mat.template.rarity, 5)
        level_extra = (mat.level - 1) * 2
        total_bonus += base + level_extra

    # 应用属性加成 (百分比提升所有属性，含速度)
    multiplier = 1 + total_bonus / 100
    target.attack *= multiplier
    target.defense *= multiplier
    target.hp *= multiplier
    if hasattr(target, 'speed') and target.speed:
        target.speed *= multiplier

    # 删除材料卡片
    for mat in materials:
        db.delete(mat)

    db.commit()
    db.refresh(target)

    return {
        "success": True,
        "bonus_percent": total_bonus,
        "card": card_to_response(target)
    }
