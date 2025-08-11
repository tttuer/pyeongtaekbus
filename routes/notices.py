from datetime import datetime

import pytz
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi import Query
from utils.logger import log
from sqlalchemy import desc
from sqlmodel import Session, select, func
from starlette.responses import RedirectResponse

from auth.authenticate import authenticate
from database.connection import get_session
from models.notice import Notice, NoticeType, NoticeUpdate, NoticeRequest, NoticePublic

notice_router = APIRouter(
    tags=["Notice"],
)


@notice_router.get("", response_model=dict)
# qa의 전체 리스트 반환
async def get_notices(
        notice_type: NoticeType = NoticeType.NOTICE,
        page: int = Query(1, ge=1),  # 기본 페이지 번호는 1
        page_size: int = Query(20, ge=1, le=100),  # 페이지 크기는 1~100 사이, 기본 20
        session: Session = Depends(get_session)
):
    offset = (page - 1) * page_size  # 페이지 번호에 따른 오프셋 계산

    # 전체 항목 수와 총 페이지 계산
    total_count = session.exec(select(func.count()).select_from(Notice).where(Notice.notice_type == notice_type)).one()
    total_pages = (total_count + page_size - 1) // page_size

    # 필요한 필드만 선택해서 역순으로 가져오는 쿼리 작성
    statement = (
        select(Notice)
        .where(Notice.notice_type == notice_type)
        .order_by(desc(Notice.id))  # id를 기준으로 내림차순 정렬
        .offset(offset)
        .limit(page_size)
    )
    result = session.exec(statement).all()

    # 필요한 필드를 CustomerQAShort로 변환
    notices_short = [
        {
            "num": (page - 1) * page_size + index + 1,
            "id": row.id,
            "title": row.title,
            "writer": row.writer,
            "c_date": row.c_date,
            "done": row.done,
            "read_cnt": row.read_cnt,
            "attachment_filename": row.attachment_filename,
            "notice_type": notice_type,
        }
        for index, row in enumerate(result)
    ]

    return {
        "notices": notices_short,
        "page": page,
        "total_pages": total_pages
    }


# qa 상세보기 클릭했을때 조회
@notice_router.get("/{id}", response_model=NoticePublic)
async def get_notice(id: int, session: Session = Depends(get_session)) -> NoticePublic:
    # CustomerQA를 id로 조회하고 관련된 answers를 미리 로드
    notice = session.get(Notice, id)

    if not notice:
        log.error(f"공지사항을 찾을 수 없음: ID {id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notice not found",
        )

    return notice.to_notice_public()


@notice_router.post("", response_model=Notice)
# qa 생성
async def create_notice(
        notice_request: NoticeRequest = Depends(NoticeRequest.as_form),
        user: str = Depends(authenticate),
        session=Depends(get_session)):
    check_admin(user)

    raise_exception(notice_request.title, "Title cannot be blank")

    new_notice = await notice_request.to_notice()

    new_notice.c_date = get_kr_date().format('%Y-%m-%d')
    new_notice.creator = user

    session.add(new_notice)
    session.commit()
    session.refresh(new_notice)

    return RedirectResponse(url='/adm/notice', status_code=303)


# qa 삭제
@notice_router.delete("/{id}")
async def delete_notice(id: int, user: str = Depends(authenticate), session: Session = Depends(get_session)) -> dict:
    check_admin(user)

    notice = session.get(Notice, id)

    if notice:
        session.delete(notice)
        session.commit()
        return {
            'message': 'Notice deleted',
        }
    log.error(f"삭제할 공지사항을 찾을 수 없음: ID {id}")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Customer QA not found",
    )


@notice_router.patch("/{id}")
async def update_notice(id: int, update_notice: NoticeUpdate, user: str = Depends(authenticate),
                        session: Session = Depends(get_session)) -> Notice:
    check_admin(user)

    notice = session.get(Notice, id)
    if notice:
        notice_data = update_notice.model_dump(exclude_unset=True)
        for key, value in notice_data.items():
            setattr(notice, key, value)
        session.add(notice)
        session.commit()
        session.refresh(notice)

        return notice

    log.error(f"수정할 공지사항을 찾을 수 없음: ID {id}")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Notice not found",
    )


def raise_exception(empty_val, message: str):
    if empty_val == '':
        log.error(f"입력 값 검증 오류: {message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )


def check_admin(user: str):
    if user != 'bsbus':
        log.error(f"관리자 권한 없음: {user}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )


def get_kr_date():
    # KST 타임존을 설정
    kst = pytz.timezone('Asia/Seoul')

    # 현재 KST 날짜와 시간 가져오기
    return datetime.now(kst).strftime('%Y-%m-%d')
