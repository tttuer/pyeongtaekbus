# captcha_routes.py
from fastapi import APIRouter, Form, HTTPException
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
async def get_captcha_image():
    text = generate_captcha_text()
    image = captcha_generator.generate_image(text)
    buffer = BytesIO()
    image.save(buffer, "PNG")
    buffer.seek(0)
    # CAPTCHA 텍스트를 전역 상태에 저장하여 검증에 사용
    captcha_router.captcha_text = text
    return StreamingResponse(buffer, media_type="image/png")

# CAPTCHA 확인 및 폼 처리 엔드포인트
@captcha_router.post("/submit")
async def submit_form(captcha: str = Form(...)):
    if captcha != captcha_router.captcha_text:
        log.error(f"CAPTCHA 검증 실패: 입력값 '{captcha}', 기대값 '{captcha_router.captcha_text}'")
        raise HTTPException(status_code=400, detail="Invalid CAPTCHA")
    return {"message": "CAPTCHA verified successfully!"}
