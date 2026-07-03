"""
游戏核心逻辑
- 抽卡系统
- 战斗系统
- 卡片属性计算
"""
import random
import math
from models import CardTemplate, UserCard


# ===== 抽卡概率 =====
DRAW_COST = 100  # 单次抽卡消耗卡金

# 稀有度概率
RARITY_PROBABILITY = {
    "普通": 0.60,    # 60%
    "高级": 0.25,    # 25%
    "史诗": 0.12,    # 12%
    "典藏": 0.03,    # 3%
}

# 星级波动（基础星级上下浮动1-2星）
def get_random_stars(base_stars):
    """根据基础星级随机生成实际星级"""
    # 70%概率基础星级，20%概率+1星，8%概率+2星，2%概率+3星
    rand = random.random()
    if rand < 0.70:
        return base_stars
    elif rand < 0.90:
        return base_stars + 1
    elif rand < 0.98:
        return base_stars + 2
    else:
        return base_stars + 3


def draw_card(db):
    """
    抽一张卡
    返回: UserCard对象
    """
    # 1. 先决定稀有度
    rand = random.random()
    cumulative = 0
    selected_rarity = "普通"
    for rarity, prob in RARITY_PROBABILITY.items():
        cumulative += prob
        if rand <= cumulative:
            selected_rarity = rarity
            break
    
    # 2. 从该稀有度的卡片中随机选一张
    templates = db.query(CardTemplate).filter(CardTemplate.rarity == selected_rarity).all()
    if not templates:
        # 如果该稀有度没有卡，降级到普通
        templates = db.query(CardTemplate).filter(CardTemplate.rarity == "普通").all()
    
    template = random.choice(templates)
    
    # 3. 生成星级
    stars = get_random_stars(template.base_stars)
    
    # 4. 计算属性（星级加成）
    star_multiplier = 1 + (stars - 1) * 0.12  # 每星+12%属性
    
    attack = template.base_attack * star_multiplier
    defense = template.base_defense * star_multiplier
    hp = template.base_hp * star_multiplier
    speed = template.speed * star_multiplier
    
    # 5. 创建用户卡片
    user_card = UserCard(
        template_id=template.id,
        stars=stars,
        level=1,
        attack=round(attack, 1),
        defense=round(defense, 1),
        hp=round(hp, 1),
        speed=round(speed, 1),
        is_on_battle=False
    )
    
    return user_card


def draw_multiple(db, count=10):
    """连抽"""
    cards = []
    for _ in range(count):
        cards.append(draw_card(db))
    return cards


# ===== 卡片升级 =====
def get_upgrade_cost(level):
    """计算升级所需卡金"""
    return int(50 * math.pow(1.15, level - 1))


def upgrade_card(user_card):
    """升级卡片 - 使用比例升级，保留融合加成"""
    old_level_mult = 1 + (user_card.level - 1) * 0.05
    user_card.level += 1
    new_level_mult = 1 + (user_card.level - 1) * 0.05  # 每级+5%
    ratio = new_level_mult / old_level_mult  # 升级比例，保留融合等额外加成

    user_card.attack = round(user_card.attack * ratio, 1)
    user_card.defense = round(user_card.defense * ratio, 1)
    user_card.hp = round(user_card.hp * ratio, 1)
    user_card.speed = round((getattr(user_card, 'speed', None) or user_card.template.speed) * ratio, 1)

    return user_card


# ===== 卡金兑换 =====
def get_card_sell_value(user_card):
    """计算卡片兑换卡金的价值"""
    rarity_values = {
        "普通": 20,
        "高级": 50,
        "史诗": 150,
        "典藏": 500,
    }
    base_value = rarity_values.get(user_card.template.rarity, 20)
    star_bonus = (user_card.stars - 1) * 20
    level_bonus = (user_card.level - 1) * 10
    
    return base_value + star_bonus + level_bonus


# ===== 战斗系统 =====

def _normalize_trigger(trigger, skill_param):
    """将旧版 trigger 值统一转换为新格式，返回 (trigger_type, param)"""
    if not trigger:
        return "passive", 0
    if trigger in ("round_2", "round_3", "round_4"):
        return "round_n", int(trigger.split("_")[1])
    elif trigger == "every_3_rounds":
        return "every_n_rounds", 3
    elif trigger == "low_hp":
        return "hp_below_pct", 30
    elif trigger == "濒死":
        return "on_death", 0
    elif trigger in ("every_n_rounds", "round_n", "hp_below_pct", "on_death") and skill_param:
        return trigger, int(skill_param)
    return trigger, int(skill_param) if skill_param else 0


