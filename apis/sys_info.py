import time
from fastapi import APIRouter, Depends
from typing import Dict, Any
from core.auth import get_current_user_or_ak
from .base import success_response, error_response
from driver.token import wx_cfg
from jobs.mps import TaskQueue
from driver.success import getLoginInfo, getStatus
from .ver import API_VERSION
from core.ver import VERSION as CORE_VERSION

router = APIRouter(prefix="/sys", tags=["系统信息"])

# 记录服务器启动时间（仅用来提供简单运行时长信息）
_START_TIME = time.time()


@router.get("/info", summary="获取系统信息")
async def get_system_info(
    current_user: dict = Depends(get_current_user_or_ak)
) -> Dict[str, Any]:
    """获取精简后的系统信息，主要用于前端判断登录与授权状态。"""
    try:
        wx_cfg.reload()
        system_info = {
            "api_version": API_VERSION,
            "core_version": CORE_VERSION,
            "uptime": round(time.time() - _START_TIME, 2),
            "wx": {
                "token": wx_cfg.get("token", ""),
                "expiry_time": wx_cfg.get("expiry.expiry_time", "") if getStatus() else "",
                "info": getLoginInfo(),
                "login": getStatus(),
            },
            "queue": TaskQueue.get_queue_info(),
        }
        return success_response(data=system_info)
    except Exception as e:
        return error_response(
            code=50001,
            message=f"获取系统信息失败: {str(e)}"
        )