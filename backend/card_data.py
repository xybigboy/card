"""
卡片模板数据 - 动漫角色
"""

CARD_TEMPLATES = [
    # ===== 龙珠系列 =====
    {
        "name": "卡卡罗特",
        "rarity": "典藏",
        "base_stars": 5,
        "base_attack": 150,
        "base_defense": 80,
        "base_hp": 500,
        "speed": 120,
        "skill_name": "超级赛亚人变身",
        "skill_desc": "第3回合开始，攻击力提升50%",
        "skill_type": "attack_buff",
        "skill_value": 50,
        "skill_trigger": "round_3",
        "category": "龙珠",
        "image": "db-goku"
    },
    {
        "name": "贝吉塔",
        "rarity": "史诗",
        "base_stars": 4,
        "base_attack": 140,
        "base_defense": 70,
        "base_hp": 450,
        "speed": 125,
        "skill_name": "最终闪光",
        "skill_desc": "每回合有20%概率造成双倍伤害",
        "skill_type": "critical",
        "skill_value": 20,
        "skill_trigger": "passive",
        "category": "龙珠",
        "image": "db-vegeta"
    },
    {
        "name": "弗利沙",
        "rarity": "史诗",
        "base_stars": 4,
        "base_attack": 130,
        "base_defense": 90,
        "base_hp": 480,
        "speed": 110,
        "skill_name": "再生能力",
        "skill_desc": "每回合恢复5%最大生命值",
        "skill_type": "heal",
        "skill_value": 5,
        "skill_trigger": "every_round",
        "category": "龙珠",
        "image": "db-frieza"
    },
    {
        "name": "孙悟饭",
        "rarity": "高级",
        "base_stars": 3,
        "base_attack": 100,
        "base_defense": 60,
        "base_hp": 350,
        "speed": 105,
        "skill_name": "愤怒爆发",
        "skill_desc": "生命值低于30%时，攻击力提升80%",
        "skill_type": "attack_buff",
        "skill_value": 80,
        "skill_trigger": "low_hp",
        "category": "龙珠",
        "image": "db-gohan"
    },
    {
        "name": "克林",
        "rarity": "普通",
        "base_stars": 2,
        "base_attack": 60,
        "base_defense": 40,
        "base_hp": 200,
        "speed": 95,
        "skill_name": "气圆斩",
        "skill_desc": "攻击无视30%防御",
        "skill_type": "armor_pierce",
        "skill_value": 30,
        "skill_trigger": "passive",
        "category": "龙珠",
        "image": "db-krillin"
    },

    # ===== 火影系列 =====
    {
        "name": "漩涡鸣人",
        "rarity": "典藏",
        "base_stars": 5,
        "base_attack": 140,
        "base_defense": 100,
        "base_hp": 550,
        "speed": 115,
        "skill_name": "九尾模式",
        "skill_desc": "每回合恢复5%生命值，攻击力提升20%",
        "skill_type": "combo",
        "skill_value": 20,
        "skill_trigger": "every_round",
        "category": "火影",
        "image": "nz-naruto"
    },
    {
        "name": "宇智波佐助",
        "rarity": "史诗",
        "base_stars": 4,
        "base_attack": 145,
        "base_defense": 65,
        "base_hp": 420,
        "speed": 130,
        "skill_name": "写轮眼",
        "skill_desc": "有25%概率闪避攻击",
        "skill_type": "dodge",
        "skill_value": 25,
        "skill_trigger": "passive",
        "category": "火影",
        "image": "nz-sasuke"
    },
    {
        "name": "旗木卡卡西",
        "rarity": "史诗",
        "base_stars": 4,
        "base_attack": 120,
        "base_defense": 85,
        "base_hp": 400,
        "speed": 120,
        "skill_name": "雷切",
        "skill_desc": "第2回合必定暴击（2倍伤害）",
        "skill_type": "critical_strike",
        "skill_value": 100,
        "skill_trigger": "round_2",
        "category": "火影",
        "image": "nz-kakashi"
    },
    {
        "name": "我爱罗",
        "rarity": "高级",
        "base_stars": 3,
        "base_attack": 85,
        "base_defense": 110,
        "base_hp": 400,
        "speed": 85,
        "skill_name": "砂之盾",
        "skill_desc": "受到的伤害减少20%",
        "skill_type": "damage_reduction",
        "skill_value": 20,
        "skill_trigger": "passive",
        "category": "火影",
        "image": "nz-gaara"
    },
    {
        "name": "春野樱",
        "rarity": "普通",
        "base_stars": 2,
        "base_attack": 55,
        "base_defense": 50,
        "base_hp": 220,
        "speed": 90,
        "skill_name": "医疗忍术",
        "skill_desc": "每回合恢复10%生命值",
        "skill_type": "heal",
        "skill_value": 10,
        "skill_trigger": "every_round",
        "category": "火影",
        "image": "nz-sakura"
    },

    # ===== 奥特曼系列 =====
    {
        "name": "迪迦奥特曼",
        "rarity": "典藏",
        "base_stars": 5,
        "base_attack": 145,
        "base_defense": 95,
        "base_hp": 520,
        "speed": 110,
        "skill_name": "光之复苏",
        "skill_desc": "濒死时复活一次，恢复50%生命值（限1次）",
        "skill_type": "revive",
        "skill_value": 50,
        "skill_trigger": "濒死",
        "category": "奥特曼",
        "image": "ul-tiga"
    },
    {
        "name": "赛罗奥特曼",
        "rarity": "史诗",
        "base_stars": 4,
        "base_attack": 150,
        "base_defense": 70,
        "base_hp": 400,
        "speed": 140,
        "skill_name": "终极形态",
        "skill_desc": "第4回合攻击力翻倍",
        "skill_type": "attack_buff",
        "skill_value": 100,
        "skill_trigger": "round_4",
        "category": "奥特曼",
        "image": "ul-zero"
    },
    {
        "name": "泽塔奥特曼",
        "rarity": "高级",
        "base_stars": 3,
        "base_attack": 105,
        "base_defense": 75,
        "base_hp": 380,
        "speed": 115,
        "skill_name": "德尔塔天爪",
        "skill_desc": "攻击附带10%吸血效果",
        "skill_type": "lifesteal",
        "skill_value": 10,
        "skill_trigger": "passive",
        "category": "奥特曼",
        "image": "ul-z"
    },
    {
        "name": "初代奥特曼",
        "rarity": "普通",
        "base_stars": 2,
        "base_attack": 65,
        "base_defense": 55,
        "base_hp": 250,
        "speed": 100,
        "skill_name": "斯派修姆光线",
        "skill_desc": "每3回合造成额外50点伤害",
        "skill_type": "bonus_damage",
        "skill_value": 50,
        "skill_trigger": "every_3_rounds",
        "category": "奥特曼",
        "image": "ul-original"
    },

    # ===== 其他动漫 =====
    {
        "name": "路飞",
        "rarity": "史诗",
        "base_stars": 4,
        "base_attack": 135,
        "base_defense": 80,
        "base_hp": 500,
        "speed": 105,
        "skill_name": "橡胶果实",
        "skill_desc": "受到的物理伤害减少15%",
        "skill_type": "damage_reduction",
        "skill_value": 15,
        "skill_trigger": "passive",
        "category": "海贼王",
        "image": "op-luffy"
    },
    {
        "name": "索隆",
        "rarity": "高级",
        "base_stars": 3,
        "base_attack": 120,
        "base_defense": 55,
        "base_hp": 320,
        "speed": 125,
        "skill_name": "三刀流",
        "skill_desc": "攻击力提升25%",
        "skill_type": "attack_buff",
        "skill_value": 25,
        "skill_trigger": "passive",
        "category": "海贼王",
        "image": "op-zoro"
    },
    {
        "name": "炭治郎",
        "rarity": "高级",
        "base_stars": 3,
        "base_attack": 110,
        "base_defense": 70,
        "base_hp": 350,
        "speed": 110,
        "skill_name": "火之神神乐",
        "skill_desc": "每回合攻击力提升5%（可叠加）",
        "skill_type": "stack_attack",
        "skill_value": 5,
        "skill_trigger": "every_round",
        "category": "鬼灭",
        "image": "ds-tanjiro"
    },
    {
        "name": "祢豆子",
        "rarity": "普通",
        "base_stars": 2,
        "base_attack": 50,
        "base_defense": 60,
        "base_hp": 280,
        "speed": 100,
        "skill_name": "血鬼术",
        "skill_desc": "攻击有30%概率使敌人流血（每回合损失5%生命）",
        "skill_type": "bleed",
        "skill_value": 5,
        "skill_trigger": "passive",
        "category": "鬼灭",
        "image": "ds-nezuko"
    },
    {
        "name": "柯南",
        "rarity": "普通",
        "base_stars": 2,
        "base_attack": 55,
        "base_defense": 45,
        "base_hp": 230,
        "speed": 100,
        "skill_name": "真相只有一个",
        "skill_desc": "有15%概率直接秒杀敌人（对高星卡概率降低）",
        "skill_type": "execute",
        "skill_value": 15,
        "skill_trigger": "passive",
        "category": "名侦探柯南",
        "image": "dt-conan"
    },
    {
        "name": "皮卡丘",
        "rarity": "高级",
        "base_stars": 3,
        "base_attack": 95,
        "base_defense": 50,
        "base_hp": 300,
        "speed": 140,
        "skill_name": "十万伏特",
        "skill_desc": "攻击有30%概率麻痹敌人（跳过下回合）",
        "skill_type": "stun",
        "skill_value": 30,
        "skill_trigger": "passive",
        "category": "宝可梦",
        "image": "pm-pikachu"
    },
]


def init_card_templates(db):
    """初始化卡片模板数据"""
    from models import CardTemplate
    
    # 检查是否已有数据
    if db.query(CardTemplate).count() > 0:
        return
    
    for card_data in CARD_TEMPLATES:
        card = CardTemplate(**card_data)
        db.add(card)
    
    db.commit()
    print(f"已初始化 {len(CARD_TEMPLATES)} 张卡片模板")
