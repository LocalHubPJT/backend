# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from database import engine, SessionLocal, Base
import models

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import schemas
from typing import List, Optional


# main.py 상단에 추가
from openai import OpenAI
from dotenv import load_dotenv

# .env 환경 변수 로드 및 OpenAI 클라이언트 초기화
load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# 1. DB 테이블 자동 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LocalHub API Server")

# 2. CORS 미들웨어 설정 (프론트엔드 레포가 분리되어 있으므로 필수!)
origins = [
    "http://localhost:5173",  # Vue.js 로컬 개발 포트
    # 추후 Netlify 배포 시 실제 프론트 주소를 여기에 추가하게 됩니다.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 서버 시작 시 공공데이터 JSON 자동 파싱 및 DB 적재
@app.on_event("startup")
def load_public_data():
    db = SessionLocal()
    try:
        # DB에 데이터가 이미 있다면 마이그레이션 생략
        if db.query(models.LocationData).first() is not None:
            print("데이터베이스에 이미 공공데이터가 존재합니다. 마이그레이션을 건너뜁니다.")
            return

        print("공공데이터 JSON 분석 및 데이터베이스 적재를 시작합니다...")
        
        data_dir = "./data"
        json_files = [
            "대전_충청권_관광지.json", 
            "대전_충청권_레포츠.json", 
            "대전_충청권_문화시설.json", 
            "대전_충청권_쇼핑.json", 
            "대전_충청권_숙박.json", 
            "대전_충청권_여행코스.json", 
            "대전_충청권_음식점.json", 
            "대전_충청권_축제공연행사.json"
        ]

        for file_name in json_files:
            file_path = os.path.join(data_dir, file_name)
            if not os.path.exists(file_path):
                print(f"경고: {file_name} 파일을 찾을 수 없어 건너뜁니다.")
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            region = raw_data.get("region", "미지정")
            content_type_name = raw_data.get("contentType", "기타")
            items = raw_data.get("items", [])

            print(f"적재 중: {file_name} ({len(items)}개 항목 감지)...")

            for item in items:
                # 중복 데이터 검사
                existing = db.query(models.LocationData).filter_by(contentid=item.get("contentid")).first()
                if existing:
                    continue

                location = models.LocationData(
                    region=region,
                    content_type_name=content_type_name,
                    contentid=item.get("contentid"),
                    contenttypeid=item.get("contenttypeid"),
                    title=item.get("title", ""),
                    addr1=item.get("addr1", "") or None, # 빈 문자열 방지
                    addr2=item.get("addr2", "") or None,
                    zipcode=item.get("zipcode", "") or None,
                    tel=item.get("tel", "") or None,
                    mapx=item.get("mapx", "") or None,
                    mapy=item.get("mapy", "") or None,
                    mlevel=item.get("mlevel", "") or None,
                    areacode=item.get("areacode", "") or None,
                    sigungucode=item.get("sigungucode", "") or None,
                    cat1=item.get("cat1", "") or None,
                    cat2=item.get("cat2", "") or None,
                    cat3=item.get("cat3", "") or None,
                    firstimage=item.get("firstimage", "") or None,
                    firstimage2=item.get("firstimage2", "") or None,
                    cpyrhtDivCd=item.get("cpyrhtDivCd", "") or None,
                    createdtime=item.get("createdtime", "") or None,
                    modifiedtime=item.get("modifiedtime", "") or None
                )
                db.add(location)
            
            db.commit() # 파일 단위 커밋
            print(f"적재 완료: {file_name}")

        print("모든 공공데이터 마이그레이션이 성공적으로 마쳤습니다!")
    except Exception as e:
        db.rollback()
        print(f"마이그레이션 과정 중 오류 발생: {e}")
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to LocalHub API Server!"}


# ==========================================
# [API] 1. 게시글 관련 CRUD
# ==========================================

@app.post("/api/posts", response_model=schemas.PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db)):
    """새로운 익명 게시글 작성"""
    db_post = models.Post(
        title=post.title,
        content=post.content,
        author=post.author,
        password=post.password  # 평문 비밀번호 그대로 저장
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@app.get("/api/posts", response_model=List[schemas.PostResponse])
def get_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """게시글 목록 조회 (최신순 정렬)"""
    return db.query(models.Post).order_by(models.Post.id.desc()).offset(skip).limit(limit).all()


@app.get("/api/posts/{post_id}", response_model=schemas.PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    """게시글 상세 조회"""
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return db_post


@app.put("/api/posts/{post_id}", response_model=schemas.PostResponse)
def update_post(post_id: int, post_update: schemas.PostUpdate, db: Session = Depends(get_db)):
    """익명 게시글 수정 (비밀번호 일치 여부 검증)"""
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    # 의도된 요구사항: 평문 비밀번호 일치 확인
    if db_post.password != post_update.password:
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않아 수정 권한이 없습니다.")
    
    db_post.title = post_update.title
    db_post.content = post_update.content
    db.commit()
    db.refresh(db_post)
    return db_post


# 비밀번호는 쿼리 매개변수(password: str)로 직접 받습니다.
@app.delete("/api/posts/{post_id}")
def delete_post(post_id: int, req: schemas.PostDelete, db: Session = Depends(get_db)):
    """익명 게시글 삭제 (Body의 비밀번호 일치 여부 검증)"""
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    # Body로 전달받은 req.password와 비교합니다.
    if db_post.password != req.password:
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않아 삭제 권한이 없습니다.")
    
    db.delete(db_post)
    db.commit()
    return {"message": "게시글이 성공적으로 삭제되었습니다."}

# 비밀번호 검증
@app.post("/api/posts/{post_id}/verify")
def verify_post_password(
    post_id: int,
    req: schemas.PostDelete,
    db: Session = Depends(get_db)
):
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()

    if not db_post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    if db_post.password != req.password:
        raise HTTPException(
            status_code=403,
            detail="비밀번호가 일치하지 않습니다."
        )

    return {"message": "비밀번호 확인 완료"}


# ==========================================
# [API] 2. 댓글 관련 API
# ==========================================

@app.post("/api/posts/{post_id}/comments", response_model=schemas.CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(post_id: int, comment: schemas.CommentCreate, db: Session = Depends(get_db)):
    """특정 게시글에 익명 댓글 작성"""
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    db_comment = models.Comment(
        post_id=post_id,
        content=comment.content,
        author=comment.author,
        password=comment.password
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


# ==========================================
# [API] 3. 지역 정보 조회 API (프론트엔드 정보 표출용)
# ==========================================

@app.get("/api/locations", response_model=List[schemas.LocationResponse])
def get_locations(category_id: Optional[str] = None, query: Optional[str] = None, db: Session = Depends(get_db)):
    """DB에 적재된 공공데이터 목록 검색 및 조회"""
    q = db.query(models.LocationData)
    if category_id:
        q = q.filter(models.LocationData.contenttypeid == category_id)
    if query:
        q = q.filter(models.LocationData.title.contains(query) | models.LocationData.addr1.contains(query))
    return q.limit(2000).all()



# ==========================================
# [API] 4. AI 로컬 가이드 챗봇 API
# ==========================================

@app.post("/api/chat", response_model=schemas.ChatResponse)
def chat_with_local_guide(req: schemas.ChatRequest, db: Session = Depends(get_db)):
    """
    대전·충청권 공공데이터 기반 맞춤형 AI 로컬 가이드 챗봇
    """
    user_message = req.message

    # 1. 사용자의 질문 키워드가 공공데이터 타이틀이나 주소에 포함되어 있는지 가볍게 검색
    # 예: "성심당 추천해 줘" -> "성심당" 키워드로 DB 검색
    related_places = []
    # 간단한 명사 형태 검색 유도를 위해 2글자 이상 단어들 추출 후 검색 시도
    keywords = [word for word in user_message.split() if len(word) >= 2]
    
    if keywords:
        # 첫 번째 유의미한 키워드로 최대 5개의 지역 정보 검색
        search_keyword = keywords[0]
        db_results = db.query(models.LocationData).filter(
            models.LocationData.title.contains(search_keyword) | 
            models.LocationData.addr1.contains(search_keyword)
        ).limit(5).all()
        
        for place in db_results:
            related_places.append(
                f"- 이름: {place.title} | 분류: {place.content_type_name} | 주소: {place.addr1 or '정보 없음'} | 전화번호: {place.tel or '정보 없음'}"
            )

    # AI에게 줄 컨텍스트 빌드
    context = ""
    if related_places:
        context = "대화에 참고할 실제 지역 정보:\n" + "\n".join(related_places)
    else:
        context = "참고할 특정한 DB 정보가 없습니다. 일반적인 대전·충청권 지식을 바탕으로 친절하게 답변해 주세요."

    # 2. OpenAI GPT API 호출 (system prompt 설정을 통해 대전·충청 전문가 페르소나 부여)
    try:
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",  
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 대전 및 충청 지역(LocalHub)의 전문 로컬 가이드 AI입니다. "
                        "사용자에게 매우 친절하고 친근한 톤(예: '~해보시는 건 어떨까요?', '~를 추천해 드려요!')으로 지역 정보를 안내해야 합니다.\n\n"
                        
                        # 1. 환각 방지 및 기본 지침
                        "제공된 '실제 지역 정보' 데이터가 있다면 반드시 이를 최우선으로 정확하게 안내하세요. "
                        "데이터가 부족하더라도 알고 있는 신뢰할 수 있는 정보를 동원해 구체적인 코스나 꿀팁을 함께 제안하되, "
                        "확실치 않은 정보는 방문 전 확인을 권장하는 멘트를 부드럽게 덧붙이세요.\n\n"
                        
                        # 2. 강력한 포맷팅 규칙 (가독성 극대화)
                        "★ [매우 중요 - 출력 포맷 가이드라인] ★\n"
                        "답변을 작성할 때는 가독성을 위해 반드시 다음 규칙을 준수하세요:\n"
                        "1. 모든 추천 장소(코스) 사이에는 반드시 빈 줄을 하나 추가하여 문단을 분리하세요. 절대 하나의 긴 줄글로 이어서 쓰지 마세요.\n"
                        "2. 가독성을 높이기 위해 다음과 같은 형태의 마크다운(Markdown) 리스트와 이모지를 적용하세요.\n"
                        "   (예시 포맷):\n"
                        "   📍 **추천 테마 이름**\n"
                        "   - **장소명**: 주소\n"
                        "   - **특징 및 꿀팁**: 한 줄 평 요약\n"
                        "3. 긴 설명 대신 핵심 정보 위주로 깔끔하게 요약하여 한눈에 들어오게 작성하세요.\n"
                        "4. 전체 답변의 길이는 사용자가 특별히 요청하지 않는 한, 3개 이하의 코스 추천과 함께 전체 분량은 5문장 내외의 요약된 수준으로 제한하세요."
                    )
                },
                {
                    "role": "user",
                    "content": f"{context}\n\n사용자 질문: {user_message}"
                }
            ]
        )
        
        ai_reply = response.choices[0].message.content
        return schemas.ChatResponse(reply=ai_reply)

    except Exception as e:
        print(f"OpenAI API 호출 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500, 
            detail="AI 가이드와 연결하는 중에 문제가 발생했습니다. API 키를 확인해 주세요."
        )