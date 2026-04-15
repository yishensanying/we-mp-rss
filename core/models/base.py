import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, DateTime,Date,ForeignKey,Boolean,Enum,Table,JSON as SAJSON
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.types import TypeDecorator
from core.config import cfg, get_db_url

_db_url = get_db_url()
if _db_url.startswith("mysql"):
    from sqlalchemy.dialects.mysql import MEDIUMTEXT as Text
elif _db_url.startswith("oracle"):
    from sqlalchemy import Text  # Oracle: Text -> CLOB
else:
    from sqlalchemy import Text


class JSON(TypeDecorator):
    """
    跨数据库 JSON 类型封装：
    - Oracle: 使用 Text(CLOB) 存储，手动做 JSON 序列化/反序列化
    - 其他数据库: 使用 SQLAlchemy 原生 JSON
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "oracle":
            return dialect.type_descriptor(Text())
        return dialect.type_descriptor(SAJSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "oracle":
            if isinstance(value, str):
                return value
            return json.dumps(value, ensure_ascii=False)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "oracle":
            # oracledb 读取 CLOB 时可能返回 LOB 对象，需先 read()
            if hasattr(value, "read"):
                value = value.read()
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except Exception:
                    return value
        return value

class DataStatus():
    DELETED:int = 1000
    ACTIVE:int = 1
    INACTIVE:int = 2
    PENDING:int = 3
    COMPLETED:int = 4
    FAILED:int = 5
    FETCHING:int = 6  # 正在获取内容（锁定状态，防止多节点重复获取）
DATA_STATUS=DataStatus()
Base = declarative_base()