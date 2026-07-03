-- MySQL 5.7 初始化脚本
-- 卡牌对战游戏数据库

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 用户表
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(50) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `card_gold` INT DEFAULT 0,
  `free_draws` INT DEFAULT 10,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `rating` INT DEFAULT 1000,
  `wins` INT DEFAULT 0,
  `losses` INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 卡片模板表
CREATE TABLE IF NOT EXISTS `card_templates` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `rarity` VARCHAR(20) NOT NULL,
  `base_stars` INT DEFAULT 1,
  `base_attack` FLOAT NOT NULL,
  `base_defense` FLOAT NOT NULL,
  `base_hp` FLOAT NOT NULL,
  `speed` FLOAT DEFAULT 100,
  `skill_name` VARCHAR(100),
  `skill_desc` TEXT,
  `skill_type` VARCHAR(50),
  `skill_value` FLOAT DEFAULT 0,
  `skill_trigger` VARCHAR(50),
  `image` VARCHAR(255),
  `category` VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户卡片表
CREATE TABLE IF NOT EXISTS `user_cards` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT,
  `template_id` INT,
  `stars` INT DEFAULT 1,
  `level` INT DEFAULT 1,
  `attack` FLOAT NOT NULL,
  `defense` FLOAT NOT NULL,
  `hp` FLOAT NOT NULL,
  `speed` FLOAT DEFAULT 100,
  `is_on_battle` BOOLEAN DEFAULT FALSE,
  `obtained_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`template_id`) REFERENCES `card_templates`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 战斗记录表
CREATE TABLE IF NOT EXISTS `battle_records` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `player1_id` INT,
  `player2_id` INT,
  `player1_card_id` INT,
  `player2_card_id` INT,
  `winner_id` INT,
  `reward_gold` INT DEFAULT 0,
  `card_stolen` BOOLEAN DEFAULT FALSE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `battle_log` TEXT,
  `player1_rating_change` INT DEFAULT 0,
  `player2_rating_change` INT DEFAULT 0,
  `player1_card_name` VARCHAR(100),
  `player2_card_name` VARCHAR(100),
  `duration_rounds` INT DEFAULT 0,
  FOREIGN KEY (`player1_id`) REFERENCES `users`(`id`),
  FOREIGN KEY (`player2_id`) REFERENCES `users`(`id`),
  FOREIGN KEY (`player1_card_id`) REFERENCES `user_cards`(`id`),
  FOREIGN KEY (`player2_card_id`) REFERENCES `user_cards`(`id`),
  FOREIGN KEY (`winner_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 管理员表
CREATE TABLE IF NOT EXISTS `admin_users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(50) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- AI提供商配置表
CREATE TABLE IF NOT EXISTS `ai_providers` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(50) NOT NULL,
  `base_url` VARCHAR(255) NOT NULL,
  `model` VARCHAR(100) NOT NULL,
  `api_key` VARCHAR(255) NOT NULL,
  `is_active` BOOLEAN DEFAULT TRUE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;