class BattleCard:
    """战斗中的卡片状态"""
    def __init__(self, user_card):
        self.user_card = user_card
        self.template = user_card.template
        self.max_hp = user_card.hp
        self.current_hp = user_card.hp
        self.attack = user_card.attack
        self.defense = user_card.defense
        self.speed = getattr(user_card, 'speed', None) or user_card.template.speed
        self.stars = user_card.stars

        # 解析技能列表（支持多重技能）
        self.skills = self._parse_skills()

        # 兼容旧代码：保留 trigger_type/trigger_param（取第一个技能的）
        if self.skills:
            self.trigger_type = self.skills[0]["trigger_type"]
            self.trigger_param = self.skills[0]["trigger_param"]
        else:
            self.trigger_type = "passive"
            self.trigger_param = 0

        # 状态效果
        self.attack_buff = 0
        self.defense_buff = 0
        self.damage_reduction = 0
        self.stunned = False
        self.stun_immunity = 0
        self.bleeding = 0  # 流血层数
        self.revive_used = False
        self.lifesteal = 0
        self.armor_pierce = 0
        self.stack_attack_bonus = 0

        # 被动技能在初始化时生效
        self._apply_passive()

    def _parse_skills(self):
        """解析技能列表：优先 skills_json，否则回退到旧单技能字段"""
        import json
        skills = []

        raw_json = getattr(self.template, 'skills_json', None)
        if raw_json:
            try:
                parsed = json.loads(raw_json)
                if isinstance(parsed, list):
                    for s in parsed:
                        if not s.get("type"):
                            continue
                        tt, tp = _normalize_trigger(
                            s.get("trigger", "passive"), s.get("param", 0) or 0
                        )
                        skills.append({
                            "type": s["type"],
                            "value": s.get("value", 0) or 0,
                            "trigger_type": tt,
                            "trigger_param": tp,
                            "name": s.get("name", ""),
                            "desc": s.get("desc", ""),
                            "hp_below_triggered": False,
                            "round_n_triggered": False,
                        })
            except (json.JSONDecodeError, TypeError):
                pass

        # 回退到旧单技能字段
        if not skills and self.template.skill_type:
            tt, tp = _normalize_trigger(
                self.template.skill_trigger,
                getattr(self.template, 'skill_param', 0) or 0
            )
            skills.append({
                "type": self.template.skill_type,
                "value": self.template.skill_value or 0,
                "trigger_type": tt,
                "trigger_param": tp,
                "name": self.template.skill_name or "",
                "desc": self.template.skill_desc or "",
                "hp_below_triggered": False,
                "round_n_triggered": False,
            })

        return skills

    def _apply_passive(self):
        """被动技能在战斗开始时永久生效（遍历所有技能）"""
        for sk in self.skills:
            if sk["trigger_type"] != "passive":
                continue
            st, sv = sk["type"], sk["value"]
            if st == "attack_buff":
                self.attack_buff = max(self.attack_buff, sv)
            elif st == "damage_reduction":
                self.damage_reduction = max(self.damage_reduction, sv)
            elif st == "lifesteal":
                self.lifesteal = max(self.lifesteal, sv)
            elif st == "armor_pierce":
                self.armor_pierce = max(self.armor_pierce, sv)


def calculate_damage(attacker: BattleCard, defender: BattleCard):
    """计算伤害"""
    effective_defense = defender.defense * (1 + defender.defense_buff / 100)
    effective_defense *= (1 - attacker.armor_pierce / 100)

    base_damage = attacker.attack * (1 + attacker.attack_buff / 100 + attacker.stack_attack_bonus / 100)
    damage = max(1, base_damage - effective_defense * 0.5)

    damage *= (1 - defender.damage_reduction / 100)

    return max(1, round(damage, 1))


def _should_trigger_skill(skill_config, round_num):
    """判断本回合是否应该触发某个技能"""
    t = skill_config["trigger_type"]
    p = skill_config["trigger_param"]

    if t == "passive":
        return False
    if t == "every_round":
        return True
    if t == "every_n_rounds":
        return p > 0 and round_num % p == 0
    if t == "round_n":
        if round_num == p and not skill_config["round_n_triggered"]:
            skill_config["round_n_triggered"] = True
            return True
        return False
    if t == "hp_below_pct":
        return False
    if t == "on_death":
        return False
    return False


