-- SQLite 初始化脚本
-- 用于创建游戏数据库的所有表结构
-- SQLite 不需要预先创建数据库，文件存在即可使用

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    card_gold INTEGER DEFAULT 0,
    free_draws INTEGER DEFAULT 10,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    rating INTEGER DEFAULT 1000,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0
);

-- 卡片模板表
CREATE TABLE IF NOT EXISTS card_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    rarity VARCHAR(20) NOT NULL,
    base_stars INTEGER DEFAULT 1,
    base_attack FLOAT NOT NULL,
    base_defense FLOAT NOT NULL,
    base_hp FLOAT NOT NULL,
    speed FLOAT DEFAULT 100,
    skill_name VARCHAR(100),
    skill_desc TEXT,
    skill_type VARCHAR(50),
    skill_value FLOAT DEFAULT 0,
    skill_trigger VARCHAR(50),
    image VARCHAR(255),
    category VARCHAR(50)
);

-- 用户卡片表
CREATE TABLE IF NOT EXISTS user_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    template_id INTEGER REFERENCES card_templates(id),
    stars INTEGER DEFAULT 1,
    level INTEGER DEFAULT 1,
    attack FLOAT NOT NULL,
    defense FLOAT NOT NULL,
    hp FLOAT NOT NULL,
    speed FLOAT DEFAULT 100,
    is_on_battle BOOLEAN DEFAULT 0,
    obtained_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 战斗记录表
CREATE TABLE IF NOT EXISTS battle_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player1_id INTEGER REFERENCES users(id),
    player2_id INTEGER REFERENCES users(id),
    player1_card_id INTEGER REFERENCES user_cards(id),
    player2_card_id INTEGER REFERENCES user_cards(id),
    winner_id INTEGER REFERENCES users(id),
    reward_gold INTEGER DEFAULT 0,
    card_stolen BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    battle_log TEXT,
    player1_rating_change INTEGER DEFAULT 0,
    player2_rating_change INTEGER DEFAULT 0,
    player1_card_name VARCHAR(100),
    player2_card_name VARCHAR(100),
    duration_rounds INTEGER DEFAULT 0
);

-- 管理员用户表
CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- AI提供商配置表
CREATE TABLE IF NOT EXISTS ai_providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL,
    base_url VARCHAR(255) NOT NULL,
    model VARCHAR(100) NOT NULL,
    api_key VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_user_cards_user_id ON user_cards(user_id);
CREATE INDEX IF NOT EXISTS idx_user_cards_template_id ON user_cards(template_id);
CREATE INDEX IF NOT EXISTS idx_battle_records_player1 ON battle_records(player1_id);
CREATE INDEX IF NOT EXISTS idx_battle_records_player2 ON battle_records(player2_id);
CREATE INDEX IF NOT EXISTS idx_card_templates_rarity ON card_templates(rarity);
CREATE INDEX IF NOT EXISTS idx_ai_providers_active ON ai_providers(is_active);
