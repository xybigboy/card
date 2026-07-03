from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Date, Text
from sqlalchemy.orm import relationship
from datetime import datetime, date
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    card_gold = Column(Integer, default=0)  # 卡金
    free_draws = Column(Integer, default=10)  # 免费抽卡次数
    created_at = Column(DateTime, default=datetime.now)  # 使用本地时间(CST)
    rating = Column(Integer, default=1000)  # PVP积分
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)

    cards = relationship("UserCard", back_populates="owner", cascade="all, delete-orphan")


class CardTemplate(Base):
    """卡片模板 - 预设的卡片数据"""
    __tablename__ = "card_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # 卡片名称
    rarity = Column(String(20), nullable=False)  # 普通/高级/史诗/典藏
    base_stars = Column(Integer, default=1)  # 基础星级
    base_attack = Column(Float, nullable=False)  # 基础攻击力
    base_defense = Column(Float, nullable=False)  # 基础防御力
    base_hp = Column(Float, nullable=False)  # 基础生命值
    speed = Column(Float, default=100)  # 速度（决定先手）
    skill_name = Column(String(100))  # 技能名称
    skill_desc = Column(Text)  # 技能描述
    skill_type = Column(String(50))  # 技能类型
    skill_value = Column(Float, default=0)  # 技能数值
    skill_trigger = Column(String(50))  # 触发条件: passive/every_round/every_n_rounds/round_n/hp_below_pct/on_death
    skill_param = Column(Float, default=0)  # 触发参数: N(every_n_rounds间隔) / 百分比(hp_below_pct阈值) / 回合数(round_n)
    skills_json = Column(Text)  # JSON数组：多重技能 [{"type":"heal","value":30,"trigger":"every_round","param":0,"name":"治疗术","desc":"..."}]
    image = Column(String(255))  # 卡片图片
    category = Column(String(50))  # 分类（龙珠/火影/奥特曼等）


class UserCard(Base):
    """用户拥有的卡片"""
    __tablename__ = "user_cards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    template_id = Column(Integer, ForeignKey("card_templates.id"))
    stars = Column(Integer, default=1)  # 当前星级
    level = Column(Integer, default=1)  # 等级
    attack = Column(Float, nullable=False)  # 当前攻击力
    defense = Column(Float, nullable=False)  # 当前防御力
    hp = Column(Float, nullable=False)  # 当前生命值
    speed = Column(Float, default=100)  # 当前速度
    is_on_battle = Column(Boolean, default=False)  # 是否出战
    selected_image = Column(String(255), nullable=True)  # 玩家选择的皮肤图片路径，null=使用模板默认
    obtained_at = Column(DateTime, default=datetime.now)

    owner = relationship("User", back_populates="cards")
    template = relationship("CardTemplate")


class BattleRecord(Base):
    """战斗记录"""
    __tablename__ = "battle_records"

    id = Column(Integer, primary_key=True, index=True)
    player1_id = Column(Integer, ForeignKey("users.id"))
    player2_id = Column(Integer, ForeignKey("users.id"))
    player1_card_id = Column(Integer, ForeignKey("user_cards.id"))
    player2_card_id = Column(Integer, ForeignKey("user_cards.id"))
    winner_id = Column(Integer, ForeignKey("users.id"))
    reward_gold = Column(Integer, default=0)
    card_stolen = Column(Boolean, default=False)  # 是否掠夺了卡片
    created_at = Column(DateTime, default=datetime.now)
    battle_log = Column(Text)  # 战斗日志
    player1_rating_change = Column(Integer, default=0)
    player2_rating_change = Column(Integer, default=0)
    player1_card_name = Column(String(100))
    player2_card_name = Column(String(100))
    duration_rounds = Column(Integer, default=0)


class AdminUser(Base):
    __tablename__ = "admin_users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    token = Column(String(100), unique=True, nullable=True)  # 管理员token（存数据库，支持多worker）
    created_at = Column(DateTime, default=datetime.now)


class AIProvider(Base):
    """AI服务提供商配置"""
    __tablename__ = "ai_providers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)  # 显示名称
    base_url = Column(String(255), nullable=False)  # API基础URL
    model = Column(String(100), nullable=False)  # 模型名称
    api_key = Column(String(255), nullable=False)  # API密钥
    provider_type = Column(String(20), default="text")  # text / image
    is_active = Column(Boolean, default=True)  # 是否启用
    created_at = Column(DateTime, default=datetime.now)


class Guild(Base):
    """公会"""
    __tablename__ = "guilds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # 公会名称（唯一）
    leader_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 会长
    description = Column(Text)  # 公会简介
    fund = Column(Integer, default=0)  # 公会资金（公会金库卡金）
    created_at = Column(DateTime, default=datetime.now)  # 使用本地时间(CST)

    members = relationship("GuildMember", back_populates="guild", cascade="all, delete-orphan")
    applications = relationship("GuildApplication", back_populates="guild", cascade="all, delete-orphan")
    check_ins = relationship("GuildCheckIn", back_populates="guild", cascade="all, delete-orphan")


class GuildMember(Base):
    """公会成员"""
    __tablename__ = "guild_members"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guilds.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="member")  # leader / vice_leader / member
    joined_at = Column(DateTime, default=datetime.now)

    guild = relationship("Guild", back_populates="members")


class GuildApplication(Base):
    """公会申请"""
    __tablename__ = "guild_applications"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guilds.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="pending")  # pending / approved / rejected
    applied_at = Column(DateTime, default=datetime.now)

    guild = relationship("Guild", back_populates="applications")


class GuildCheckIn(Base):
    """公会签到"""
    __tablename__ = "guild_check_ins"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guilds.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    check_in_date = Column(Date, default=date.today)  # 签到日期
    reward_claimed = Column(Boolean, default=True)  # 是否已领取奖励

    guild = relationship("Guild", back_populates="check_ins")


class CardImage(Base):
    """卡片图片/皮肤 - 每张卡片模板可以有多张图片"""
    __tablename__ = "card_images"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("card_templates.id"), nullable=False)
    image_path = Column(String(255), nullable=False)  # 相对路径如 /images/cards/xxx.png
    source = Column(String(20), default="admin")  # admin / player
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 上传者ID（玩家上传时记录）
    is_default = Column(Boolean, default=False)  # 是否为默认图片
    created_at = Column(DateTime, default=datetime.now)

    template = relationship("CardTemplate")
