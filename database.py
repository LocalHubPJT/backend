# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# 환경변수에서 DATABASE_URL을 가져오며, 기본값으로 로컬 sqlite를 지정합니다.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./localhub.db")

# SQLite의 경우 멀티 스레드 접근을 허용하기 위해 connect_args 설정이 필요합니다.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# DB 세션 의존성 주입을 위한 제너레이터 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()