"""
数据库管理路由 - 管理后台配置数据库连接、测试、迁移
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db, test_db_connection, get_current_db_info, migrate_data_to_new_db, Base, engine
from config_db import (
    list_db_configs, add_db_config, update_db_config, delete_db_config,
    set_active_db_config, get_active_db_config
)
from utils import verify_admin_token

router = APIRouter()


class DbConfigCreate(BaseModel):
    name: str
    db_type: str  # sqlite / mysql
    host: str = ""
    port: int = 0
    database: str = ""
    username: str = ""
    password: str = ""


class DbConfigUpdate(BaseModel):
    name: Optional[str] = None
    db_type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class TestConnectionRequest(BaseModel):
    db_type: str
    host: str = ""
    port: int = 0
    database: str = ""
    username: str = ""
    password: str = ""


class MigrateRequest(BaseModel):
    target_config_id: int


@router.get("/admin/db-configs")
def list_configs(token: str, db: Session = Depends(get_db)):
    """获取所有数据库配置"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")
    configs = list_db_configs()
    current = get_current_db_info()
    return {
        "success": True,
        "configs": configs,
        "current": current,
    }


@router.post("/admin/db-configs")
def create_config(token: str, body: DbConfigCreate, db: Session = Depends(get_db)):
    """添加数据库配置"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")
    config_id = add_db_config(
        name=body.name, db_type=body.db_type,
        host=body.host, port=body.port, database=body.database,
        username=body.username, password=body.password
    )
    return {"success": True, "message": f"配置「{body.name}」创建成功", "id": config_id}


@router.put("/admin/db-configs/{config_id}")
def update_config(config_id: int, token: str, body: DbConfigUpdate, db: Session = Depends(get_db)):
    """更新数据库配置"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")
    update_db_config(config_id, **body.dict(exclude_none=True))
    return {"success": True, "message": "配置更新成功"}


@router.delete("/admin/db-configs/{config_id}")
def delete_config(config_id: int, token: str, db: Session = Depends(get_db)):
    """删除数据库配置"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")
    delete_db_config(config_id)
    return {"success": True, "message": "配置已删除"}


@router.post("/admin/db-test-connection")
def test_connection(token: str, body: TestConnectionRequest, db: Session = Depends(get_db)):
    """测试数据库连接"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")
    success, message = test_db_connection(
        db_type=body.db_type, host=body.host, port=body.port,
        database=body.database, username=body.username, password=body.password
    )
    return {"success": success, "message": message}


@router.post("/admin/db-migrate")
def migrate_data(token: str, body: MigrateRequest, db: Session = Depends(get_db)):
    """迁移数据到新的数据库"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")

    # 获取目标配置
    configs = list_db_configs()
    target = None
    for c in configs:
        if c["id"] == body.target_config_id:
            target = c
            break
    if not target:
        raise HTTPException(status_code=404, detail="目标数据库配置不存在")

    # 先测试连接
    success, msg = test_db_connection(
        db_type=target["db_type"], host=target.get("host", ""),
        port=target.get("port", 0), database=target.get("database", ""),
        username=target.get("username", ""), password=target.get("password", "")
    )
    if not success:
        raise HTTPException(status_code=400, detail=f"目标数据库连接失败: {msg}")

    # 执行迁移
    success, msg, table_count, row_count = migrate_data_to_new_db(target)
    if not success:
        raise HTTPException(status_code=500, detail=msg)

    # 设置为活跃配置
    set_active_db_config(body.target_config_id)

    return {
        "success": True,
        "message": f"{msg}，切换成功！请重启服务使新数据库生效。",
        "table_count": table_count,
        "row_count": row_count,
        "need_restart": True,
    }


@router.get("/admin/db-current")
def get_current_db(token: str, db: Session = Depends(get_db)):
    """获取当前数据库信息"""
    if not verify_admin_token(token, db):
        raise HTTPException(status_code=401, detail="无效的管理员token")
    info = get_current_db_info()
    # 不返回密码
    safe_info = {k: v for k, v in info.items() if k != "password"}
    return {"success": True, "current": safe_info}
