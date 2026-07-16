# database.py
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# 로컬에서는 기본값으로 SQLite를 사용하고,
# Render에서는 환경변수 DATABASE_URL의 PostgreSQL 주소를 사용합니다.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./localhub.db",
)

# 일부 환경에서 postgres:// 형식으로 전달될 경우
# SQLAlchemy가 인식하는 postgresql:// 형식으로 변경합니다.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1,
    )

engine_options = {
    "pool_pre_ping": True,
}

# check_same_thread는 SQLite에서만 사용할 수 있습니다.
if DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {
        "check_same_thread": False,
    }

engine = create_engine(
    DATABASE_URL,
    **engine_options,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()