def apply_skill_effects(card: BattleCard, round_num: int, is_attacker: bool):
    """回合开始时应用技能效果（遍历所有技能）"""
    logs = []
    for sk in card.skills:
        if not _should_trigger_skill(sk, round_num):
            if sk["trigger_type"] == "hp_below_pct" and not sk["hp_below_triggered"]:
                threshold = sk["trigger_param"] or 30
                if card.current_hp / card.max_hp <= threshold / 100:
                    sk["hp_below_triggered"] = True
                    logs.extend(_apply_skill_effect(card, sk, is_attacker, prefix="血量低于"))
            continue
        logs.extend(_apply_skill_effect(card, sk, is_attacker))
    return logs


def _apply_skill_effect(card: BattleCard, skill_config, is_attacker: bool, prefix: str = ""):
    """执行技能效果，返回日志列表"""
    logs = []
    trigger_desc = f"{prefix}{skill_config['trigger_param']}%" if prefix else ""
    skill_type = skill_config["type"]
    skill_value = skill_config["value"]
    skill_name = skill_config.get("name") or card.template.name

    if skill_type == "heal":
        heal_amount = card.max_hp * skill_value / 100
        card.current_hp = min(card.max_hp, card.current_hp + heal_amount)
        logs.append({
            "type": "heal",
            "card": card.template.name,
            "skill_name": skill_name,
            "amount": round(heal_amount, 1),
            "card_hp": round(card.current_hp, 1),
            "text": f"{skill_name} 恢复了 {round(heal_amount, 1)} 点生命值"
        })

    elif skill_type == "stack_attack":
        card.stack_attack_bonus += skill_value
        logs.append({
            "type": "stack_attack",
            "card": skill_name,
            "value": skill_value,
            "current_bonus": card.stack_attack_bonus,
            "text": f"{skill_name} 攻击力提升 {skill_value}%（当前+{card.stack_attack_bonus}%）"
        })

    elif skill_type == "combo":
        heal_amount = card.max_hp * 5 / 100
        card.current_hp = min(card.max_hp, card.current_hp + heal_amount)
        card.attack_buff = max(card.attack_buff, skill_value)
        logs.append({
            "type": "combo",
            "card": card.template.name,
            "skill_name": skill_name,
            "heal": round(heal_amount, 1),
            "attack_buff": skill_value,
            "card_hp": round(card.current_hp, 1),
            "text": f"{skill_name} 恢复 {round(heal_amount, 1)} 生命，攻击力+{skill_value}%"
        })

    elif skill_type == "attack_buff":
        card.attack_buff = max(card.attack_buff, skill_value)
        desc = f"{trigger_desc}，" if trigger_desc else ""
        logs.append({
            "type": "attack_buff",
            "card": skill_name,
            "value": skill_value,
            "text": f"{skill_name} 触发！{desc}攻击力提升 {skill_value}%"
        })

    elif skill_type == "critical_strike":
        logs.append({
            "type": "critical_strike_ready",
            "card": skill_name,
            "text": f"{skill_name} 蓄力完成！本回合必定暴击！"
        })

    elif skill_type == "bonus_damage":
        logs.append({
            "type": "bonus_damage_ready",
            "card": skill_name,
            "value": skill_value,
            "text": f"{skill_name} 蓄力中，本回合攻击将造成额外 {skill_value} 点伤害"
        })

    return logs


