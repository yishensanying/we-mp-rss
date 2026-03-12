import uvicorn
from core.config import cfg
from core.print import print_warning, print_success
import threading
from driver.auth import *


if __name__ == '__main__':
    print("环境变量:")
    for k,v in os.environ.items():
        print(f"{k}={v}")
    # 可选：仅在显式指定 --init=True 时创建默认用户
    if getattr(cfg, "args", None) and getattr(cfg.args, "init", "False") == "True":
        import init_sys as init
        init.init()

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
    print("启动服务器")
    AutoReload=cfg.get("server.auto_reload",False)
    thread=cfg.get("server.threads",1)
    uvicorn.run("web:app", host="0.0.0.0", port=int(cfg.get("port",8001)),
            reload=AutoReload,
            reload_dirs=['core','web_ui'],
            reload_excludes=['static','web_ui','data'], 
            workers=thread,
            )
    pass