import base64
from datetime import datetime

import pytz
from fastapi import APIRouter, UploadFile, File, Form
from utils.logger import log
from fastapi.responses import RedirectResponse
from sqlalchemy import desc
from sqlalchemy.orm import selectinload
from starlette.status import HTTP_401_UNAUTHORIZED

from models.qa import QAWithAnswer, QARetrieve

qa_router = APIRouter(
    tags=["Qa"],
)

# qa의 전체 리스트 반환
from fastapi import Depends, Query
from sqlmodel import Session, select, func
from models.qa import QA, QAType
from database.connection import get_session


@qa_router.get("", response_model=dict)
async def get_qas(
        qa_type: QAType,
        done: bool = None,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        session: Session = Depends(get_session)
):
    offset = (page - 1) * page_size

    if done is None:
        statement = (
            select(QA)
            .where(QA.qa_type == qa_type)
            .order_by(desc(QA.id))  # id를 기준으로 내림차순 정렬
            .offset(offset)
            .limit(page_size)
        )

        # 전체 항목 수와 총 페이지 계산
        total_count = session.exec(select(func.count()).select_from(QA).where(QA.qa_type == qa_type)).one()
    elif done is True:
        statement = (
            select(QA)
            .where(QA.qa_type == qa_type)
            .where(QA.done == True)
            .order_by(desc(QA.id))  # id를 기준으로 내림차순 정렬
            .offset(offset)
            .limit(page_size)
        )

        # 전체 항목 수와 총 페이지 계산
        total_count = session.exec(
            select(func.count()).select_from(QA).where(QA.qa_type == qa_type).where(QA.done == True)).one()
    else:
        statement = (
            select(QA)
            .where(QA.qa_type == qa_type)
            .where(QA.done == False)
            .order_by(desc(QA.id))  # id를 기준으로 내림차순 정렬
            .offset(offset)
            .limit(page_size)
        )

        # 전체 항목 수와 총 페이지 계산
        total_count = session.exec(
            select(func.count()).select_from(QA).where(QA.qa_type == qa_type).where(QA.done == False)).one()

    result = session.exec(statement).all()

    # 필요한 필드를 CustomerQAShort로 변환
    qas_short = [
        {
            "id": row.id,
            "num": (page - 1) * page_size + index + 1,
            "title": row.title,
            "writer": row.writer,
            "c_date": row.c_date,
            "done": row.done,
            "hidden": row.hidden,
            "read_cnt": row.read_cnt,
            "attachment_filename": row.attachment_filename,
        }
        for index, row in enumerate(result)
    ]

    total_pages = (total_count + page_size - 1) // page_size

    return {
        "qas": qas_short,
        "page": page,
        "total_pages": total_pages
    }


# qa 상세보기 클릭했을때 조회
@qa_router.get("/{id}", response_model=QAWithAnswer)
async def get_qa(id: int, password: str = 'default-password', session: Session = Depends(get_session)) -> QAWithAnswer:
    # CustomerQA를 id로 조회하고 관련된 answers를 미리 로드
    statement = select(QA).options(selectinload(QA.answers)).where(QA.id == id)
    qa = session.exec(statement).first()

    if not qa:
        log.error(f"QA를 찾을 수 없음: ID {id}")
        raise HTTPException(status_code=404, detail="QA not found")
    if qa.hidden and password != 'default-password' and qa.password != password:
        log.error(f"QA 비밀번호 불일치: ID {id}, 입력 비밀번호: {password[:2]}***")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Password mismatch")

    # attachment를 Base64로 인코딩
    attachment_base64 = base64.b64encode(qa.attachment).decode("cp949") if qa.attachment else None

    # QAPublic 또는 QAWithAnswer 모델로 반환
    return QAWithAnswer(
        id=qa.id,
        password=qa.password,
        writer=qa.writer,
        email=qa.email,
        title=qa.title,
        content=qa.content,
        attachment=attachment_base64,
        attachment_filename=qa.attachment_filename,
        c_date=qa.c_date,
        done=qa.done,
        read_cnt=qa.read_cnt,
        hidden=qa.hidden,
        qa_type=qa.qa_type,
        answers=qa.answers  # 예시로 직접 넣음
    )


# qa 생성
from fastapi import HTTPException, status