def perform_attack(attacker: BattleCard, defender: BattleCard, round_num: int):
    """执行一次攻击"""
    logs = []

    # 检查是否被麻痹
    if attacker.stunned:
        attacker.stunned = False
        attacker.stun_immunity = 2
        logs.append({
            "type": "stunned",
            "card": attacker.template.name,
            "text": f"{attacker.template.name} 被麻痹，跳过本回合！"
        })
        return logs

    # 闪避判定（防守方被动技能）
    for sk in defender.skills:
        if sk["type"] == "dodge" and sk["trigger_type"] == "passive":
            if random.random() < sk["value"] / 100:
                logs.append({
                    "type": "dodge",
                    "card": defender.template.name,
                    "text": f"{defender.template.name} 闪避了攻击！"
                })
                return logs

    # 速度闪避判定
    speed_diff = defender.speed - attacker.speed
    if speed_diff > 0:
        dodge_chance = min(0.15, speed_diff / 400)
        if random.random() < dodge_chance:
            logs.append({
                "type": "speed_dodge",
                "card": defender.template.name,
                "dodge_chance": round(dodge_chance * 100, 1),
                "text": f"{defender.template.name} 凭借速度优势闪避了攻击！"
            })
            return logs

    # 秒杀判定（攻击方被动技能）
    for sk in attacker.skills:
        if sk["type"] == "execute" and sk["trigger_type"] == "passive":
            execute_chance = sk["value"] * max(0.3, 1 - (defender.stars - 1) * 0.15) / 100
            if random.random() < execute_chance:
                defender.current_hp = 0
                logs.append({
                    "type": "execute",
                    "skill": sk.get("name") or attacker.template.name,
                    "attacker": attacker.template.name,
                    "defender": defender.template.name,
                    "defender_hp": 0,
                    "text": f"{sk.get('name') or attacker.template.name} 触发！直接秒杀！"
                })
                return logs

    # 计算伤害
    damage = calculate_damage(attacker, defender)

    # 暴击判定（攻击方被动技能）
    is_critical = False
    for sk in attacker.skills:
        if sk["type"] == "critical" and sk["trigger_type"] == "passive":
            if random.random() < sk["value"] / 100:
                damage *= 2
                is_critical = True
                break

    # round_n 触发的必定暴击
    for sk in attacker.skills:
        if sk["type"] == "critical_strike" and sk["trigger_type"] == "round_n":
            if round_num == sk["trigger_param"] and not sk["round_n_triggered"]:
                sk["round_n_triggered"] = True
                damage *= 2
                is_critical = True

    # every_n_rounds / every_round 额外伤害
    for sk in attacker.skills:
        if sk["type"] == "bonus_damage":
            should_bonus = False
            if sk["trigger_type"] == "every_n_rounds" and sk["trigger_param"] > 0:
                if round_num % sk["trigger_param"] == 0:
                    should_bonus = True
            elif sk["trigger_type"] == "every_round":
                should_bonus = True
            if should_bonus:
                damage += sk["value"]
                logs.append({
                    "type": "bonus_damage",
                    "skill": sk.get("name") or attacker.template.name,
                    "value": sk["value"],
                    "text": f"{sk.get('name') or attacker.template.name} 触发！额外造成 {sk['value']} 点伤害"
                })

    # 流血效果（攻击方被动技能）
    for sk in attacker.skills:
        if sk["type"] == "bleed" and sk["trigger_type"] == "passive":
            if random.random() < 30 / 100:
                defender.bleeding += 1
                logs.append({
                    "type": "bleed",
                    "card": defender.template.name,
                    "text": f"{defender.template.name} 陷入流血状态！（当前{defender.bleeding}层）"
                })
                break

    # 麻痹效果（攻击方被动技能）
    for sk in attacker.skills:
        if sk["type"] == "stun" and sk["trigger_type"] == "passive":
            if defender.stun_immunity <= 0 and random.random() < sk["value"] / 100:
                defender.stunned = True
                logs.append({
                    "type": "stun",
                    "card": defender.template.name,
                    "text": f"{defender.template.name} 被麻痹了！"
                })
                break

    # 造成伤害
    defender.current_hp = max(0, defender.current_hp - damage)

    logs.append({
        "type": "attack",
        "attacker": attacker.template.name,
        "defender": defender.template.name,
        "damage": round(damage, 1),
        "critical": is_critical,
        "defender_hp": round(defender.current_hp, 1),
        "attacker_hp": round(attacker.current_hp, 1),
        "text": f"{attacker.template.name} 对 {defender.template.name} 造成了 {round(damage, 1)} 点伤害" + ("（暴击！）" if is_critical else "")
    })

    # 吸血
    if attacker.lifesteal > 0:
        heal_amount = damage * attacker.lifesteal / 100
        attacker.current_hp = min(attacker.max_hp, attacker.current_hp + heal_amount)
        logs.append({
            "type": "lifesteal",
            "card": attacker.template.name,
            "amount": round(heal_amount, 1),
            "attacker_hp": round(attacker.current_hp, 1),
            "text": f"吸血效果：恢复 {round(heal_amount, 1)} 点生命值"
        })

    # 检查攻击后是否触发 hp_below_pct（攻击方自身血量低）
    for sk in attacker.skills:
        if sk["trigger_type"] == "hp_below_pct" and not sk["hp_below_triggered"]:
            threshold = sk["trigger_param"] or 30
            if attacker.current_hp / attacker.max_hp <= threshold / 100:
                sk["hp_below_triggered"] = True
                if sk["type"] == "attack_buff":
                    attacker.attack_buff = max(attacker.attack_buff, sk["value"])
                    logs.append({
                        "type": "low_hp_buff",
                        "card": sk.get("name") or attacker.template.name,
                        "value": sk["value"],
                        "text": f"{sk.get('name') or attacker.template.name} 触发！生命值低于{threshold}%，攻击力提升 {sk['value']}%"
                    })

    # 检查被攻击方是否触发 hp_below_pct
    for sk in defender.skills:
        if sk["trigger_type"] == "hp_below_pct" and not sk["hp_below_triggered"]:
            threshold = sk["trigger_param"] or 30
            if defender.current_hp / defender.max_hp <= threshold / 100:
                sk["hp_below_triggered"] = True
                if sk["type"] == "attack_buff":
                    defender.attack_buff = max(defender.attack_buff, sk["value"])
                    logs.append({
                        "type": "low_hp_buff",
                        "card": sk.get("name") or defender.template.name,
                        "value": sk["value"],
                        "text": f"{sk.get('name') or defender.template.name} 触发！生命值低于{threshold}%，攻击力提升 {sk['value']}%"
                    })

    return logs


