import time
from datetime import datetime

from fastapi import HTTPException, status
from jose import jwt, JWTError
from utils.logger import log

from database.connection import Settings

settings = Settings()


def create_access_token(user: str):
    payload = {
        "user": user,
        "expires": time.time() + 86400
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token


from starlette.responses import RedirectResponse


def verify_access_token(token: str):
    try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        expire = data.get('expires')

        if expire is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='No access token supplied')
        return datetime.utcnow() < datetime.utcfromtimestamp(expire)

    except JWTError as e:
        log.error(f"JWT 토큰 검증 실패: {e}")
        return RedirectResponse(url="/adm/login")


def get_access_token(token: str):
    try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        expire = data.get('expires')

        if expire is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='No access token supplied')
        if datetime.utcnow() > datetime.utcfromtimestamp(expire):
            return None

        return data

    except JWTError as e:
        log.error(f"JWT 토큰 디코딩 실패: {e}")
        return RedirectResponse(url="/adm/login")
