import threading
import asyncio
from core.print import print_warning
from driver.base import WX_InterFace
import os
import portalocker
from core.task import TaskScheduler
from driver.success import Success
from core.config import cfg

def auth():
    def run_auth():
        wx = WX_InterFace()
        # 在新的事件循环中运行异步方法
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(wx.switch_account())
        finally:
            loop.close()

    thread = threading.Thread(target=run_auth)
    thread.start()
    thread.join()  # 可选：等待完成
def start_auth_service():    
    # 启动时是否执行微信预鉴权，默认开启，可通过环境变量关闭
    enable_startup_auth = str(os.getenv("WE_RSS.STARTUP_AUTH", "True")).lower() == "true"
    is_web_auth = bool(cfg.get("server.auth_web", False))

    # Web认证模式走浏览器流程，启动时不应调用wx_api的网络鉴权
    if enable_startup_auth and not is_web_auth:
        from driver.wx_api import login_with_token
        try:
            login_with_token()
        except Exception as e:
            # 微信外部网络异常不应阻塞系统主服务启动
            print_warning(f"启动时微信token鉴权失败，已跳过: {e}")
    else:
        print_warning("已跳过启动阶段微信预鉴权")
    if str(os.getenv('WE_RSS.AUTH',False))=="True":
        print_warning("启动授权定时任务")
        auth_task=TaskScheduler()
        auth_task.clear_all_jobs()
        print("是否开启调试模式:",str(os.getenv('DEBUG',False)))
        if str(os.getenv('DEBUG',False))=="True":
            auth_task.add_cron_job(auth, "*/10 * * * *",tag="授权定时更新")
        else:
            auth_task.add_cron_job(auth, "0 0 */1 * *",tag="授权定时更新")
        auth_task.start()