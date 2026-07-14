# schemas.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# ==========================================
# 1. 댓글(Comment) 관련 스키마
# ==========================================
class CommentBase(BaseModel):
    content: str
    author: Optional[str] = "익명"

class CommentCreate(CommentBase):
    password: str  # 등록 시 비밀번호 필수

class CommentResponse(CommentBase):
    id: int
    post_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# 2. 게시글(Post) 관련 스키마
# ==========================================
class PostBase(BaseModel):
    title: str
    content: str
    author: Optional[str] = "익명"

class PostCreate(PostBase):
    password: str  # 등록 시 평문 비밀번호 필수

class PostUpdate(BaseModel):
    title: str
    content: str
    password: str  # 수정 시 본인 확인용 비밀번호 전달 필요

class PostDelete(BaseModel):
    password: str  # 삭제 시 본인 확인용 비밀번호 전달 필요

class PostResponse(PostBase):
    id: int
    created_at: datetime
    updated_at: datetime
    # 상세 조회 시 댓글 목록도 함께 내려주기 위해 포함
    comments: List[CommentResponse] = []

    class Config:
        from_attributes = True


# ==========================================
# 3. 공공데이터(Location) 관련 스키마 (조회용)
# ==========================================
class LocationResponse(BaseModel):
    id: int
    region: str
    content_type_name: str
    contentid: str
    contenttypeid: str
    title: str
    addr1: Optional[str] = None
    addr2: Optional[str] = None
    tel: Optional[str] = None
    mapx: Optional[str] = None
    mapy: Optional[str] = None
    firstimage: Optional[str] = None

    class Config:
        from_attributes = True


# ==========================================
# 4. AI 챗봇 관련 스키마
# ==========================================
class ChatRequest(BaseModel):
    message: str  # 사용자가 보낸 질문

class ChatResponse(BaseModel):
    reply: str    # AI가 생성한 답변