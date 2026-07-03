"""
WebSocket PVP 匹配系统
包含 MatchManager 类和 websocket_pvp 处理函数
"""
import json
import asyncio
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserCard, CardTemplate, BattleRecord
from utils import get_user_by_token
from game_logic import simulate_battle, calculate_battle_reward, calculate_rating_change

router = APIRouter()


class MatchManager:
    """匹配管理器"""
    def __init__(self):
        self.waiting_players = []  # 等待匹配的玩家列表
        self.active_battles = {}   # 进行中的战斗

    @staticmethod
    async def safe_send(ws, data):
        """安全发送 WebSocket 消息，断线时不抛异常"""
        try:
            await ws.send_json(data)
        except Exception:
            pass

    async def add_to_queue(self, websocket: WebSocket, user_id: int, card_id: int, db: Session):
        """加入匹配队列"""
        player = {
            "websocket": websocket,
            "user_id": user_id,
            "card_id": card_id,
            "db": db
        }

        # 检查是否有可匹配的对手
        opponent = None
        for p in self.waiting_players:
            if p["user_id"] != user_id:
                opponent = p
                break

        if opponent:
            # 匹配成功
            self.waiting_players.remove(opponent)
            await self.start_battle(player, opponent)
        else:
            # 加入等待队列
            self.waiting_players.append(player)
            await websocket.send_json({
                "type": "matching",
                "message": "正在匹配对手..."
            })

    def remove_from_queue(self, user_id: int):
        """从匹配队列移除"""
        self.waiting_players = [
            p for p in self.waiting_players if p["user_id"] != user_id
        ]

    def get_queue_size(self) -> int:
        """获取当前等待队列人数"""
        return len(self.waiting_players)

    async def start_ai_battle(self, player: dict):
        """与AI对手战斗"""
        import random as _rand
        battle_id = f"ai_battle_{uuid.uuid4().hex[:8]}"
        ws = player["websocket"]
        db = player["db"]

        # 获取玩家卡片
        card1 = db.query(UserCard).filter(UserCard.id == player["card_id"]).first()
        if not card1:
            await self.safe_send(ws, {"type": "error", "message": "卡片不存在"})
            return

        # 生成AI卡片 - 从模板库随机选一张, 属性为玩家卡片的70-90%
        tpl_count = db.query(CardTemplate).count()
        ai_template = db.query(CardTemplate).offset(
            _rand.randint(0, max(0, tpl_count - 1))
        ).first()
        if not ai_template:
            await self.safe_send(ws, {"type": "error", "message": "无法生成AI对手"})
            return

        scale = _rand.uniform(0.7, 0.9)
        ai_card_name = ai_template.name
        ai_stars = max(1, card1.stars - _rand.randint(0, 1))
        ai_hp = card1.hp * scale
        ai_attack = card1.attack * scale
        ai_defense = card1.defense * scale
        ai_image = ai_template.image

        # 构建mock user_card对象 (simulate_battle 内部会创建 BattleCard)
        class MockUserCard:
            pass

        ai_mock = MockUserCard()
        ai_mock.template = ai_template
        ai_mock.hp = ai_hp
        ai_mock.attack = ai_attack
        ai_mock.defense = ai_defense
        ai_mock.speed = card1.speed * scale if getattr(card1, 'speed', None) else ai_template.speed * scale
        ai_mock.stars = ai_stars

        # 通知玩家匹配到AI（含完整属性）
        await self.safe_send(ws, {
            "type": "matched",
            "battle_id": battle_id,
            "is_ai": True,
            "my_card": {
                "name": card1.template.name,
                "stars": card1.stars,
                "level": card1.level,
                "hp": card1.hp,
                "attack": card1.attack,
                "defense": card1.defense,
                "speed": getattr(card1, 'speed', None) or card1.template.speed,
                "image": card1.template.image,
                "category": card1.template.category,
                "rarity": card1.template.rarity,
                "skill_name": card1.template.skill_name,
                "skill_desc": card1.template.skill_desc,
            },
            "opponent": {
                "name": f"AI训练师",
                "card": {
                    "name": ai_card_name,
                    "stars": ai_stars,
                    "level": 1,
                    "hp": ai_hp,
                    "attack": ai_attack,
                    "defense": ai_defense,
                    "speed": card1.speed * scale if getattr(card1, 'speed', None) else ai_template.speed * scale,
                    "image": ai_image,
                    "category": ai_template.category,
                    "rarity": ai_template.rarity,
                    "skill_name": ai_template.skill_name,
                    "skill_desc": ai_template.skill_desc,
                }
            }
        })

        # 模拟战斗 (simulate_battle 内部会创建 BattleCard, 传原始对象即可)
        winner_id, battle_logs, duration_rounds = simulate_battle(card1, ai_mock)

        # 逐条发送战斗日志
        for i, log_entry in enumerate(battle_logs):
            await asyncio.sleep(0.3)
            await self.safe_send(ws, {
                "type": "battle_log",
                "log": log_entry,
                "index": i + 1
            })

        # 计算奖励 (AI战斗减半, 不掠夺卡片, 不影响积分)
        reward_db = next(get_db())
        try:
            user = reward_db.query(User).filter(User.id == player["user_id"]).first()
            if not user:
                return

            result = "draw"
            reward_gold = 15
            rating_change = 0

            if winner_id == 1:
                result = "win"
                reward_gold = 30
                user.wins += 1
            elif winner_id == 2:
                result = "lose"
                reward_gold = 10
                user.losses += 1

            user.card_gold += reward_gold

            # 保存战斗记录
            battle_record = BattleRecord(
                player1_id=player["user_id"],
                player2_id=0,  # AI 用 0
                player1_card_id=player["card_id"],
                player2_card_id=0,
                winner_id=player["user_id"] if winner_id == 1 else (0 if winner_id == 0 else -1),
                reward_gold=reward_gold,
                card_stolen=False,
                battle_log=json.dumps(battle_logs, ensure_ascii=False),
                player1_rating_change=0,
                player2_rating_change=0,
                player1_card_name=card1.template.name,
                player2_card_name=ai_card_name,
                duration_rounds=duration_rounds
            )
            reward_db.add(battle_record)
            reward_db.commit()

            await self.safe_send(ws, {
                "type": "battle_end",
                "result": result,
                "reward_gold": reward_gold,
                "rating_change": 0,
                "is_ai": True
            })
        except Exception as e:
            print(f"[AI Battle Error] {e}")
            await self.safe_send(ws, {"type": "error", "message": "AI战斗结算异常"})
        finally:
            reward_db.close()

    async def start_battle(self, player1: dict, player2: dict):
        """开始战斗"""
        battle_id = f"battle_{uuid.uuid4().hex[:8]}"

        # 获取卡片信息
        db1 = player1["db"]
        db2 = player2["db"]

        card1 = db1.query(UserCard).filter(UserCard.id == player1["card_id"]).first()
        card2 = db2.query(UserCard).filter(UserCard.id == player2["card_id"]).first()

        if not card1 or not card2:
            await self.safe_send(player1["websocket"], {"type": "error", "message": "卡片不存在"})
            await self.safe_send(player2["websocket"], {"type": "error", "message": "卡片不存在"})
            return

        # 通知双方匹配成功（包含完整属性，防止前端显示旧数据）
        def card_battle_info(card):
            return {
                "name": card.template.name,
                "stars": card.stars,
                "level": card.level,
                "hp": card.hp,
                "attack": card.attack,
                "defense": card.defense,
                "speed": getattr(card, 'speed', None) or card.template.speed,
                "image": card.template.image,
                "category": card.template.category,
                "rarity": card.template.rarity,
                "skill_name": card.template.skill_name,
                "skill_desc": card.template.skill_desc,
            }

        await self.safe_send(player1["websocket"], {
            "type": "matched",
            "battle_id": battle_id,
            "my_card": card_battle_info(card1),
            "opponent": {
                "name": db2.query(User).filter(User.id == player2["user_id"]).first().username,
                "card": card_battle_info(card2)
            }
        })

        await self.safe_send(player2["websocket"], {
            "type": "matched",
            "battle_id": battle_id,
            "my_card": card_battle_info(card2),
            "opponent": {
                "name": db1.query(User).filter(User.id == player1["user_id"]).first().username,
                "card": card_battle_info(card1)
            }
        })

        # 模拟战斗
        winner_id, battle_logs, duration_rounds = simulate_battle(card1, card2)

        # 逐条发送结构化战斗日志
        for i, log_entry in enumerate(battle_logs):
            await asyncio.sleep(0.3)  # 每回合间隔
            log_message = {
                "type": "battle_log",
                "log": log_entry,
                "index": i + 1
            }
            await self.safe_send(player1["websocket"], log_message)
            await self.safe_send(player2["websocket"], log_message)

        # 计算奖励 - 使用新 db session 防止断线后旧 session 已关闭
        reward_db = next(get_db())
        try:
            user1 = reward_db.query(User).filter(User.id == player1["user_id"]).first()
            user2 = reward_db.query(User).filter(User.id == player2["user_id"]).first()

            if winner_id == 1:
                winner = user1
                loser = user2
                winner_card = card1
                loser_card = card2
            elif winner_id == 2:
                winner = user2
                loser = user1
                winner_card = card2
                loser_card = card1
            else:
                # 平局
                await self.safe_send(player1["websocket"], {
                    "type": "battle_end",
                    "result": "draw",
                    "reward_gold": 25,
                    "rating_change": 0
                })
                await self.safe_send(player2["websocket"], {
                    "type": "battle_end",
                    "result": "draw",
                    "reward_gold": 25,
                    "rating_change": 0
                })
                user1.card_gold += 25
                user2.card_gold += 25

                # 保存平局战斗记录
                battle_record = BattleRecord(
                    player1_id=player1["user_id"],
                    player2_id=player2["user_id"],
                    player1_card_id=player1["card_id"],
                    player2_card_id=player2["card_id"],
                    winner_id=0,
                    reward_gold=25,
                    card_stolen=False,
                    battle_log=json.dumps(battle_logs, ensure_ascii=False),
                    player1_rating_change=0,
                    player2_rating_change=0,
                    player1_card_name=card1.template.name,
                    player2_card_name=card2.template.name,
                    duration_rounds=duration_rounds
                )
                reward_db.add(battle_record)
                reward_db.commit()
                return

            # 计算奖励
            winner_gold, loser_gold = calculate_battle_reward(
                winner.rating, loser.rating, winner_card.stars
            )

            # 积分变化
            winner_rating_change, loser_rating_change = calculate_rating_change(
                winner.rating, loser.rating
            )

            # 更新数据
            winner.card_gold += winner_gold
            loser.card_gold += loser_gold
            winner.wins += 1
            loser.losses += 1
            winner.rating += winner_rating_change
            loser.rating += loser_rating_change

            # 确定 p1/p2 的 rating 变化
            if winner_id == 1:
                p1_rating_change = winner_rating_change
                p2_rating_change = loser_rating_change
            else:
                p1_rating_change = loser_rating_change
                p2_rating_change = winner_rating_change

            # 掠夺卡片（30%概率）- 只有对手卡片超过3张，且被掠夺卡片2星及以下
            card_stolen = False
            stolen_card_name = None
            if winner_id == 1:
                if card2.stars <= 2 and len(user2.cards) > 3:
                    if __import__('random').random() < 0.3:
                        card2.user_id = user1.id
                        card2.is_on_battle = False
                        card_stolen = True
                        stolen_card_name = card2.template.name
            else:
                if card1.stars <= 2 and len(user1.cards) > 3:
                    if __import__('random').random() < 0.3:
                        card1.user_id = user2.id
                        card1.is_on_battle = False
                        card_stolen = True
                        stolen_card_name = card1.template.name

            # 保存战斗记录
            battle_record = BattleRecord(
                player1_id=player1["user_id"],
                player2_id=player2["user_id"],
                player1_card_id=player1["card_id"],
                player2_card_id=player2["card_id"],
                winner_id=winner.id,
                reward_gold=winner_gold,
                card_stolen=card_stolen,
                battle_log=json.dumps(battle_logs, ensure_ascii=False),
                player1_rating_change=p1_rating_change,
                player2_rating_change=p2_rating_change,
                player1_card_name=card1.template.name,
                player2_card_name=card2.template.name,
                duration_rounds=duration_rounds
            )
            reward_db.add(battle_record)
            reward_db.commit()

            # 发送战斗结果
            await self.safe_send(player1["websocket"], {
                "type": "battle_end",
                "result": "win" if winner_id == 1 else "lose",
                "reward_gold": winner_gold if winner_id == 1 else loser_gold,
                "rating_change": winner_rating_change if winner_id == 1 else loser_rating_change,
                "card_stolen": card_stolen and winner_id == 2,
                "stolen_card_name": stolen_card_name if (card_stolen and winner_id == 2) else None,
                "stole_card": card_stolen and winner_id == 1,
                "stole_card_name": stolen_card_name if (card_stolen and winner_id == 1) else None
            })

            await self.safe_send(player2["websocket"], {
                "type": "battle_end",
                "result": "win" if winner_id == 2 else "lose",
                "reward_gold": winner_gold if winner_id == 2 else loser_gold,
                "rating_change": winner_rating_change if winner_id == 2 else loser_rating_change,
                "card_stolen": card_stolen and winner_id == 1,
                "stolen_card_name": stolen_card_name if (card_stolen and winner_id == 1) else None,
                "stole_card": card_stolen and winner_id == 2,
                "stole_card_name": stolen_card_name if (card_stolen and winner_id == 2) else None
            })
        except Exception as e:
            print(f"[Battle Error] {e}")
        finally:
            reward_db.close()


