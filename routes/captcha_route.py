# captcha_routes.py
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import StreamingResponse
from utils.logger import log
from captcha.image import ImageCaptcha  # captcha 라이브러리 사용
from io import BytesIO
import random
import string
import uuid
import time

captcha_router = APIRouter()

# CAPTCHA 객체 생성
captcha_generator = ImageCaptcha(width=150, height=50)  # 이미지 크기 조절

# 메모리에 캡차 저장 (captcha_id: {"text": text, "timestamp": timestamp})
captcha_store = {}

# 숫자만 포함된 CAPTCHA 생성
def generate_captcha_text():
    return ''.join(random.choices(string.digits, k=5))  # 숫자 5자리로 제한

# 만료된 캡차 정리 (5분 이상 된 것들)
def cleanup_expired_captchas():
    current_time = time.time()
    expired_keys = [
        key for key, value in captcha_store.items()
        if current_time - value["timestamp"] > 300  # 5분
    ]
    for key in expired_keys:
        captcha_store.pop(key, None)

# CAPTCHA 이미지 생성 엔드포인트
@captcha_router.get("/captcha_image")
async def get_captcha_image():
    # 만료된 캡차 정리
    cleanup_expired_captchas()
    
    text = generate_captcha_text()
    captcha_id = str(uuid.uuid4())
    
    # 메모리에 캡차 저장
    captcha_store[captcha_id] = {
        "text": text,
        "timestamp": time.time()
    }
    
    image = captcha_generator.generate_image(text)
    buffer = BytesIO()
    image.save(buffer, "PNG")
    buffer.seek(0)
    
    # 응답 헤더에 captcha_id 포함
    response = StreamingResponse(buffer, media_type="image/png")
    response.headers["X-Captcha-ID"] = captcha_id
    
    return response

# CAPTCHA 확인 및 폼 처리 엔드포인트
@captcha_router.post("/submit")
async def submit_form(captcha: str = Form(...), captcha_id: str = Form(...)):
    captcha_data = captcha_store.get(captcha_id)
    
    if not captcha_data or captcha != captcha_data["text"]:
        log.error(f"CAPTCHA 검증 실패: 입력값 '{captcha}', ID '{captcha_id}'")
        raise HTTPException(status_code=400, detail="Invalid CAPTCHA")
    
    # 검증 후 캡차 제거 (재사용 방지)
    captcha_store.pop(captcha_id, None)
    
    return {"message": "CAPTCHA verified successfully!"}
