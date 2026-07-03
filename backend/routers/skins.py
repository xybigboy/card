"""
卡片皮肤/多图片 API
- 玩家查看可用皮肤列表
- 玩家上传自定义皮肤
- 玩家选择/切换皮肤
- 管理员添加模板皮肤
"""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import User, UserCard, CardTemplate, CardImage
from schemas import CardResponse
from utils import get_user_by_token, card_to_response, get_images_dir
import re

router = APIRouter()


@router.get("/cards/{card_id}/skins")
def get_card_skins(card_id: int, token: str, db: Session = Depends(get_db)):
    """获取卡片所有可用皮肤"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    card = db.query(UserCard).filter(UserCard.id == card_id, UserCard.user_id == user.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")

    template = card.template
    skins = []

    # 模板默认图片
    if template.image:
        skins.append({
            "image_path": template.image,
            "source": "default",
            "is_default": True,
            "is_selected": card.selected_image is None or card.selected_image == template.image,
        })

    # 数据库中的所有皮肤图片
    card_images = db.query(CardImage).filter(CardImage.template_id == template.id).all()
    for ci in card_images:
        # 玩家只能看到管理员生成的和自己上传的
        if ci.source == "player" and ci.uploader_id != user.id:
            continue
        skins.append({
            "image_path": ci.image_path,
            "source": ci.source,
            "is_default": ci.is_default,
            "is_selected": card.selected_image == ci.image_path,
            "id": ci.id,
        })

    return {
        "success": True,
        "skins": skins,
        "selected_image": card.selected_image,
        "default_image": template.image,
    }


@router.post("/cards/{card_id}/skins")
async def upload_card_skin(
    card_id: int,
    token: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """玩家上传自定义皮肤图片"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    card = db.query(UserCard).filter(UserCard.id == card_id, UserCard.user_id == user.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")

    # 验证文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只能上传图片文件")

    # 验证文件大小 (5MB 限制)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过5MB")

    # 生成文件名
    safe_name = re.sub(r'[^\w\u4e00-\u9fff-]', '_', card.template.name)[:30]
    unique_id = uuid.uuid4().hex[:8]
    ext = "png"
    if file.content_type == "image/jpeg":
        ext = "jpg"
    elif file.content_type == "image/gif":
        ext = "gif"
    elif file.content_type == "image/webp":
        ext = "webp"
    filename = f"skin_{safe_name}_{unique_id}.{ext}"

    # 保存文件
    images_dir = get_images_dir()
    file_path = os.path.join(images_dir, filename)
    with open(file_path, "wb") as f:
        f.write(content)

    # 数据库记录
    image_path = f"/images/cards/{filename}"
    card_image = CardImage(
        template_id=card.template_id,
        image_path=image_path,
        source="player",
        uploader_id=user.id,
        is_default=False,
    )
    db.add(card_image)
    db.commit()
    db.refresh(card_image)

    return {
        "success": True,
        "message": "皮肤上传成功",
        "skin": {
            "id": card_image.id,
            "image_path": image_path,
            "source": "player",
        }
    }


@router.put("/cards/{card_id}/skin")
def select_card_skin(card_id: int, token: str, image_path: Optional[str] = None, db: Session = Depends(get_db)):
    """选择/切换卡片皮肤，image_path为null则恢复默认"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    card = db.query(UserCard).filter(UserCard.id == card_id, UserCard.user_id == user.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")

    if image_path is None or image_path == "":
        # 恢复默认
        card.selected_image = None
    elif image_path == card.template.image:
        # 选择默认图片
        card.selected_image = None
    else:
        # 验证图片是否属于该模板或该玩家
        card_image = db.query(CardImage).filter(
            CardImage.template_id == card.template_id,
            CardImage.image_path == image_path,
        ).first()
        if not card_image:
            raise HTTPException(status_code=400, detail="无效的皮肤图片")
        if card_image.source == "player" and card_image.uploader_id != user.id:
            raise HTTPException(status_code=403, detail="无权使用此皮肤")
        card.selected_image = image_path

    db.commit()

    return {
        "success": True,
        "message": "皮肤已切换",
        "card": card_to_response(card).model_dump(),
    }


# ===== 管理员接口 =====

@router.post("/admin/templates/{template_id}/skins")
async def admin_upload_template_skin(
    template_id: int,
    token: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """管理员上传模板皮肤图片"""
    from utils import verify_admin_token
    admin = verify_admin_token(token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="管理员未登录")

    template = db.query(CardTemplate).filter(CardTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只能上传图片文件")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过10MB")

    safe_name = re.sub(r'[^\w\u4e00-\u9fff-]', '_', template.name)[:30]
    unique_id = uuid.uuid4().hex[:8]
    ext = "png"
    if file.content_type == "image/jpeg":
        ext = "jpg"
    elif file.content_type == "image/gif":
        ext = "gif"
    elif file.content_type == "image/webp":
        ext = "webp"
    filename = f"admin_{safe_name}_{unique_id}.{ext}"

    images_dir = get_images_dir()
    file_path = os.path.join(images_dir, filename)
    with open(file_path, "wb") as f:
        f.write(content)

    image_path = f"/images/cards/{filename}"
    card_image = CardImage(
        template_id=template_id,
        image_path=image_path,
        source="admin",
        uploader_id=None,
        is_default=False,
    )
    db.add(card_image)
    db.commit()
    db.refresh(card_image)

    return {
        "success": True,
        "message": "皮肤上传成功",
        "skin": {
            "id": card_image.id,
            "image_path": image_path,
            "source": "admin",
        }
    }


@router.delete("/admin/skins/{skin_id}")
def admin_delete_skin(skin_id: int, token: str, db: Session = Depends(get_db)):
    """管理员删除皮肤图片"""
    from utils import verify_admin_token
    admin = verify_admin_token(token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="管理员未登录")

    card_image = db.query(CardImage).filter(CardImage.id == skin_id).first()
    if not card_image:
        raise HTTPException(status_code=404, detail="皮肤不存在")

    # 删除文件
    try:
        images_dir = get_images_dir()
        filename = card_image.image_path.split("/")[-1]
        file_path = os.path.join(images_dir, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass

    # 清除使用此皮肤的玩家选择
    db.query(UserCard).filter(UserCard.selected_image == card_image.image_path).update(
        {"selected_image": None}
    )

    db.delete(card_image)
    db.commit()

    return {"success": True, "message": "皮肤已删除"}


@router.get("/admin/templates/{template_id}/skins")
def admin_get_template_skins(template_id: int, token: str, db: Session = Depends(get_db)):
    """管理员获取模板所有皮肤"""
    from utils import verify_admin_token
    admin = verify_admin_token(token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="管理员未登录")

    template = db.query(CardTemplate).filter(CardTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    skins = []
    if template.image:
        skins.append({
            "image_path": template.image,
            "source": "default",
            "is_default": True,
            "id": None,
        })

    card_images = db.query(CardImage).filter(CardImage.template_id == template_id).all()
    for ci in card_images:
        skins.append({
            "image_path": ci.image_path,
            "source": ci.source,
            "is_default": ci.is_default,
            "id": ci.id,
            "uploader_id": ci.uploader_id,
            "created_at": ci.created_at.isoformat() if ci.created_at else None,
        })

    return {"success": True, "skins": skins}
