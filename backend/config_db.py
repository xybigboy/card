"""
配置数据库 - 始终使用 SQLite，存储游戏数据库的连接配置
与游戏数据数据库分离，确保无论游戏数据库切换到哪里，配置始终可读
"""
import os
import sqlite3
from datetime import datetime

_data_dir = os.environ.get('DATA_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'))
CONFIG_DB_PATH = os.path.join(_data_dir, "config.db")


def _ensure_config_dir():
    os.makedirs(os.path.dirname(CONFIG_DB_PATH), exist_ok=True)


def _init_config_db():
    """初始化配置数据库"""
    _ensure_config_dir()
    conn = sqlite3.connect(CONFIG_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS db_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL,
            db_type VARCHAR(20) NOT NULL DEFAULT 'sqlite',
            host VARCHAR(255) DEFAULT '',
            port INTEGER DEFAULT 0,
            database VARCHAR(100) DEFAULT '',
            username VARCHAR(100) DEFAULT '',
            password VARCHAR(255) DEFAULT '',
            is_active INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_active_db_config():
    """获取当前活跃的数据库配置，如果没有则返回默认 SQLite 配置"""
    _init_config_db()
    conn = sqlite3.connect(CONFIG_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM db_config WHERE is_active = 1 LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row["id"],
            "name": row["name"],
            "db_type": row["db_type"],
            "host": row["host"],
            "port": row["port"],
            "database": row["database"],
            "username": row["username"],
            "password": row["password"],
            "is_active": True,
        }
    # 默认配置: SQLite
    _data_dir = os.environ.get('DATA_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'))
    return {
        "id": 0,
        "name": "默认SQLite",
        "db_type": "sqlite",
        "host": "",
        "port": 0,
        "database": os.path.join(_data_dir, "game.db"),
        "username": "",
        "password": "",
        "is_active": True,
    }


def list_db_configs():
    """列出所有数据库配置"""
    _init_config_db()
    conn = sqlite3.connect(CONFIG_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM db_config ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "db_type": r["db_type"],
            "host": r["host"],
            "port": r["port"],
            "database": r["database"],
            "username": r["username"],
            "password": r["password"],
            "is_active": bool(r["is_active"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def add_db_config(name, db_type, host="", port=0, database="", username="", password=""):
    """添加数据库配置"""
    _init_config_db()
    conn = sqlite3.connect(CONFIG_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO db_config (name, db_type, host, port, database, username, password, is_active) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
        (name, db_type, host, port, database, username, password)
    )
    conn.commit()
    config_id = cursor.lastrowid
    conn.close()
    return config_id


def update_db_config(config_id, **kwargs):
    """更新数据库配置"""
    _init_config_db()
    conn = sqlite3.connect(CONFIG_DB_PATH)
    cursor = conn.cursor()
    fields = []
    values = []
    for k, v in kwargs.items():
        if k in ("name", "db_type", "host", "port", "database", "username", "password", "is_active"):
            fields.append(f"{k} = ?")
            values.append(v)
    if not fields:
        return False
    values.append(config_id)
    cursor.execute(f"UPDATE db_config SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected


def delete_db_config(config_id):
    """删除数据库配置"""
    _init_config_db()
    conn = sqlite3.connect(CONFIG_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM db_config WHERE id = ?", (config_id,))
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected


def set_active_db_config(config_id):
    """设置活跃的数据库配置"""
    _init_config_db()
    conn = sqlite3.connect(CONFIG_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE db_config SET is_active = 0")
    cursor.execute("UPDATE db_config SET is_active = 1 WHERE id = ?", (config_id,))
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected


# 初始化
_init_config_db()
