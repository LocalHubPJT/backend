# models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class LocationData(Base):
    """TourAPI 4.0 기반 공공데이터 적재 테이블"""
    __tablename__ = "location_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 최상위 메타 정보
    region = Column(String, index=True)         # 수집 권역명
    content_type_name = Column(String)          # 콘텐츠 유형 한국어명 (예: 관광지, 음식점)
    
    # items[] 상세 정보
    contentid = Column(String, unique=True, index=True, nullable=False) # 고유 ID (중복 적재 방지)
    contenttypeid = Column(String, index=True)  # 유형 ID (12, 14, 15, ...)
    title = Column(String, index=True, nullable=False) # 장소명
    addr1 = Column(String, nullable=True)       # 주소
    addr2 = Column(String, nullable=True)       # 상세 주소
    zipcode = Column(String, nullable=True)
    tel = Column(String, nullable=True)
    mapx = Column(String, nullable=True)        # 경도 (String 유지)
    mapy = Column(String, nullable=True)        # 위도 (String 유지)
    mlevel = Column(String, nullable=True)
    areacode = Column(String, nullable=True)
    sigungucode = Column(String, nullable=True)
    
    # 분류 코드들
    cat1 = Column(String, nullable=True)
    cat2 = Column(String, nullable=True)
    cat3 = Column(String, nullable=True)
    
    # 이미지 및 메타데이터
    firstimage = Column(String, nullable=True)  # 대표 이미지 URL
    firstimage2 = Column(String, nullable=True) # 대표 이미지 URL (썸네일)
    cpyrhtDivCd = Column(String, nullable=True) # 저작권 코드
    createdtime = Column(String, nullable=True)
    modifiedtime = Column(String, nullable=True)


class Post(Base):
    """익명 게시판 테이블"""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    author = Column(String, default="익명")
    password = Column(String, nullable=False) # 수정/삭제용 평문 패스워드 (의도된 설계)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")


class Comment(Base):
    """게시글 댓글 테이블"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String, default="익명")
    password = Column(String, nullable=False) # 수정/삭제용 평문 패스워드
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    post = relationship("Post", back_populates="comments")