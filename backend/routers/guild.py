"""
公会路由
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Guild, GuildMember, GuildApplication, GuildCheckIn, User
from schemas import GuildCreateRequest, GuildDepositRequest, GuildDistributeRequest
from utils import get_user_by_token

router = APIRouter()

GUILD_CREATE_COST = 500  # 创建公会花费
CHECK_IN_REWARD = 50  # 每日签到奖励卡金


def _guild_brief(guild, db: Session):
    """公会简要信息（含成员数、会长名）"""
    member_count = db.query(GuildMember).filter(GuildMember.guild_id == guild.id).count()
    leader = db.query(User).filter(User.id == guild.leader_id).first()
    return {
        "id": guild.id,
        "name": guild.name,
        "description": guild.description,
        "fund": guild.fund,
        "leader_id": guild.leader_id,
        "leader_name": leader.username if leader else "",
        "member_count": member_count,
        "created_at": guild.created_at.isoformat() if guild.created_at else None,
    }


# ===== 静态路径（必须在 /guilds/{guild_id} 之前注册） =====

@router.post("/guilds/create")
def create_guild(body: GuildCreateRequest, token: str, db: Session = Depends(get_db)):
    """创建公会（花费500卡金，创建者成为会长）"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    name = body.name.strip() if body.name else ""
    if not name:
        raise HTTPException(status_code=400, detail="公会名称不能为空")

    if user.card_gold < GUILD_CREATE_COST:
        raise HTTPException(status_code=400, detail=f"创建公会需要{GUILD_CREATE_COST}卡金")

    if db.query(Guild).filter(Guild.name == name).first():
        raise HTTPException(status_code=400, detail="公会名称已存在")

    if db.query(GuildMember).filter(GuildMember.user_id == user.id).first():
        raise HTTPException(status_code=400, detail="你已经加入了一个公会")

    user.card_gold -= GUILD_CREATE_COST

    guild = Guild(
        name=name,
        leader_id=user.id,
        description=body.description,
        fund=0,
    )
    db.add(guild)
    db.flush()  # 获取自增 id

    member = GuildMember(
        guild_id=guild.id,
        user_id=user.id,
        role="leader",
    )
    db.add(member)
    db.commit()
    db.refresh(guild)

    return {
        "success": True,
        "message": "公会创建成功",
        "cost": GUILD_CREATE_COST,
        "card_gold": user.card_gold,
        "guild": _guild_brief(guild, db),
    }


@router.get("/guilds/list")
def list_guilds(db: Session = Depends(get_db)):
    """获取所有公会列表"""
    guilds = db.query(Guild).order_by(Guild.created_at.desc()).all()
    return {
        "success": True,
        "guilds": [_guild_brief(g, db) for g in guilds],
    }


@router.get("/guilds/search")
def search_guilds(name: str = "", db: Session = Depends(get_db)):
    """按名称搜索公会"""
    query = db.query(Guild)
    keyword = name.strip() if name else ""
    if keyword:
        query = query.filter(Guild.name.like(f"%{keyword}%"))
    guilds = query.order_by(Guild.created_at.desc()).all()
    return {
        "success": True,
        "keyword": name,
        "guilds": [_guild_brief(g, db) for g in guilds],
    }


@router.get("/guilds/my")
def my_guild(token: str, db: Session = Depends(get_db)):
    """获取当前用户所在公会"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    member = db.query(GuildMember).filter(GuildMember.user_id == user.id).first()
    if not member:
        return {"success": True, "guild": None, "role": None}

    guild = db.query(Guild).filter(Guild.id == member.guild_id).first()
    return {
        "success": True,
        "role": member.role,
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        "guild": _guild_brief(guild, db) if guild else None,
    }


@router.get("/guilds/ranking")
def guild_ranking(limit: int = 20, db: Session = Depends(get_db)):
    """公会资金排行"""
    guilds = db.query(Guild).order_by(Guild.fund.desc()).limit(limit).all()
    return {
        "success": True,
        "ranking": [
            {
                "rank": i + 1,
                **_guild_brief(g, db),
            }
            for i, g in enumerate(guilds)
        ],
    }


@router.post("/guilds/check-in")
def guild_check_in(token: str, db: Session = Depends(get_db)):
    """每日签到（获得50卡金，每天一次）"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    member = db.query(GuildMember).filter(GuildMember.user_id == user.id).first()
    if not member:
        raise HTTPException(status_code=400, detail="你还没有加入公会")

    today = date.today()
    existing = db.query(GuildCheckIn).filter(
        GuildCheckIn.user_id == user.id,
        GuildCheckIn.check_in_date == today,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="今天已经签到过了")

    user.card_gold += CHECK_IN_REWARD
    record = GuildCheckIn(
        guild_id=member.guild_id,
        user_id=user.id,
        check_in_date=today,
        reward_claimed=True,
    )
    db.add(record)
    db.commit()

    return {
        "success": True,
        "message": "签到成功",
        "reward": CHECK_IN_REWARD,
        "card_gold": user.card_gold,
    }


