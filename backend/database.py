"""
数据库引擎管理 - 支持动态切换 SQLite / MySQL
启动时从 config_db 读取活跃配置，创建对应的引擎
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from config_db import get_active_db_config

Base = declarative_base()

# 兼容旧代码: DB_PATH
_env_data_dir = os.environ.get('DATA_DIR')
if _env_data_dir:
    BASE_DIR = _env_data_dir
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data") if not _env_data_dir else BASE_DIR
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "game.db")


def build_connection_url(db_config):
    """根据配置构建 SQLAlchemy 连接 URL"""
    db_type = db_config.get("db_type", "sqlite")

    if db_type == "sqlite":
        db_path = db_config.get("database", DB_PATH)
        if not db_path:
            db_path = DB_PATH
        # 确保目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        return f"sqlite:///{db_path}"

    elif db_type == "mysql":
        host = db_config.get("host", "localhost")
        port = db_config.get("port", 3306)
        database = db_config.get("database", "")
        username = db_config.get("username", "root")
        password = db_config.get("password", "")
        return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}?charset=utf8mb4"

    else:
        raise ValueError(f"不支持的数据库类型: {db_type}")


def create_engine_from_config(db_config):
    """根据配置创建引擎"""
    url = build_connection_url(db_config)
    db_type = db_config.get("db_type", "sqlite")

    if db_type == "sqlite":
        return create_engine(url, connect_args={"check_same_thread": False})
    else:
        return create_engine(url, pool_pre_ping=True, pool_size=10, max_overflow=20, pool_recycle=3600)


def test_db_connection(db_type, host="", port=0, database="", username="", password=""):
    """测试数据库连接，返回 (success, message)"""
    config = {
        "db_type": db_type,
        "host": host,
        "port": port,
        "database": database,
        "username": username,
        "password": password,
    }
    try:
        url = build_connection_url(config)
        if db_type == "sqlite":
            test_engine = create_engine(url, connect_args={"check_same_thread": False})
        else:
            test_engine = create_engine(url, pool_pre_ping=True)
        # 尝试连接
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        test_engine.dispose()
        return True, "连接成功"
    except Exception as e:
        return False, str(e)


# 启动时读取配置并创建引擎
_active_config = get_active_db_config()
engine = create_engine_from_config(_active_config)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 对 SQLite，DB_PATH 与配置保持一致（供迁移函数使用）
if _active_config.get("db_type") == "sqlite":
    _cfg_db = _active_config.get("database", "")
    if _cfg_db:
        DB_PATH = _cfg_db

# 打印当前数据库信息
print(f"[Database] 当前数据库: {_active_config['db_type']} | {_active_config.get('name', '默认')}")


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_db_info():
    """获取当前数据库配置信息"""
    return _active_config


def migrate_data_to_new_db(target_config):
    """
    将当前数据库的所有数据迁移到新的目标数据库
    返回 (success, message, table_count, row_count)
    """
    from models import User, UserCard, CardTemplate, BattleRecord, AdminUser, AIProvider

    # 创建目标引擎
    target_engine = create_engine_from_config(target_config)

    # 在目标库创建所有表
    Base.metadata.create_all(bind=target_engine)
    TargetSession = sessionmaker(autocommit=False, autoflush=False, bind=target_engine)
    target_db = TargetSession()

    # 源数据库会话
    source_db = SessionLocal()

    total_rows = 0
    table_count = 0

    try:
        # 按依赖顺序迁移
        models_to_migrate = [AdminUser, CardTemplate, User, UserCard, BattleRecord, AIProvider]

        for model in models_to_migrate:
            table_name = model.__tablename__
            # 读取源数据
            records = source_db.query(model).all()
            if not records:
                continue

            # 清空目标表（如果已有数据）
            target_db.query(model).delete()

            # 批量插入
            for record in records:
                # 创建新对象，避免绑定到源 session
                new_record = model()
                for col in model.__table__.columns:
                    val = getattr(record, col.name)
                    setattr(new_record, col.name, val)
                target_db.add(new_record)

            total_rows += len(records)
            table_count += 1
            print(f"  迁移 {table_name}: {len(records)} 行")

        target_db.commit()
        return True, f"迁移成功: {table_count} 张表, {total_rows} 条数据", table_count, total_rows

    except Exception as e:
        target_db.rollback()
        return False, f"迁移失败: {str(e)}", 0, 0
    finally:
        source_db.close()
        target_db.close()
        target_engine.dispose()
