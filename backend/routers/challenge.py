"""
挑战系统路由
支持输入玩家名称挑战指定玩家（离线异步战斗）
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserCard, BattleRecord
from schemas import ChallengeByNameRequest
from utils import get_user_by_token
from game_logic import simulate_battle

router = APIRouter()


@router.post("/challenge/by-name")
def challenge_by_name(token: str, body: ChallengeByNameRequest, db: Session = Depends(get_db)):
    """指名挑战：输入玩家名挑战对方（不需要对方在线）"""
    challenger = get_user_by_token(token, db)
    if not challenger:
        raise HTTPException(status_code=401, detail="无效的token")

    # 查找挑战者出战卡
    my_card = db.query(UserCard).filter(
        UserCard.user_id == challenger.id, UserCard.is_on_battle == True
    ).first()
    if not my_card:
        raise HTTPException(status_code=400, detail="请先设置出战卡片")

    # 查找目标玩家
    target = db.query(User).filter(User.username == body.username).first()
    if not target:
        raise HTTPException(status_code=404, detail=f"玩家「{body.username}」不存在")

    if target.id == challenger.id:
        raise HTTPException(status_code=400, detail="不能挑战自己")

    # 查找目标出战卡
    target_card = db.query(UserCard).filter(
        UserCard.user_id == target.id, UserCard.is_on_battle == True
    ).first()
    if not target_card:
        raise HTTPException(status_code=400, detail=f"玩家「{body.username}」未设置出战卡片")

    # 模拟战斗
    winner_id, battle_logs, duration_rounds = simulate_battle(my_card, target_card)

    # 判定结果
    is_win = winner_id == 1
    result_str = "win" if is_win else ("lose" if winner_id == 2 else "draw")

    # 奖励（友谊赛，不影响积分）
    reward_gold = 20 if is_win else (5 if winner_id == 2 else 10)
    challenger.card_gold += reward_gold

    # 保存战斗记录
    record = BattleRecord(
        player1_id=challenger.id,
        player2_id=target.id,
        player1_card_id=my_card.id,
        player2_card_id=target_card.id,
        winner_id=challenger.id if is_win else (target.id if winner_id == 2 else 0),
        reward_gold=reward_gold,
        card_stolen=False,
        battle_log=json.dumps(battle_logs, ensure_ascii=False),
        player1_rating_change=0,
        player2_rating_change=0,
        player1_card_name=my_card.template.name,
        player2_card_name=target_card.template.name,
        duration_rounds=duration_rounds,
    )
    db.add(record)
    db.commit()

    return {
        "success": True,
        "result": result_str,
        "reward_gold": reward_gold,
        "rating_change": 0,
        "opponent_name": target.username,
        "duration_rounds": duration_rounds,
        "battle_logs": battle_logs,
        "my_card": {
            "name": my_card.template.name,
            "stars": my_card.stars,
            "level": my_card.level,
            "hp": my_card.hp,
            "attack": my_card.attack,
            "defense": my_card.defense,
            "speed": getattr(my_card, 'speed', None) or my_card.template.speed,
            "image": my_card.template.image,
            "category": my_card.template.category,
            "skill_name": my_card.template.skill_name,
            "skill_desc": my_card.template.skill_desc,
        },
        "opponent_card": {
            "name": target_card.template.name,
            "stars": target_card.stars,
            "level": target_card.level,
            "hp": target_card.hp,
            "attack": target_card.attack,
            "defense": target_card.defense,
            "speed": getattr(target_card, 'speed', None) or target_card.template.speed,
            "image": target_card.template.image,
            "category": target_card.template.category,
            "skill_name": target_card.template.skill_name,
            "skill_desc": target_card.template.skill_desc,
        },
    }