@router.get("/guilds/check-in/status")
def check_in_status(token: str, db: Session = Depends(get_db)):
    """查询今日签到状态"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    member = db.query(GuildMember).filter(GuildMember.user_id == user.id).first()
    if not member:
        return {"success": True, "in_guild": False, "checked_in": False}

    today = date.today()
    existing = db.query(GuildCheckIn).filter(
        GuildCheckIn.user_id == user.id,
        GuildCheckIn.check_in_date == today,
    ).first()
    return {
        "success": True,
        "in_guild": True,
        "checked_in": existing is not None,
    }


@router.post("/guilds/leave")
def leave_guild(token: str, db: Session = Depends(get_db)):
    """离开公会（会长不能离开，需解散）"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    member = db.query(GuildMember).filter(GuildMember.user_id == user.id).first()
    if not member:
        raise HTTPException(status_code=400, detail="你还没有加入公会")

    if member.role == "leader":
        raise HTTPException(status_code=400, detail="会长不能直接离开，请使用解散公会")

    db.delete(member)
    db.commit()

    return {"success": True, "message": "已离开公会"}


@router.post("/guilds/disband")
def disband_guild(token: str, db: Session = Depends(get_db)):
    """解散公会（仅会长）"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    member = db.query(GuildMember).filter(GuildMember.user_id == user.id).first()
    if not member:
        raise HTTPException(status_code=400, detail="你还没有加入公会")

    if member.role != "leader":
        raise HTTPException(status_code=403, detail="只有会长才能解散公会")

    guild = db.query(Guild).filter(Guild.id == member.guild_id).first()
    if not guild:
        raise HTTPException(status_code=404, detail="公会不存在")

    guild_name = guild.name
    db.delete(guild)  # 级联删除成员/申请/签到
    db.commit()

    return {"success": True, "message": f"公会「{guild_name}」已解散"}


@router.post("/guilds/applications/{app_id}/approve")
def approve_application(app_id: int, token: str, db: Session = Depends(get_db)):
    """批准申请（仅会长）"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    application = db.query(GuildApplication).filter(GuildApplication.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="申请不存在")

    guild = db.query(Guild).filter(Guild.id == application.guild_id).first()
    if not guild or guild.leader_id != user.id:
        raise HTTPException(status_code=403, detail="只有会长才能批准申请")

    if application.status != "pending":
        raise HTTPException(status_code=400, detail="该申请已处理")

    if db.query(GuildMember).filter(GuildMember.user_id == application.user_id).first():
        raise HTTPException(status_code=400, detail="该玩家已加入公会")

    application.status = "approved"
    member = GuildMember(
        guild_id=application.guild_id,
        user_id=application.user_id,
        role="member",
    )
    db.add(member)
    db.commit()

    return {"success": True, "message": "已批准申请"}


@router.post("/guilds/applications/{app_id}/reject")
def reject_application(app_id: int, token: str, db: Session = Depends(get_db)):
    """拒绝申请（仅会长）"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    application = db.query(GuildApplication).filter(GuildApplication.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="申请不存在")

    guild = db.query(Guild).filter(Guild.id == application.guild_id).first()
    if not guild or guild.leader_id != user.id:
        raise HTTPException(status_code=403, detail="只有会长才能拒绝申请")

    if application.status != "pending":
        raise HTTPException(status_code=400, detail="该申请已处理")

    application.status = "rejected"
    db.commit()

    return {"success": True, "message": "已拒绝申请"}


# ===== 动态路径 /guilds/{guild_id} =====

@router.get("/guilds/{guild_id}")
def guild_detail(guild_id: int, db: Session = Depends(get_db)):
    """获取公会详情（成员、资金等）"""
    guild = db.query(Guild).filter(Guild.id == guild_id).first()
    if not guild:
        raise HTTPException(status_code=404, detail="公会不存在")

    members = db.query(GuildMember).filter(GuildMember.guild_id == guild_id).all()
    user_ids = [m.user_id for m in members]
    users = {
        u.id: u
        for u in db.query(User).filter(User.id.in_(user_ids)).all()
    } if user_ids else {}

    member_list = []
    for m in members:
        u = users.get(m.user_id)
        member_list.append({
            "user_id": m.user_id,
            "username": u.username if u else "",
            "role": m.role,
            "joined_at": m.joined_at.isoformat() if m.joined_at else None,
        })

    role_order = {"leader": 0, "vice_leader": 1, "member": 2}
    member_list.sort(key=lambda x: (role_order.get(x["role"], 3), x["user_id"]))

    leader = users.get(guild.leader_id)

    return {
        "success": True,
        "guild": {
            "id": guild.id,
            "name": guild.name,
            "description": guild.description,
            "fund": guild.fund,
            "leader_id": guild.leader_id,
            "leader_name": leader.username if leader else "",
            "member_count": len(members),
            "created_at": guild.created_at.isoformat() if guild.created_at else None,
        },
        "members": member_list,
    }


@router.post("/guilds/{guild_id}/apply")
def apply_guild(guild_id: int, token: str, db: Session = Depends(get_db)):
    """申请加入公会"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    guild = db.query(Guild).filter(Guild.id == guild_id).first()
    if not guild:
        raise HTTPException(status_code=404, detail="公会不存在")

    if db.query(GuildMember).filter(GuildMember.user_id == user.id).first():
        raise HTTPException(status_code=400, detail="你已经加入了一个公会")

    pending = db.query(GuildApplication).filter(
        GuildApplication.guild_id == guild_id,
        GuildApplication.user_id == user.id,
        GuildApplication.status == "pending",
    ).first()
    if pending:
        raise HTTPException(status_code=400, detail="你已有待处理的申请")

    application = GuildApplication(
        guild_id=guild_id,
        user_id=user.id,
        status="pending",
    )
    db.add(application)
    db.commit()

    return {"success": True, "message": "申请已提交"}


