# captcha_routes.py
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import StreamingResponse
from utils.logger import log
from captcha.image import ImageCaptcha  # captcha 라이브러리 사용
from io import BytesIO
import random
import string

captcha_router = APIRouter()

# CAPTCHA 객체 생성
captcha_generator = ImageCaptcha(width=150, height=50)  # 이미지 크기 조절

# 숫자만 포함된 CAPTCHA 생성
def generate_captcha_text():
    return ''.join(random.choices(string.digits, k=5))  # 숫자 5자리로 제한

# CAPTCHA 이미지 생성 엔드포인트
@captcha_router.get("/captcha_image")
async def get_captcha_image(request: Request):
    text = generate_captcha_text()
    image = captcha_generator.generate_image(text)
    buffer = BytesIO()
    image.save(buffer, "PNG")
    buffer.seek(0)
    # CAPTCHA 텍스트를 세션에 저장하여 사용자별로 관리
    request.session["captcha_text"] = text
    return StreamingResponse(buffer, media_type="image/png")

# CAPTCHA 검증 함수 (다른 라우터에서 사용 가능)
def verify_captcha(request: Request, captcha_input: str) -> bool:
    session_captcha = request.session.get("captcha_text")
    if not session_captcha:
        return False
    
    # 검증 후 세션에서 캡차 제거 (재사용 방지)
    request.session.pop("captcha_text", None)
    
    return captcha_input == session_captcha

# CAPTCHA 확인 및 폼 처리 엔드포인트
@captcha_router.post("/submit")
async def submit_form(request: Request, captcha: str = Form(...)):
    if not verify_captcha(request, captcha):
        log.error(f"CAPTCHA 검증 실패: 입력값 '{captcha}'")
        raise HTTPException(status_code=400, detail="Invalid CAPTCHA")
    return {"message": "CAPTCHA verified successfully!"}
