"""
管理员 - AI卡片生成 + 提供商管理 + 图片生成路由
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import CardTemplate, AIProvider, UserCard
from schemas import (
    AIGenerateRequest, BatchSaveRequest, AIProviderCreate, AIProviderUpdate,
    ImageGenerateRequest, CardImageGenerateRequest,
)
from utils import verify_admin_token, download_image_to_local
from game_logic import get_random_stars

router = APIRouter()


# ===== AI 卡片生成 =====

@router.post("/admin/ai-generate-cards")
async def ai_generate_cards(token: str, body: AIGenerateRequest, db: Session = Depends(get_db)):
    """使用AI批量生成卡片模板（可选生成图片）"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")

    provider = db.query(AIProvider).filter(
        AIProvider.id == body.provider_id,
        AIProvider.is_active == True,
        AIProvider.provider_type == "text",
    ).first()
    if not provider:
        raise HTTPException(status_code=400, detail="文本AI提供商不存在或未启用")

    if body.count < 1 or body.count > 20:
        raise HTTPException(status_code=400, detail="生成数量必须在1-20之间")

    # 获取现有卡片名称（用于去重）
    existing_names = set(r[0] for r in db.query(CardTemplate.name).all())
    existing_summary = []
    for t in db.query(CardTemplate).all():
        existing_summary.append(
            f"  {t.name}({t.rarity}/{t.base_stars}星): ATK={t.base_attack} DEF={t.base_defense} "
            f"HP={t.base_hp} SPD={t.speed} 技能={t.skill_name}({t.skill_type},{t.skill_value},"
            f"trigger={t.skill_trigger},param={getattr(t, 'skill_param', 0)})"
        )

    category_hint = f"动漫系列: {body.category}" if body.category else "请从各种热门动漫中选择（龙珠、火影、海贼王、奥特曼、鬼灭、宝可梦、名侦探柯南等）"
    theme_hint = f"主题: {body.theme}" if body.theme else ""

    prompt = f"""你是一个动漫卡牌游戏设计师。请生成 {body.count} 张新的卡牌模板数据。

{category_hint}
{theme_hint}

现有卡片的数值参考（用于保持平衡，且名称不能与这些重复）:
{chr(10).join(existing_summary)}

数值范围参考:
- 普通(2星): ATK 50-65, DEF 40-60, HP 200-280, SPD 90-105
- 高级(3星): ATK 85-120, DEF 50-110, HP 300-400, SPD 85-140
- 史诗(4星): ATK 120-150, DEF 65-90, HP 400-500, SPD 105-140
- 典藏(5星): ATK 140-155, DEF 80-100, HP 500-560, SPD 110-125

可用的技能类型(skill_type): attack_buff, critical, critical_strike, heal, stack_attack, combo, damage_reduction, lifesteal, armor_pierce, dodge, execute, stun, bleed, bonus_damage, revive

技能触发方式(skill_trigger) — 必须选择以下之一:
- passive: 被动，永久生效（如暴击率、闪避、吸血、减伤）
- every_round: 每回合触发（如持续回血、叠加攻击）
- every_n_rounds: 每隔N回合触发，需设skill_param=N（如每3回合额外伤害，param=3）
- round_n: 第N回合触发一次，需设skill_param=N（如第3回合攻击翻倍，param=3）
- hp_below_pct: 生命值低于百分之N时触发一次，需设skill_param=N（如血低于30%攻击提升，param=30）
- on_death: 死亡时触发（如复活）

skill_param: 触发参数，与触发方式配合使用（every_n_rounds=间隔回合数, round_n=回合数, hp_below_pct=百分比阈值），其他触发方式设为0

稀有度分配建议: 普通30%, 高级35%, 史诗25%, 典藏10%

category字段必须使用以下对应关系:
- 龙珠 / 火影 / 奥特曼 / 海贼王 / 鬼灭 / 宝可梦 / 名侦探柯南 / 其他动漫

每张卡片必须包含以下字段，且不能为空:
name(唯一不重复), rarity, base_stars, base_attack, base_defense, base_hp, speed,
skill_name(技能名称，不能为空), skill_desc(技能描述，不能为空),
skill_type, skill_value(技能数值), skill_trigger, skill_param(触发参数，默认0), category

请以JSON数组格式输出，只输出JSON数组，不要其他内容。"""

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            base_url=provider.base_url,
            api_key=provider.api_key
        )

        response = await client.chat.completions.create(
            model=provider.model,
            messages=[
                {"role": "system", "content": "你是一个专业的游戏数值策划，擅长设计平衡的卡牌数值。只输出JSON数组，不要markdown代码块。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=4000
        )

        content = response.choices[0].message.content.strip()

        # 提取JSON（可能有markdown代码块包裹）
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        generated = json.loads(content)

        # 验证和修正
        valid_rarities = ["普通", "高级", "史诗", "典藏"]
        valid_skill_types = [
            "attack_buff", "critical", "critical_strike", "heal", "stack_attack",
            "combo", "damage_reduction", "lifesteal", "armor_pierce", "dodge",
            "execute", "stun", "bleed", "bonus_damage", "revive"
        ]
        valid_triggers = ["passive", "every_round", "every_n_rounds", "round_n", "hp_below_pct", "on_death"]
        stars_map = {"普通": 2, "高级": 3, "史诗": 4, "典藏": 5}
        trigger_param_map = {"every_3_rounds": 3, "low_hp": 30, "round_2": 2, "round_3": 3, "round_4": 4, "濒死": 0}

        validated = []
        seen_names = set()
        for card in generated:
            name = card.get("name", "").strip()
            if not name:
                continue
            # 名称唯一性校验
            if name in existing_names or name in seen_names:
                continue
            seen_names.add(name)

            rarity = card.get("rarity", "普通")
            if rarity not in valid_rarities:
                rarity = "普通"
            card["rarity"] = rarity
            card["base_stars"] = stars_map.get(rarity, 2)

            card["base_attack"] = max(20, min(200, float(card.get("base_attack", 60))))
            card["base_defense"] = max(20, min(150, float(card.get("base_defense", 50))))
            card["base_hp"] = max(100, min(700, float(card.get("base_hp", 250))))
            card["speed"] = max(60, min(160, float(card.get("speed", 100))))

            skill_type = card.get("skill_type", "")
            if skill_type not in valid_skill_types:
                skill_type = "attack_buff"
            card["skill_type"] = skill_type
            card["skill_value"] = max(1, min(100, float(card.get("skill_value", 10))))

            # 确保 skill_name 和 skill_desc 不为空
            if not card.get("skill_name"):
                card["skill_name"] = "未知技能"
            if not card.get("skill_desc"):
                card["skill_desc"] = "技能效果"

            # 规范化 trigger
            trigger = card.get("skill_trigger", "passive")
            if trigger in trigger_param_map:
                card["skill_param"] = trigger_param_map[trigger]
                # 转换旧 trigger 值
                if trigger == "every_3_rounds":
                    card["skill_trigger"] = "every_n_rounds"
                elif trigger == "low_hp":
                    card["skill_trigger"] = "hp_below_pct"
                elif trigger.startswith("round_"):
                    card["skill_trigger"] = "round_n"
                elif trigger == "濒死":
                    card["skill_trigger"] = "on_death"
            elif trigger not in valid_triggers:
                card["skill_trigger"] = "passive"

            # 确保 skill_param 与 trigger 配合
            if card["skill_trigger"] in ("every_n_rounds", "round_n", "hp_below_pct"):
                if not card.get("skill_param") or float(card.get("skill_param", 0)) <= 0:
                    if card["skill_trigger"] == "every_n_rounds":
                        card["skill_param"] = 3
                    elif card["skill_trigger"] == "round_n":
                        card["skill_param"] = 3
                    elif card["skill_trigger"] == "hp_below_pct":
                        card["skill_param"] = 30
            else:
                card["skill_param"] = 0

            # category 校验
            if not card.get("category"):
                card["category"] = body.category or "其他动漫"
            card.setdefault("image", f"ai-{name[:10]}")

            validated.append(card)

        return {
            "success": True,
            "generated": validated,
            "count": len(validated),
            "skipped_duplicates": len(generated) - len(validated)
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI返回的数据格式无法解析")
    except Exception as e:
        print(f"[AI Generate Error] {e}")
        raise HTTPException(status_code=500, detail=f"AI生成失败: {str(e)}")


@router.post("/admin/batch-save-cards")
def batch_save_cards(token: str, body: BatchSaveRequest, db: Session = Depends(get_db)):
    """批量保存AI生成的卡片（含名称唯一性校验）"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")

    existing_names = set(r[0] for r in db.query(CardTemplate.name).all())
    saved = []
    skipped = []

    for card_data in body.cards:
        name = card_data.get("name", "").strip()
        if not name:
            skipped.append({"name": "(空名称)", "reason": "名称为空"})
            continue
        if name in existing_names:
            skipped.append({"name": name, "reason": "名称已存在"})
            continue

        template = CardTemplate(
            name=name,
            rarity=card_data["rarity"],
            base_stars=card_data.get("base_stars", 2),
            base_attack=card_data["base_attack"],
            base_defense=card_data["base_defense"],
            base_hp=card_data["base_hp"],
            speed=card_data.get("speed", 100),
            skill_name=card_data.get("skill_name"),
            skill_desc=card_data.get("skill_desc"),
            skill_type=card_data.get("skill_type"),
            skill_value=card_data.get("skill_value"),
            skill_trigger=card_data.get("skill_trigger"),
            skill_param=card_data.get("skill_param", 0),
            category=card_data.get("category", "其他动漫"),
            image=card_data.get("image", "card-default")
        )
        db.add(template)
        existing_names.add(name)
        saved.append(name)

    db.commit()

    return {
        "success": True,
        "message": f"成功保存 {len(saved)} 张卡片" + (f"，跳过 {len(skipped)} 张重复" if skipped else ""),
        "saved_names": saved,
        "skipped": skipped
    }


# ===== AI 图片生成 =====

@router.post("/admin/ai-generate-image")
async def ai_generate_image(token: str, body: ImageGenerateRequest, db: Session = Depends(get_db)):
    """使用AI生成单张图片"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")

    provider = db.query(AIProvider).filter(
        AIProvider.id == body.provider_id,
        AIProvider.is_active == True,
        AIProvider.provider_type == "image",
    ).first()
    if not provider:
        raise HTTPException(status_code=400, detail="图片AI提供商不存在或未启用")

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            base_url=provider.base_url,
            api_key=provider.api_key
        )

        # Agnes 需要 extra_body，但某些新模型不支持 response_format
        extra_body = {}
        if "agnes" in provider.base_url.lower():
            extra_body["response_format"] = "url"
        extra_body_options = [extra_body, {}]

        # 不同图片API支持的尺寸不同，按优先级尝试
        size_options = [body.size, "1024x1024", "2048x2048", "1664x2496"]
        response = None
        last_err = None
        for eb in extra_body_options:
            if response:
                break
            for sz in size_options:
                try:
                    response = await client.images.generate(
                        model=provider.model,
                        prompt=body.prompt,
                        size=sz,
                        n=body.n,
                        **eb,
                    )
                    break
                except Exception as e:
                    last_err = e
                    err_str = str(e)
                    if "size" in err_str.lower() or "Size invalid" in err_str:
                        continue
                    if "response_format" in err_str or "UnsupportedParams" in err_str:
                        break  # 换extra_body策略
                    raise e
        if not response:
            raise last_err or HTTPException(status_code=500, detail="图片生成失败")

        images = []
        for item in response.data:
            # 下载图片到本地存储
            local_path = download_image_to_local(item.url, "generated")
            if local_path:
                images.append({
                    "url": local_path,
                    "original_url": item.url,
                    "revised_prompt": getattr(item, "revised_prompt", None)
                })
            else:
                # 下载失败时回退到外部URL
                images.append({
                    "url": item.url,
                    "revised_prompt": getattr(item, "revised_prompt", None)
                })

        return {
            "success": True,
            "images": images,
            "count": len(images)
        }

    except Exception as e:
        print(f"[AI Image Error] {e}")
        raise HTTPException(status_code=500, detail=f"图片生成失败: {str(e)}")


@router.post("/admin/ai-generate-card-images")
async def ai_generate_card_images(
    token: str,
    body: CardImageGenerateRequest,
    db: Session = Depends(get_db)
):
    """为指定卡片模板批量生成角色图片（不传template_ids则为所有无图卡片生成）"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")

    image_provider_id = body.image_provider_id
    template_ids = body.template_ids

    provider = db.query(AIProvider).filter(
        AIProvider.id == image_provider_id,
        AIProvider.is_active == True,
        AIProvider.provider_type == "image",
    ).first()
    if not provider:
        raise HTTPException(status_code=400, detail="图片AI提供商不存在或未启用")

    # 查找需要生成图片的卡片
    query = db.query(CardTemplate)
    if template_ids:
        query = query.filter(CardTemplate.id.in_(template_ids))
    else:
        # 默认为所有 image 以 "ai-" 开头或为空的卡片生成
        query = query.filter(
            (CardTemplate.image == None) |
            (CardTemplate.image == "") |
            (CardTemplate.image.like("ai-%"))
        )
    templates = query.all()

    if not templates:
        return {"success": True, "message": "没有需要生成图片的卡片", "updated": 0}

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            base_url=provider.base_url,
            api_key=provider.api_key
        )

        extra_body = {}
        if "agnes" in provider.base_url.lower():
            extra_body["response_format"] = "url"
        # 某些模型不支持 response_format，准备无extra_body的回退
        extra_body_options = [extra_body, {}]

        updated = 0
        errors = []
        # 不同图片API支持的尺寸不同，按优先级尝试
        size_options = ["1024x1024", "2048x2048", "1664x2496", "1536x2752"]

        # 风格映射
        style_map = {
            "default": "精致动漫角色立绘, 全身, 战斗姿态, 高质量, 色彩鲜明, 竖版构图",
            "realistic": "真人写实风格, 高度细节, 摄影级光影, 超写实人物立绘, 全身, 竖版构图",
            "anime": "日漫风格, 二次元动漫角色, 鲜艳色彩, 精致线条, 全身, 战斗姿态, 竖版构图",
        }
        style_desc = style_map.get(body.style, style_map["default"])
        if body.style == "custom" and body.custom_style:
            style_desc = body.custom_style

        for tpl in templates:
            prompt = (
                f"角色卡牌立绘: {tpl.name}({tpl.category}系列), "
                f"稀有度{tpl.rarity}, 技能: {tpl.skill_name or '未知'}. "
                f"风格: {style_desc}"
            )
            if body.include_text:
                prompt += (
                    f". 图片底部中央包含卡片名称文字\"{tpl.name}\", "
                    f"使用简体中文, 字体清晰, 白色粗体描边, 位置固定在底部居中, 不可乱码"
                )
            success = False
            last_err = None
            for eb in extra_body_options:
                if success:
                    break
                for sz in size_options:
                    try:
                        response = await client.images.generate(
                            model=provider.model,
                            prompt=prompt,
                            size=sz,
                            n=1,
                            **eb,
                        )
                        if response.data and response.data[0].url:
                            # 下载图片到本地存储，避免外部链接过期
                            local_path = download_image_to_local(response.data[0].url, tpl.name)
                            if local_path:
                                tpl.image = local_path
                            else:
                                # 下载失败时回退到外部URL
                                tpl.image = response.data[0].url
                            updated += 1
                            success = True
                            break
                    except Exception as e:
                        last_err = e
                        err_str = str(e)
                        if "size" in err_str.lower() or "Size invalid" in err_str:
                            continue
                        if "response_format" in err_str or "UnsupportedParams" in err_str:
                            break  # 换extra_body策略
                        break  # 非尺寸/参数错误，不重试
            if not success and last_err:
                errors.append({"name": tpl.name, "error": str(last_err)})

        db.commit()

        return {
            "success": True,
            "message": f"成功为 {updated}/{len(templates)} 张卡片生成图片",
            "updated": updated,
            "total": len(templates),
            "errors": errors[:10]  # 只返回前10个错误
        }

    except Exception as e:
        print(f"[AI Card Images Error] {e}")
        raise HTTPException(status_code=500, detail=f"批量生成图片失败: {str(e)}")


# ===== AI 提供商管理 =====

@router.get("/admin/ai-providers")
def list_ai_providers(token: str, provider_type: str = None, db: Session = Depends(get_db)):
    """获取AI提供商列表（可按类型筛选 text/image）"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")

    query = db.query(AIProvider).order_by(AIProvider.id)
    if provider_type:
        query = query.filter(AIProvider.provider_type == provider_type)
    providers = query.all()

    return {
        "success": True,
        "providers": [
            {
                "id": p.id,
                "name": p.name,
                "base_url": p.base_url,
                "model": p.model,
                "api_key": p.api_key[:8] + "..." + p.api_key[-4:] if len(p.api_key) > 12 else "***",
                "api_key_full": p.api_key,
                "provider_type": p.provider_type or "text",
                "is_active": p.is_active,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in providers
        ]
    }


@router.post("/admin/ai-providers")
def create_ai_provider(token: str, body: AIProviderCreate, db: Session = Depends(get_db)):
    """创建AI提供商"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")

    provider = AIProvider(
        name=body.name,
        base_url=body.base_url,
        model=body.model,
        api_key=body.api_key,
        provider_type=body.provider_type,
        is_active=body.is_active,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return {"success": True, "message": f"AI提供商「{provider.name}」创建成功", "id": provider.id}


@router.put("/admin/ai-providers/{provider_id}")
def update_ai_provider(provider_id: int, token: str, body: AIProviderUpdate, db: Session = Depends(get_db)):
    """更新AI提供商"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")

    provider = db.query(AIProvider).filter(AIProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="AI提供商不存在")

    if body.name is not None:
        provider.name = body.name
    if body.base_url is not None:
        provider.base_url = body.base_url
    if body.model is not None:
        provider.model = body.model
    if body.api_key is not None:
        provider.api_key = body.api_key
    if body.provider_type is not None:
        provider.provider_type = body.provider_type
    if body.is_active is not None:
        provider.is_active = body.is_active

    db.commit()
    return {"success": True, "message": f"AI提供商「{provider.name}」更新成功"}


@router.delete("/admin/ai-providers/{provider_id}")
def delete_ai_provider(provider_id: int, token: str, db: Session = Depends(get_db)):
    """删除AI提供商"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")

    provider = db.query(AIProvider).filter(AIProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="AI提供商不存在")

    db.delete(provider)
    db.commit()
    return {"success": True, "message": f"AI提供商「{provider.name}」已删除"}