@router.post("/guilds/{guild_id}/cancel-apply")
def cancel_apply(guild_id: int, token: str, db: Session = Depends(get_db)):
    """取消申请"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    application = db.query(GuildApplication).filter(
        GuildApplication.guild_id == guild_id,
        GuildApplication.user_id == user.id,
        GuildApplication.status == "pending",
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="没有待处理的申请")

    db.delete(application)
    db.commit()

    return {"success": True, "message": "已取消申请"}


@router.get("/guilds/{guild_id}/applications")
def list_applications(guild_id: int, token: str, db: Session = Depends(get_db)):
    """查看待处理申请（仅会长）"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    guild = db.query(Guild).filter(Guild.id == guild_id).first()
    if not guild:
        raise HTTPException(status_code=404, detail="公会不存在")

    if guild.leader_id != user.id:
        raise HTTPException(status_code=403, detail="只有会长才能查看申请")

    apps = db.query(GuildApplication).filter(
        GuildApplication.guild_id == guild_id,
        GuildApplication.status == "pending",
    ).order_by(GuildApplication.applied_at.desc()).all()

    user_ids = [a.user_id for a in apps]
    users = {
        u.id: u
        for u in db.query(User).filter(User.id.in_(user_ids)).all()
    } if user_ids else {}

    return {
        "success": True,
        "applications": [
            {
                "id": a.id,
                "user_id": a.user_id,
                "username": users[a.user_id].username if a.user_id in users else "",
                "status": a.status,
                "applied_at": a.applied_at.isoformat() if a.applied_at else None,
            }
            for a in apps
        ],
    }


@router.post("/guilds/{guild_id}/deposit")
def deposit_fund(guild_id: int, body: GuildDepositRequest, token: str, db: Session = Depends(get_db)):
    """向公会资金存入卡金（仅成员）"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    guild = db.query(Guild).filter(Guild.id == guild_id).first()
    if not guild:
        raise HTTPException(status_code=404, detail="公会不存在")

    member = db.query(GuildMember).filter(
        GuildMember.guild_id == guild_id,
        GuildMember.user_id == user.id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="只有公会成员才能存入资金")

    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="存入金额必须大于0")

    if user.card_gold < body.amount:
        raise HTTPException(status_code=400, detail="卡金不足")

    user.card_gold -= body.amount
    guild.fund += body.amount
    db.commit()

    return {
        "success": True,
        "message": "存入成功",
        "amount": body.amount,
        "card_gold": user.card_gold,
        "fund": guild.fund,
    }


@router.post("/guilds/{guild_id}/distribute")
def distribute_fund(guild_id: int, body: GuildDistributeRequest, token: str, db: Session = Depends(get_db)):
    """分配公会资金给成员（仅会长）"""
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    guild = db.query(Guild).filter(Guild.id == guild_id).first()
    if not guild:
        raise HTTPException(status_code=404, detail="公会不存在")

    if guild.leader_id != user.id:
        raise HTTPException(status_code=403, detail="只有会长才能分配资金")

    if not body.member_ids:
        raise HTTPException(status_code=400, detail="请选择接收成员")

    if len(body.member_ids) != len(body.amounts):
        raise HTTPException(status_code=400, detail="成员与金额数量不一致")

    if len(set(body.member_ids)) != len(body.member_ids):
        raise HTTPException(status_code=400, detail="成员不能重复")

    for amt in body.amounts:
        if amt < 0:
            raise HTTPException(status_code=400, detail="分配金额不能为负")

    total = sum(body.amounts)
    if total <= 0:
        raise HTTPException(status_code=400, detail="分配总额必须大于0")

    if total > guild.fund:
        raise HTTPException(status_code=400, detail="公会资金不足")

    # 校验所有目标都是该公会成员
    for mid in body.member_ids:
        if not db.query(GuildMember).filter(
            GuildMember.guild_id == guild_id,
            GuildMember.user_id == mid,
        ).first():
            raise HTTPException(status_code=400, detail=f"用户 {mid} 不是该公会成员")

    # 执行分配
    for mid, amt in zip(body.member_ids, body.amounts):
        target = db.query(User).filter(User.id == mid).first()
        if target:
            target.card_gold += amt

    guild.fund -= total
    db.commit()

    return {
        "success": True,
        "message": "分配成功",
        "total": total,
        "fund": guild.fund,
    }
