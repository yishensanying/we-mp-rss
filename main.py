import sys
import asyncio

# Windows 需要使用 ProactorEventLoop 以支持 Playwright 子进程
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from core.config import cfg
if cfg.get("redis.server.enabled", False):
        from tools.redis_server import run_redis_server
        run_redis_server(config_path="config.yaml")
import uvicorn
from core.print import print_warning, print_success
import threading
import os


if __name__ == '__main__':
    import shutil
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    app_env = os.environ.get("APP_ENV", "prod")
    if app_env != 'dev':
        try:
            from core.disconf import init_disconf
            disconf_result = init_disconf()
            if disconf_result:
                logging.info("成功从Disconf加载配置")
            elif os.environ.get("DISCONF_LOCAL_MODE") == "true":
                logging.info("使用本地配置模式，跳过Disconf远程加载")
            else:
                logging.warning("无法从Disconf加载配置，将尝试使用系统环境变量或本地配置文件")

            disconf_config = os.path.join("disconf", "download", "config.yaml")
            if os.path.exists(disconf_config):
                shutil.copy2(disconf_config, "config.yaml")
                logging.info("已从Disconf更新config.yaml")
                cfg.reload()
        except Exception as e:
            logging.warning(f"Disconf初始化失败: {e}")

    # 配置就绪后，重建依赖 cfg 的组件
    from core.redis_client import redis_client
    redis_client.reconnect()

    from core.db import DB
    from core.config import get_db_url, get_db_connect_args
    DB.init(get_db_url(), get_db_connect_args())

    print("环境变量:")
    for k,v in os.environ.items():
        print(f"{k}={v}")
    # 可选：仅在显式指定 --init=True 时创建默认用户
    if getattr(cfg, "args", None) and getattr(cfg.args, "init", "False") == "True":
        import init_sys as init
        init.init()

    from driver.auth import start_auth_service
    start_auth_service()

    if cfg.args.job == "True" and cfg.get("server.enable_job", False):
        from jobs import start_job
        threading.Thread(target=start_job, daemon=False).start()
        print_success("已开启定时任务")
    else:
        print_warning("未开启定时任务")
    if cfg.get("gather.content_auto_check", False):
        from jobs import start_fix_article
        start_fix_article()
        print_success("已开启自动修正文章任务")
    else:
        print_warning("未开启自动修正文章任务")
    
    # 启动文章统计定时刷新任务
    if cfg.get("article_stats_refresh_enabled", True):  # 默认启用
        from jobs.mps import start_article_stats_refresh
        start_article_stats_refresh()
    else:
        print_warning("文章统计定时刷新任务未启用")
    
    print("启动服务器")
    AutoReload=cfg.get("server.auto_reload",False)
    thread=cfg.get("server.threads",1)
    reload_dirs = ["apis", "core", "driver", "jobs", "schemas", "tools", "views", "web_ui"]
    
    # Windows 上禁用 reload 模式，因为会导致事件循环问题
    if sys.platform == 'win32' and AutoReload:
        print_warning("Windows 平台上禁用 reload 模式以确保 Playwright 正常工作")
        AutoReload = False
    
    # Windows 上使用自定义配置确保 ProactorEventLoop
    if sys.platform == 'win32':
        # 使用 uvicorn 的 Config 和 Server 类来控制事件循环
        config = uvicorn.Config(
            "web:app",
            host="0.0.0.0",
            port=int(cfg.get("port", 8001)),
            reload=False,
            reload_dirs=reload_dirs,
            reload_excludes=['static', 'data', 'node_modules', '*.pnpm*'],
            workers=thread,
        )
        server = uvicorn.Server(config)
        
        # 确保使用 ProactorEventLoop
        if not isinstance(asyncio.get_event_loop(), asyncio.ProactorEventLoop):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        asyncio.run(server.serve())
    else:
        uvicorn.run("web:app", host="0.0.0.0", port=int(cfg.get("port",8001)),
                reload=AutoReload,
                reload_dirs=reload_dirs,
                reload_excludes=['static','data','node_modules','*.pnpm*'],
                workers=thread,
                )
    pass
