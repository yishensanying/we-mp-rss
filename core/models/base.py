from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, DateTime,Date,ForeignKey,Boolean,Enum,Table,JSON
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from core.config import cfg

_db_url = cfg.get("db", "")
if _db_url.startswith("mysql"):
    from sqlalchemy.dialects.mysql import MEDIUMTEXT as Text
elif _db_url.startswith("oracle"):
    from sqlalchemy import Text  # Oracle: Text -> CLOB
else:
    from sqlalchemy import Text

class DataStatus():
    DELETED:int = 1000
    ACTIVE:int = 1
    INACTIVE:int = 2
    PENDING:int = 3
    COMPLETED:int = 4
    FAILED:int = 5
DATA_STATUS=DataStatus()
Base = declarative_base()