@qa_router.post("", response_class=RedirectResponse)
async def create_qa(
        writer: str = Form(...),
        email: str = Form(None),
        password: str = Form(...),
        title: str = Form(...),
        content: str = Form(None),
        hidden: bool = Form(False),
        qa_type: QAType = Form(QAType.CUSTOMER),
        attachment: UploadFile = File(None),
        redirect_url: str = Form(None),
        session: Session = Depends(get_session)) -> QARetrieve:
    # 파일이 존재하는 경우 이미지 파일인지 확인
    if attachment and attachment.filename != '':
        if not attachment.content_type.startswith("image/"):
            log.error(f"QA 생성 - 잘못된 파일 형식: {attachment.content_type}, 파일명: {attachment.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미지 파일만 업로드할 수 있습니다."
            )
        attachment_data = await attachment.read()
        attachment_filename = attachment.filename
    else:
        attachment_data = None
        attachment_filename = None

    # 이메일 빈 문자열을 None으로 변환
    email = email if email else None

    # Create the QA object
    new_qa = QA(
        writer=writer,
        email=email,
        password=password,
        title=title,
        content=content,
        attachment=attachment_data,
        hidden=hidden,
        qa_type=qa_type,
        c_date=get_kr_date().format('%Y-%m-%d'),
        attachment_filename=attachment_filename,
    )

    # Add the object to the session and save to the database
    session.add(new_qa)
    session.commit()
    session.refresh(new_qa)

    return RedirectResponse(url=redirect_url, status_code=303)


# qa 삭제
@qa_router.delete("/{id}")
async def delete_qa(id: int, password: str, session: Session = Depends(get_session)) -> dict:
    qa = session.get(QA, id)
    if qa:
        if password == qa.password:
            session.delete(qa)
            session.commit()
            return {
                'message': 'Customer QA deleted',
            }
        log.error(f"QA 삭제 - 비밀번호 오류: ID {id}, 입력 비밀번호: {password[:2]}***")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect",
        )
    log.error(f"QA 삭제 - 존재하지 않는 ID: {id}")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Customer QA not found",
    )


@qa_router.patch("/{id}", response_class=RedirectResponse)
async def update_qa(
        id: int,
        email: str = Form(None),
        password: str = Form(...),
        title: str = Form(...),
        content: str = Form(None),
        hidden: bool = Form(False),
        attachment: UploadFile = File(None),
        keepAttachment: str = Form("true"),
        redirect_url: str = Form(None),
        session: Session = Depends(get_session),
) -> QA:
    qa = session.get(QA, id)
    if not qa:
        log.error(f"QA 수정 - 존재하지 않는 ID: {id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer QA not found",
        )

    # 새 파일이 업로드되었거나 파일 삭제가 요청된 경우 처리
    if keepAttachment == "false":
        if attachment.filename != '':  # 새 파일이 업로드된 경우
            if not attachment.content_type.startswith("image/"):
                log.error(f"QA 수정 - 잘못된 파일 형식: {attachment.content_type}, 파일명: {attachment.filename}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미지 파일만 업로드할 수 있습니다."
                )
            qa.attachment = await attachment.read()
            qa.attachment_filename = attachment.filename
        else:  # 파일 삭제만 요청된 경우
            qa.attachment = None
            qa.attachment_filename = None

    # 이메일이 빈 문자열로 제출되었을 때 None으로 설정
    qa.email = email or None
    qa.password = password
    qa.title = title
    qa.content = content
    qa.hidden = hidden
    qa.c_date = get_kr_date().format('%Y-%m-%d')

    # 변경 사항 저장
    session.add(qa)
    session.commit()
    session.refresh(qa)

    # 리다이렉션 수행
    return RedirectResponse(url=redirect_url, status_code=303)


@qa_router.get("/{id}/check_password")
async def check_password(id: int, password: str, session: Session = Depends(get_session)):
    qa = session.get(QA, id)

    if not qa or qa.password != password:
        log.error(f"QA 비밀번호 확인 실패: ID {id}, 입력 비밀번호: {password[:2]}***")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password incorrect",
        )


@qa_router.patch("/{id}/read")
async def read(id: int, session: Session = Depends(get_session)):
    qa = session.get(QA, id)
    if not qa:
        log.error(f"QA 조회수 증가 - 존재하지 않는 ID: {id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QA not found",
        )

    qa.read_cnt += 1

    session.commit()
    session.refresh(qa)


def raise_exception(empty_val, message: str):
    if empty_val == '':
        log.error(f"QA 유효성 검사 실패: {message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )


def get_kr_date():
    # KST 타임존을 설정
    kst = pytz.timezone('Asia/Seoul')

    # 현재 KST 날짜와 시간 가져오기
    return datetime.now(kst).strftime('%Y-%m-%d')
