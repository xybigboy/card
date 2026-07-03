"""
战斗记录路由
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserCard, BattleRecord
from utils import get_user_by_token, card_to_response

router = APIRouter()


@router.get("/battle-card")
def get_battle_card(token: str, db: Session = Depends(get_db)):
    """获取当前出战卡片"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    card = db.query(UserCard).filter(
        UserCard.user_id == user.id, UserCard.is_on_battle == True
    ).first()

    if not card:
        return {"success": True, "card": None}

    return {
        "success": True,
        "card": card_to_response(card)
    }


@router.get("/battle/history")
def get_battle_history(token: str, limit: int = 20, db: Session = Depends(get_db)):
    """获取战斗记录"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    records = db.query(BattleRecord).filter(
        (BattleRecord.player1_id == user.id) | (BattleRecord.player2_id == user.id)
    ).order_by(BattleRecord.created_at.desc()).limit(limit).all()

    result = []
    for record in records:
        is_winner = record.winner_id == user.id
        opponent_id = record.player2_id if record.player1_id == user.id else record.player1_id
        opponent = db.query(User).filter(User.id == opponent_id).first()

        # 获取rating变化和卡片名
        if record.player1_id == user.id:
            my_rating_change = record.player1_rating_change or 0
            my_card_name = record.player1_card_name
            opponent_card_name = record.player2_card_name
            opponent_rating_change = record.player2_rating_change or 0
        else:
            my_rating_change = record.player2_rating_change or 0
            my_card_name = record.player2_card_name
            opponent_card_name = record.player1_card_name
            opponent_rating_change = record.player1_rating_change or 0

        # 计算 result 字段（前端期望 'win'/'lose'/'draw'）
        if record.winner_id == 0:
            result_str = 'draw'
        elif is_winner:
            result_str = 'win'
        else:
            result_str = 'lose'

        result.append({
            "id": record.id,
            "result": result_str,
            "is_winner": is_winner,
            "opponent": opponent.username if opponent else "未知",
            "reward_gold": record.reward_gold,
            "card_stolen": record.card_stolen,
            "my_card_name": my_card_name,
            "opponent_card_name": opponent_card_name,
            "rating_change": my_rating_change,
            "my_rating_change": my_rating_change,
            "opponent_rating_change": opponent_rating_change,
            "duration_rounds": record.duration_rounds or 0,
            "created_at": record.created_at.isoformat()
        })

    return {
        "success": True,
        "records": result
    }


@router.get("/battle/{battle_id}")
def get_battle_detail(battle_id: int, token: str, db: Session = Depends(get_db)):
    """获取战斗详情"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    record = db.query(BattleRecord).filter(
        BattleRecord.id == battle_id,
        (BattleRecord.player1_id == user.id) | (BattleRecord.player2_id == user.id)
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="战斗记录不存在")

    # 判断当前用户是 player1 还是 player2
    is_player1 = record.player1_id == user.id

    # 获取双方用户
    opponent_id = record.player2_id if is_player1 else record.player1_id
    opponent = db.query(User).filter(User.id == opponent_id).first() if opponent_id else None
    my_name = user.username
    opponent_name = opponent.username if opponent else "AI训练师"

    # 获取双方卡片
    my_card_id = record.player1_card_id if is_player1 else record.player2_card_id
    opp_card_id = record.player2_card_id if is_player1 else record.player1_card_id

    my_card_obj = db.query(UserCard).filter(UserCard.id == my_card_id).first() if my_card_id else None
    opp_card_obj = db.query(UserCard).filter(UserCard.id == opp_card_id).first() if opp_card_id else None

    # 构建卡片信息
    def card_info(card_obj, fallback_name):
        if card_obj and card_obj.template:
            return {
                "name": card_obj.template.name,
                "image": card_obj.template.image,
                "category": card_obj.template.category,
                "attack": card_obj.attack,
                "hp": card_obj.hp,
                "defense": card_obj.defense,
            }
        return {
            "name": fallback_name or "未知",
            "image": "",
            "category": "",
            "attack": 0,
            "hp": 0,
            "defense": 0,
        }

    my_card = card_info(my_card_obj, record.player1_card_name if is_player1 else record.player2_card_name)
    opp_card = card_info(opp_card_obj, record.player2_card_name if is_player1 else record.player1_card_name)

    # 计算 result
    if record.winner_id == 0:
        result_str = 'draw'
    elif record.winner_id == user.id:
        result_str = 'win'
    else:
        result_str = 'lose'

    # rating change
    my_rating_change = (record.player1_rating_change if is_player1 else record.player2_rating_change) or 0

    # 解析战斗日志
    battle_logs = []
    if record.battle_log:
        try:
            battle_logs = json.loads(record.battle_log)
        except (json.JSONDecodeError, TypeError):
            battle_logs = [{"type": "legacy_text", "text": line} for line in record.battle_log.split("\n") if line]

    return {
        "success": True,
        "battle": {
            "id": record.id,
            "result": result_str,
            "reward_gold": record.reward_gold,
            "rating_change": my_rating_change,
            "rounds": record.duration_rounds or 0,
            "player_name": my_name,
            "opponent_name": opponent_name,
            "player_card": my_card,
            "opponent_card": opp_card,
            "battle_log": battle_logs,
            "card_stolen": record.card_stolen,
            "created_at": record.created_at.isoformat()
        }
    }