def apply_bleed_damage(card: BattleCard):
    """应用流血伤害"""
    logs = []
    if card.bleeding > 0:
        bleed_damage = card.max_hp * 0.05 * card.bleeding
        card.current_hp = max(0, card.current_hp - bleed_damage)
        logs.append({
            "type": "bleed_damage",
            "card": card.template.name,
            "damage": round(bleed_damage, 1),
            "stacks": card.bleeding,
            "card_hp": round(card.current_hp, 1),
            "text": f"{card.template.name} 因流血损失 {round(bleed_damage, 1)} 点生命值（{card.bleeding}层）"
        })
    return logs


def check_revive(card: BattleCard):
    """检查复活技能（on_death 触发）"""
    logs = []
    for sk in card.skills:
        if (sk["type"] == "revive" and
            sk["trigger_type"] == "on_death" and
            not card.revive_used and
            card.current_hp <= 0):

            card.revive_used = True
            card.current_hp = card.max_hp * sk["value"] / 100
            sk_name = sk.get("name") or card.template.name
            logs.append({
                "type": "revive",
                "skill": sk_name,
                "card": card.template.name,
                "hp": round(card.current_hp, 1),
                "card_hp": round(card.current_hp, 1),
                "text": f"{sk_name} 触发！{card.template.name} 复活了，恢复 {round(card.current_hp, 1)} 点生命值！"
            })
            break

    return logs


