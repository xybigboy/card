"""
共享工具函数
"""
import hashlib
import os
import re
import uuid
from typing import Optional
from urllib.request import urlopen
from sqlalchemy.orm import Session
from models import User, UserCard, AdminUser
from schemas import CardResponse


def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()


def get_user_by_token(token: str, db: Session) -> Optional[User]:
    """简单的token验证（实际项目应该用JWT）"""
    # 这里简化处理，token就是user_id的base64
    try:
        user_id = int(token.split("_")[1])
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except:
        return None


def card_to_response(card: UserCard) -> CardResponse:
    """将UserCard转换为CardResponse"""
    return CardResponse(
        id=card.id,
        template_id=card.template_id,
        name=card.template.name,
        rarity=card.template.rarity,
        stars=card.stars,
        level=card.level,
        attack=card.attack,
        defense=card.defense,
        hp=card.hp,
        speed=getattr(card, 'speed', None) or card.template.speed,
        skill_name=card.template.skill_name,
        skill_desc=card.template.skill_desc,
        skill_type=card.template.skill_type,
        skill_value=card.template.skill_value,
        skill_trigger=card.template.skill_trigger,
        skill_param=getattr(card.template, 'skill_param', 0),
        skills_json=getattr(card.template, 'skills_json', None),
        is_on_battle=card.is_on_battle,
        category=card.template.category,
        image=getattr(card, 'selected_image', None) or card.template.image,
        selected_image=getattr(card, 'selected_image', None)
    )


def verify_admin_token(token: str, db: Session) -> Optional[AdminUser]:
    """验证管理员token（数据库查询，支持多worker）"""
    if not token:
        return None
    return db.query(AdminUser).filter(AdminUser.token == token).first()


def get_images_dir() -> str:
    """获取图片存储目录路径，确保目录存在"""
    # 使用 static/images/cards 目录存储生成的图片
    images_dir = os.path.join(os.path.dirname(__file__), "static", "images", "cards")
    os.makedirs(images_dir, exist_ok=True)
    return images_dir


def download_image_to_local(url: str, card_name: str) -> Optional[str]:
    """
    下载外部图片URL到本地存储，返回本地相对路径。
    如果下载失败返回 None。
    
    Args:
        url: 外部图片URL
        card_name: 卡片名称，用于生成文件名
    
    Returns:
        本地图片路径（如 /images/cards/xxx.png）或 None
    """
    try:
        # 清理文件名，移除不安全字符
        safe_name = re.sub(r'[^\w\u4e00-\u9fff-]', '_', card_name)[:50]
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{safe_name}_{unique_id}.png"
        
        images_dir = get_images_dir()
        local_path = os.path.join(images_dir, filename)
        
        # 下载图片（超时30秒）
        with urlopen(url, timeout=30) as response:
            image_data = response.read()
        
        # 保存到本地
        with open(local_path, 'wb') as f:
            f.write(image_data)
        
        # 返回相对URL路径（相对于 static 目录）
        return f"/images/cards/{filename}"
    except Exception as e:
        print(f"[Image Download Error] Failed to download {url}: {e}")
        return None
