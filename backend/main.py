"""
卡牌对战游戏 - 后端主入口
FastAPI + SQLite/MySQL + WebSocket

模块化结构:
  routers/     - API 路由模块
  ws/          - WebSocket 模块
  models.py    - 数据模型
  database.py  - 数据库引擎管理（支持 SQLite/MySQL 切换）
  config_db.py - 配置数据库（始终 SQLite，存储 DB 连接配置）
  schemas.py   - Pydantic 模型
  utils.py     - 共享工具函数
  game_logic.py - 游戏逻辑
  card_data.py  - 卡片模板种子数据
  sql/          - 初始化 SQL 脚本
"""
import os
import sqlite3
import hashlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import engine, get_db, Base, DB_PATH
from models import User, UserCard, CardTemplate, BattleRecord, AdminUser, AIProvider, Guild, GuildMember, GuildApplication, GuildCheckIn, CardImage
from card_data import init_card_templates

# ===== 数据库迁移 =====
def _migrate_add_columns():
    """为已有表添加缺失的列"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    migrations = [
        ("battle_records", "player1_rating_change", "INTEGER DEFAULT 0"),
        ("battle_records", "player2_rating_change", "INTEGER DEFAULT 0"),
        ("battle_records", "player1_card_name", "VARCHAR(100)"),
        ("battle_records", "player2_card_name", "VARCHAR(100)"),
        ("battle_records", "duration_rounds", "INTEGER DEFAULT 0"),
        ("card_templates", "skill_param", "FLOAT DEFAULT 0"),
        ("card_templates", "skills_json", "TEXT"),
        ("user_cards", "speed", "FLOAT DEFAULT 100"),
        ("user_cards", "selected_image", "VARCHAR(255)"),
        ("ai_providers", "provider_type", "VARCHAR(20) DEFAULT 'text'"),
    ]
    for table, column, col_def in migrations:
        cursor.execute(f"PRAGMA table_info({table})")
        existing = [row[1] for row in cursor.fetchall()]
        if column not in existing:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
                print(f"Migration: Added column {column} to {table}")
            except Exception as e:
                print(f"Migration warning: {e}")
    # 迁移旧 trigger 值到新格式 + skill_param
    cursor.execute("PRAGMA table_info(card_templates)")
    cols = [r[1] for r in cursor.fetchall()]
    if "skill_param" in cols:
        cursor.execute("UPDATE card_templates SET skill_param=3 WHERE skill_trigger='every_3_rounds' AND (skill_param IS NULL OR skill_param=0)")
        cursor.execute("UPDATE card_templates SET skill_param=30 WHERE skill_trigger='low_hp' AND (skill_param IS NULL OR skill_param=0)")
        cursor.execute("UPDATE card_templates SET skill_param=2 WHERE skill_trigger='round_2' AND (skill_param IS NULL OR skill_param=0)")
        cursor.execute("UPDATE card_templates SET skill_param=3 WHERE skill_trigger='round_3' AND (skill_param IS NULL OR skill_param=0)")
        cursor.execute("UPDATE card_templates SET skill_param=4 WHERE skill_trigger='round_4' AND (skill_param IS NULL OR skill_param=0)")
    conn.commit()
    conn.close()


def _migrate_balance_patch():
    """平衡性调整迁移"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE card_templates
        SET skill_value = 20, skill_desc = '每回合恢复5%生命值，攻击力提升20%'
        WHERE name = '漩涡鸣人' AND skill_value = 30
    """)
    cursor.execute("""
        UPDATE card_templates
        SET base_stars = 2, base_attack = 55, base_defense = 45,
            base_hp = 230, speed = 100, skill_value = 15,
            skill_desc = '有15%概率直接秒杀敌人（对高星卡概率降低）'
        WHERE name = '柯南' AND base_attack = 30
    """)
    conn.commit()
    conn.close()


def _migrate_user_card_speed():
    """为 user_cards 添加 speed 列"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(user_cards)")
    existing = [row[1] for row in cursor.fetchall()]
    if "speed" not in existing:
        cursor.execute("ALTER TABLE user_cards ADD COLUMN speed FLOAT DEFAULT 100")
        cursor.execute("""
            UPDATE user_cards SET speed = (
                SELECT ct.speed * (1 + (user_cards.stars - 1) * 0.12)
                FROM card_templates ct WHERE ct.id = user_cards.template_id
            ) WHERE template_id IS NOT NULL
        """)
        print(f"Migration: Added speed column to user_cards")
    conn.commit()
    conn.close()