match_manager = MatchManager()


@router.websocket("/pvp")
async def websocket_pvp(websocket: WebSocket, token: str, card_id: int):
    """PVP WebSocket连接"""
    await websocket.accept()

    # 验证token
    db = next(get_db())
    user = get_user_by_token(token, db)

    if not user:
        await websocket.send_json({"type": "error", "message": "无效的token"})
        await websocket.close()
        return

    # 验证卡片
    card = db.query(UserCard).filter(
        UserCard.id == card_id, UserCard.user_id == user.id
    ).first()

    if not card:
        await websocket.send_json({"type": "error", "message": "卡片不存在"})
        await websocket.close()
        return

    try:
        # 加入匹配
        await match_manager.add_to_queue(websocket, user.id, card_id, db)

        # 保持连接 - 监听客户端消息
        brawl_active = False
        brawl_stats = {"wins": 0, "losses": 0, "draws": 0, "streak": 0, "max_streak": 0, "total_gold": 0, "battles": 0}

        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
                msg_type = msg.get("type")

                if msg_type == "ai_battle":
                    match_manager.remove_from_queue(user.id)
                    player_info = {
                        "websocket": websocket,
                        "user_id": user.id,
                        "card_id": card_id,
                        "db": db
                    }
                    try:
                        await match_manager.start_ai_battle(player_info)
                    except Exception as ai_err:
                        print(f"[AI Battle Error] {ai_err}")
                        await match_manager.safe_send(websocket, {
                            "type": "error",
                            "message": f"AI对战失败: {ai_err}"
                        })
                    return

                elif msg_type == "brawl_start":
                    # 进入大乱斗模式
                    brawl_active = True
                    brawl_stats = {"wins": 0, "losses": 0, "draws": 0, "streak": 0, "max_streak": 0, "total_gold": 0, "battles": 0}
                    match_manager.remove_from_queue(user.id)
                    await match_manager.safe_send(websocket, {"type": "brawl_started", "stats": brawl_stats})

                    # 大乱斗循环
                    while brawl_active:
                        try:
                            # 尝试匹配真人对手（等3秒）
                            opponent = None
                            for p in match_manager.waiting_players:
                                if p["user_id"] != user.id:
                                    opponent = p
                                    break

                            if opponent:
                                # 真人对战
                                match_manager.waiting_players.remove(opponent)
                                await match_manager.safe_send(websocket, {"type": "brawl_matching", "message": "已匹配到对手！"})

                                # 获取双方卡片
                                card1 = db.query(UserCard).filter(UserCard.id == card_id).first()
                                card2 = opponent["db"].query(UserCard).filter(UserCard.id == opponent["card_id"]).first()

                                if card1 and card2:
                                    # 发送matched
                                    def _card_info(c):
                                        return {
                                            "name": c.template.name, "stars": c.stars, "level": c.level,
                                            "hp": c.hp, "attack": c.attack, "defense": c.defense,
                                            "speed": getattr(c, 'speed', None) or c.template.speed,
                                            "image": c.template.image, "category": c.template.category,
                                            "rarity": c.template.rarity,
                                            "skill_name": c.template.skill_name, "skill_desc": c.template.skill_desc,
                                        }

                                    await match_manager.safe_send(websocket, {
                                        "type": "matched",
                                        "my_card": _card_info(card1),
                                        "opponent": {
                                            "name": "对手",
                                            "card": _card_info(card2)
                                        }
                                    })

                                    # 模拟战斗
                                    winner_id, battle_logs, duration_rounds = simulate_battle(card1, card2)

                                    # 发送战斗日志
                                    for i, log_entry in enumerate(battle_logs):
                                        await asyncio.sleep(0.3)
                                        await match_manager.safe_send(websocket, {
                                            "type": "battle_log",
                                            "log": log_entry,
                                            "index": i + 1
                                        })

                                    # 更新统计
                                    brawl_stats["battles"] += 1
                                    if winner_id == 1:
                                        brawl_stats["wins"] += 1
                                        brawl_stats["streak"] += 1
                                        brawl_stats["max_streak"] = max(brawl_stats["max_streak"], brawl_stats["streak"])
                                        brawl_stats["total_gold"] += 50
                                    elif winner_id == 2:
                                        brawl_stats["losses"] += 1
                                        brawl_stats["streak"] = 0
                                        brawl_stats["total_gold"] += 25
                                    else:
                                        brawl_stats["draws"] += 1
                                        brawl_stats["total_gold"] += 30

                                    await match_manager.safe_send(websocket, {
                                        "type": "battle_end",
                                        "result": "win" if winner_id == 1 else ("lose" if winner_id == 2 else "draw"),
                                        "reward_gold": 50 if winner_id == 1 else (25 if winner_id == 2 else 30),
                                        "rating_change": 0,
                                        "is_brawl": True
                                    })
                                    await match_manager.safe_send(websocket, {"type": "brawl_stats", "stats": brawl_stats})

                            else:
                                # 没有真人对手，进行AI对战
                                player_info = {
                                    "websocket": websocket,
                                    "user_id": user.id,
                                    "card_id": card_id,
                                    "db": db
                                }
                                # 临时设置brawl标记，修改AI战斗后的行为
                                # 使用简化的AI战斗流程
                                card1 = db.query(UserCard).filter(UserCard.id == card_id).first()
                                if not card1:
                                    break

                                import random as _rand
                                tpl_count = db.query(CardTemplate).count()
                                ai_template = db.query(CardTemplate).offset(
                                    _rand.randint(0, max(0, tpl_count - 1))
                                ).first()

                                if ai_template and card1:
                                    scale = _rand.uniform(0.7, 0.9)
                                    class MockUserCard: pass
                                    ai_mock = MockUserCard()
                                    ai_mock.template = ai_template
                                    ai_mock.hp = card1.hp * scale
                                    ai_mock.attack = card1.attack * scale
                                    ai_mock.defense = card1.defense * scale
                                    ai_mock.speed = (getattr(card1, 'speed', None) or card1.template.speed) * scale
                                    ai_mock.stars = max(1, card1.stars - _rand.randint(0, 1))

                                    await match_manager.safe_send(websocket, {
                                        "type": "matched",
                                        "is_ai": True,
                                        "my_card": {
                                            "name": card1.template.name, "stars": card1.stars, "level": card1.level,
                                            "hp": card1.hp, "attack": card1.attack, "defense": card1.defense,
                                            "speed": getattr(card1, 'speed', None) or card1.template.speed,
                                            "image": card1.template.image, "category": card1.template.category,
                                            "rarity": card1.template.rarity,
                                            "skill_name": card1.template.skill_name, "skill_desc": card1.template.skill_desc,
                                        },
                                        "opponent": {
                                            "name": "AI训练师",
                                            "card": {
                                                "name": ai_template.name, "stars": ai_mock.stars, "level": 1,
                                                "hp": ai_mock.hp, "attack": ai_mock.attack, "defense": ai_mock.defense,
                                                "speed": ai_mock.speed, "image": ai_template.image,
                                                "category": ai_template.category, "rarity": ai_template.rarity,
                                                "skill_name": ai_template.skill_name, "skill_desc": ai_template.skill_desc,
                                            }
                                        }
                                    })

                                    winner_id, battle_logs, duration_rounds = simulate_battle(card1, ai_mock)

                                    for i, log_entry in enumerate(battle_logs):
                                        await asyncio.sleep(0.3)
                                        await match_manager.safe_send(websocket, {
                                            "type": "battle_log",
                                            "log": log_entry,
                                            "index": i + 1
                                        })

                                    brawl_stats["battles"] += 1
                                    if winner_id == 1:
                                        brawl_stats["wins"] += 1
                                        brawl_stats["streak"] += 1
                                        brawl_stats["max_streak"] = max(brawl_stats["max_streak"], brawl_stats["streak"])
                                        brawl_stats["total_gold"] += 30
                                    elif winner_id == 2:
                                        brawl_stats["losses"] += 1
                                        brawl_stats["streak"] = 0
                                        brawl_stats["total_gold"] += 10
                                    else:
                                        brawl_stats["draws"] += 1
                                        brawl_stats["total_gold"] += 15

                                    # 发放奖励
                                    reward_db = next(get_db())
                                    try:
                                        u = reward_db.query(User).filter(User.id == user.id).first()
                                        if u:
                                            reward = 30 if winner_id == 1 else (10 if winner_id == 2 else 15)
                                            u.card_gold += reward
                                            if winner_id == 1:
                                                u.wins += 1
                                            elif winner_id == 2:
                                                u.losses += 1
                                            reward_db.commit()
                                    except Exception as e:
                                        print(f"[Brawl Reward Error] {e}")
                                    finally:
                                        reward_db.close()

                                    await match_manager.safe_send(websocket, {
                                        "type": "battle_end",
                                        "result": "win" if winner_id == 1 else ("lose" if winner_id == 2 else "draw"),
                                        "reward_gold": 30 if winner_id == 1 else (10 if winner_id == 2 else 15),
                                        "rating_change": 0,
                                        "is_ai": True,
                                        "is_brawl": True
                                    })
                                    await match_manager.safe_send(websocket, {"type": "brawl_stats", "stats": brawl_stats})

                            # 等待2秒后继续下一场
                            await asyncio.sleep(2)

                        except Exception as brawl_err:
                            print(f"[Brawl Error] {brawl_err}")
                            await asyncio.sleep(3)

                    # 大乱斗结束
                    await match_manager.safe_send(websocket, {
                        "type": "brawl_end",
                        "stats": brawl_stats
                    })
                    return

                elif msg_type == "brawl_stop":
                    brawl_active = False
                    await match_manager.safe_send(websocket, {
                        "type": "brawl_stopping",
                        "message": "正在结束大乱斗..."
                    })

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        match_manager.remove_from_queue(user.id)
    except Exception as e:
        match_manager.remove_from_queue(user.id)
        print(f"[WS Error] user={user.id}: {e}")
    finally:
        db.close()
