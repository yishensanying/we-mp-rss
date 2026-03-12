from core.models.user import User
from core.db import Db, DB
from core.auth import pwd_context
import os
from core.print import print_info


def init_user(_db: Db):
    """
    初始化默认管理员用户。
    仅负责插入用户，不做建表或迁移，表结构需外部提前准备。
    """
    try:
        username = os.getenv("USERNAME", "admin")
        password = os.getenv("PASSWORD", "admin@123")
        session = _db.get_session()

        # 如果已存在用户 0 或同名用户，则不重复创建
        existing = session.query(User).filter(
            (User.id == "0") | (User.username == username)
        ).first()
        if existing:
            return

        session.add(
            User(
                id="0",
                username=username,
                password_hash=pwd_context.hash(password),
            )
        )
        session.commit()
        print_info(f"初始化用户成功, 请使用以下凭据登录：{username}")
    except Exception:
        # 初始化失败时静默略过，避免影响其它流程
        session.rollback()
    finally:
        session.close()


def init():
    """对外提供的初始化入口：仅创建默认用户。"""
    init_user(DB)


if __name__ == "__main__":
    init()