def _migrate_admin_token():
    """为 admin_users 添加 token 列（支持多worker的数据库token验证）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(admin_users)")
    existing = [row[1] for row in cursor.fetchall()]
    if "token" not in existing:
        cursor.execute("ALTER TABLE admin_users ADD COLUMN token VARCHAR(100)")
        print("Migration: Added token column to admin_users")
    conn.commit()
    conn.close()


def _init_admin_user(db):
    """初始化管理员用户"""
    if db.query(AdminUser).count() == 0:
        admin = AdminUser(
            username="admin",
            password_hash=hashlib.sha256("admin123".encode()).hexdigest()
        )
        db.add(admin)
        db.commit()
        print("已创建默认管理员账号: admin / admin123")


def _init_default_ai_providers(db):
    """初始化默认AI提供商（按名称去重，防止多worker并发重复插入）都是免费的可以注册后使用自己哈"""
    defaults = [
        AIProvider(name="Sensenova文本", base_url="https://token.sensenova.cn/v1",
                   model="deepseek-v4-flash", api_key="sk-4mzKIHPOtVcpVzpDuTCF7FwWUDoQqn5va",
                   provider_type="text"),
        AIProvider(name="Agnes文本", base_url="https://apihub.agnes-ai.com/v1",
                   model="agnes-2.0-flash", api_key="sk-osNHztGg4pAhMXNO5yXgpSMSrVO60rAUsnd9gDgdFuTKODfsa",
                   provider_type="text"),
        AIProvider(name="Sensenova图片", base_url="https://token.sensenova.cn/v1",
                   model="sensenova-u1-fast", api_key="sk-4mzKIHPOtVcpVzpDuTCF7FwWUDoQqn5va",
                   provider_type="image"),
        AIProvider(name="Agnes图片", base_url="https://apihub.agnes-ai.com/v1",
                   model="agnes-image-2.1-flash", api_key="sk-osNHztGg4pAhMXNO5yXgpSMSrVO60rAUsnd9gDgdFuTKODfsa",
                   provider_type="image"),
    ]
    added = 0
    for p in defaults:
        existing = db.query(AIProvider).filter(AIProvider.name == p.name).first()
        if not existing:
            db.add(p)
            added += 1
    if added > 0:
        db.commit()
        print(f"已初始化 {added} 个默认AI提供商")


def _dedup_ai_providers(db):
    """清理重复的AI提供商（按名称去重，保留ID最小的）"""
    from sqlalchemy import func
    providers = db.query(AIProvider).order_by(AIProvider.id).all()
    seen_names = {}
    to_delete = []
    for p in providers:
        if p.name in seen_names:
            to_delete.append(p)
        else:
            seen_names[p.name] = p.id
    if to_delete:
        for p in to_delete:
            print(f"删除重复AI提供商: {p.name} (id={p.id})")
            db.delete(p)
        db.commit()
        print(f"共清理 {len(to_delete)} 个重复AI提供商")


# ===== 创建表 & 运行迁移 =====
Base.metadata.create_all(bind=engine)

# SQLite 专属迁移（MySQL 不需要这些）
from database import get_current_db_info
_db_info = get_current_db_info()
if _db_info.get("db_type") == "sqlite":
    _migrate_add_columns()
    _migrate_balance_patch()
    _migrate_user_card_speed()
    _migrate_admin_token()

# 初始化数据
db = next(get_db())
init_card_templates(db)
_init_admin_user(db)
_init_default_ai_providers(db)
_dedup_ai_providers(db)
db.close()

# 确保图片存储目录存在
from utils import get_images_dir
get_images_dir()

# ===== 创建 FastAPI 应用 =====
app = FastAPI(title="卡牌对战游戏")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 注册路由 =====
from routers import auth, gacha, cards, battle, shop, ranking, matchmaking, challenge, guild
from routers import admin_auth, admin_cards, admin_ai, admin_db, admin_rewards, skins
from ws import pvp

app.include_router(auth.router, prefix="/api")
app.include_router(gacha.router, prefix="/api")
app.include_router(cards.router, prefix="/api")
app.include_router(battle.router, prefix="/api")
app.include_router(shop.router, prefix="/api")
app.include_router(ranking.router, prefix="/api")
app.include_router(matchmaking.router, prefix="/api")
app.include_router(challenge.router, prefix="/api")
app.include_router(guild.router, prefix="/api")
app.include_router(skins.router, prefix="/api")
app.include_router(admin_auth.router, prefix="/api")
app.include_router(admin_cards.router, prefix="/api")
app.include_router(admin_ai.router, prefix="/api")
app.include_router(admin_db.router, prefix="/api")
app.include_router(admin_rewards.router, prefix="/api")
app.include_router(pvp.router, prefix="/ws")


# ===== SPA Fallback & 静态文件 =====
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import FileResponse

class SPAFallbackMiddleware(BaseHTTPMiddleware):
    """SPA fallback: 对非静态资源的404请求返回 index.html"""
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if response.status_code == 404:
            path = request.url.path
            if "." not in path.split("/")[-1] and not path.startswith("/api") and not path.startswith("/ws"):
                index_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
                if os.path.exists(index_file):
                    return FileResponse(index_file)
        return response

app.add_middleware(SPAFallbackMiddleware)

static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
