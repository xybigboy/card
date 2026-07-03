"""
管理员 - 卡片模板 CRUD 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import CardTemplate, UserCard
from schemas import CardTemplateRequest, CardTemplateResponse
from utils import verify_admin_token

router = APIRouter()


@router.get("/admin/card-templates")
def get_card_templates(token: str, db: Session = Depends(get_db)):
    """获取所有卡片模板"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")

    templates = db.query(CardTemplate).order_by(CardTemplate.id).all()

    return {
        "success": True,
        "templates": [CardTemplateResponse.model_validate(t) for t in templates],
        "total": len(templates)
    }


@router.get("/admin/card-templates/{template_id}")
def get_card_template(template_id: int, token: str, db: Session = Depends(get_db)):
    """获取单个卡片模板详情"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")

    template = db.query(CardTemplate).filter(CardTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="卡片模板不存在")

    return {
        "success": True,
        "template": CardTemplateResponse.model_validate(template)
    }


@router.post("/admin/card-templates")
def create_card_template(token: str, data: CardTemplateRequest, db: Session = Depends(get_db)):
    """新增卡片模板"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")

    # 验证稀有度
    valid_rarities = ["普通", "高级", "史诗", "典藏"]
    if data.rarity not in valid_rarities:
        raise HTTPException(status_code=400, detail=f"稀有度必须是: {', '.join(valid_rarities)}")

    template = CardTemplate(
        name=data.name,
        rarity=data.rarity,
        base_stars=data.base_stars,
        base_attack=data.base_attack,
        base_defense=data.base_defense,
        base_hp=data.base_hp,
        speed=data.speed,
        skill_name=data.skill_name,
        skill_desc=data.skill_desc,
        skill_type=data.skill_type,
        skill_value=data.skill_value,
        skill_trigger=data.skill_trigger,
        skill_param=data.skill_param,
        skills_json=data.skills_json,
        category=data.category,
        image=data.image
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return {
        "success": True,
        "message": "卡片模板创建成功",
        "template": CardTemplateResponse.model_validate(template)
    }


@router.put("/admin/card-templates/{template_id}")
def update_card_template(template_id: int, token: str, data: CardTemplateRequest, db: Session = Depends(get_db)):
    """修改卡片模板"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")

    template = db.query(CardTemplate).filter(CardTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="卡片模板不存在")

    # 验证稀有度
    valid_rarities = ["普通", "高级", "史诗", "典藏"]
    if data.rarity not in valid_rarities:
        raise HTTPException(status_code=400, detail=f"稀有度必须是: {', '.join(valid_rarities)}")

    # 更新字段
    template.name = data.name
    template.rarity = data.rarity
    template.base_stars = data.base_stars
    template.base_attack = data.base_attack
    template.base_defense = data.base_defense
    template.base_hp = data.base_hp
    template.speed = data.speed
    template.skill_name = data.skill_name
    template.skill_desc = data.skill_desc
    template.skill_type = data.skill_type
    template.skill_value = data.skill_value
    template.skill_trigger = data.skill_trigger
    template.skill_param = data.skill_param
    template.skills_json = data.skills_json
    template.category = data.category
    template.image = data.image

    db.commit()
    db.refresh(template)

    return {
        "success": True,
        "message": "卡片模板更新成功",
        "template": CardTemplateResponse.model_validate(template)
    }


@router.delete("/admin/card-templates/{template_id}")
def delete_card_template(template_id: int, token: str, db: Session = Depends(get_db)):
    """删除卡片模板"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")

    template = db.query(CardTemplate).filter(CardTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="卡片模板不存在")

    # 检查是否有用户拥有此卡片
    user_cards = db.query(UserCard).filter(UserCard.template_id == template_id).count()
    if user_cards > 0:
        raise HTTPException(status_code=400, detail=f"有 {user_cards} 张用户卡片使用此模板，无法删除")

    db.delete(template)
    db.commit()

    return {
        "success": True,
        "message": "卡片模板删除成功"
    }