def simulate_battle(card1: UserCard, card2: UserCard):
    """
    模拟战斗
    返回: (winner_id, battle_logs, duration_rounds)
    winner_id: 1 或 2，0表示平局
    duration_rounds: 战斗持续回合数
    """
    bc1 = BattleCard(card1)
    bc2 = BattleCard(card2)

    logs = []
    logs.append({
        "type": "battle_start",
        "text": "战斗开始！"
    })
    logs.append({
        "type": "versus",
        "player1": {
            "name": bc1.template.name, "stars": bc1.stars,
            "hp": round(bc1.max_hp, 1), "attack": round(bc1.attack, 1),
            "defense": round(bc1.defense, 1), "speed": round(bc1.speed, 1),
            "skill_name": bc1.template.skill_name, "skill_desc": bc1.template.skill_desc,
        },
        "player2": {
            "name": bc2.template.name, "stars": bc2.stars,
            "hp": round(bc2.max_hp, 1), "attack": round(bc2.attack, 1),
            "defense": round(bc2.defense, 1), "speed": round(bc2.speed, 1),
            "skill_name": bc2.template.skill_name, "skill_desc": bc2.template.skill_desc,
        },
        "text": f"{bc1.template.name} ({bc1.stars}星) VS {bc2.template.name} ({bc2.stars}星)"
    })

    round_num = 1
    max_rounds = 30

    # 先手判定
    first, second = (bc1, bc2) if bc1.speed >= bc2.speed else (bc2, bc1)
    first_id = 1 if first is bc1 else 2
    second_id = 2 if second is bc1 else 1

    logs.append({
        "type": "initiative",
        "card": first.template.name,
        "text": f"{first.template.name} 速度更快，先手攻击！"
    })

    while round_num <= max_rounds:
        logs.append({
            "type": "round_start",
            "round": round_num,
            "text": f"===== 第 {round_num} 回合 ====="
        })

        # 回合开始 - 应用技能效果
        logs.extend(apply_skill_effects(first, round_num, True))
        logs.extend(apply_skill_effects(second, round_num, False))

        # 先手攻击
        logs.extend(perform_attack(first, second, round_num))

        # 检查复活
        logs.extend(check_revive(second))

        if second.current_hp <= 0:
            logs.append({
                "type": "battle_end",
                "winner": first.template.name,
                "winner_id": first_id,
                "text": f"{first.template.name} 获胜！"
            })
            return first_id, logs, round_num

        # 后手攻击
        logs.extend(perform_attack(second, first, round_num))

        # 检查复活
        logs.extend(check_revive(first))

        # 回合结束 - 流血伤害
        logs.extend(apply_bleed_damage(first))
        logs.extend(apply_bleed_damage(second))

        # 流血致死 - 检查复活
        if first.current_hp <= 0:
            logs.extend(check_revive(first))
        if second.current_hp <= 0:
            logs.extend(check_revive(second))

        # 回合结束 - 递减麻痹免疫
        if first.stun_immunity > 0:
            first.stun_immunity -= 1
        if second.stun_immunity > 0:
            second.stun_immunity -= 1

        if first.current_hp <= 0:
            logs.append({
                "type": "battle_end",
                "winner": second.template.name,
                "winner_id": second_id,
                "text": f"{second.template.name} 获胜！"
            })
            return second_id, logs, round_num

        if second.current_hp <= 0:
            logs.append({
                "type": "battle_end",
                "winner": first.template.name,
                "winner_id": first_id,
                "text": f"{first.template.name} 获胜！"
            })
            return first_id, logs, round_num

        logs.append({
            "type": "round_status",
            "round": round_num,
            "player1": {"name": bc1.template.name, "hp": round(bc1.current_hp, 1), "max_hp": round(bc1.max_hp, 1)},
            "player2": {"name": bc2.template.name, "hp": round(bc2.current_hp, 1), "max_hp": round(bc2.max_hp, 1)},
            "text": f"{bc1.template.name}: {round(bc1.current_hp, 1)}/{round(bc1.max_hp, 1)} HP | {bc2.template.name}: {round(bc2.current_hp, 1)}/{round(bc2.max_hp, 1)} HP"
        })

        round_num += 1

    # 超时判定
    logs.append({"type": "timeout", "text": "战斗超时！"})
    if bc1.current_hp > bc2.current_hp:
        logs.append({
            "type": "battle_end",
            "winner": bc1.template.name,
            "winner_id": 1,
            "reason": "hp_advantage",
            "text": f"{bc1.template.name} 血量更多，获胜！"
        })
        return 1, logs, round_num
    elif bc2.current_hp > bc1.current_hp:
        logs.append({
            "type": "battle_end",
            "winner": bc2.template.name,
            "winner_id": 2,
            "reason": "hp_advantage",
            "text": f"{bc2.template.name} 血量更多，获胜！"
        })
        return 2, logs, round_num
    else:
        logs.append({
            "type": "battle_end",
            "winner_id": 0,
            "reason": "draw",
            "text": "平局！"
        })
        return 0, logs, round_num


# ===== PVP奖励 =====
def calculate_battle_reward(winner_rating, loser_rating, winner_card_stars):
    """计算战斗奖励"""
    # 基础卡金奖励
    base_gold = 50
    
    # 星级加成
    star_bonus = winner_card_stars * 10
    
    # 积分差加成（打赢高分玩家奖励更多）
    rating_diff = max(0, loser_rating - winner_rating)
    rating_bonus = int(rating_diff * 0.1)
    
    total_gold = base_gold + star_bonus + rating_bonus
    
    # 输家减半
    loser_gold = int(total_gold * 0.5)
    
    return total_gold, loser_gold


def calculate_rating_change(winner_rating, loser_rating):
    """计算积分变化（ELO简化版）"""
    k = 32
    expected_winner = 1 / (1 + pow(10, (loser_rating - winner_rating) / 400))
    expected_loser = 1 / (1 + pow(10, (winner_rating - loser_rating) / 400))
    
    winner_change = int(k * (1 - expected_winner))
    loser_change = int(k * (0 - expected_loser))

    # 积分下限保护：不低于 0
    loser_change = max(loser_change, -loser_rating)

    return winner_change, loser_change
