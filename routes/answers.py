from typing import List

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import selectinload
from sqlmodel import select, Session

from database.connection import get_session
from models import Answer
from models.qa import QA, QAShort

from fastapi import Query

from datetime import datetime
import pytz

answer_router = APIRouter(
    tags=["Answer"],
)


@answer_router.get("/", response_model=List[QAShort])
async def get_qas(
        page: int = Query(1, ge=1),  # 기본 페이지 번호는 1
        page_size: int = Query(20, ge=1, le=100),  # 페이지 크기는 1~100 사이, 기본 20
        session: Session = Depends(get_session)
) -> List[QAShort]:
    offset = (page - 1) * page_size  # 페이지 번호에 따른 오프셋 계산

    # 필요한 필드만 선택해서 가져오는 쿼리 작성
    statement = select(
        QA.id,
        QA.title,
        QA.writer,
        QA.c_date,
        QA.done,
        QA.read_cnt
    ).offset(offset).limit(page_size)

    # 실행하고 결과를 가져옴
    result = session.exec(statement).all()

    # 필요한 필드를 CustomerQAShort로 변환
    qas_short = [
        QAShort(
            id=row.id,
            title=row.title,
            writer=row.writer,
            c_date=row.c_date.strftime('%Y-%m-%d'),
            done=row.done,
            read_cnt=row.read_cnt
        ) for row in result
    ]

    return qas_short


@answer_router.get("/{id}", response_model=QA, response_model_exclude={"password"})
async def get_qa(id: int, password: str, session: Session = Depends(get_session)) -> QA:
    # CustomerQA를 id로 조회하고 관련된 answers를 미리 로드
    qa = (session.exec(select(QA).where(QA.id == id)
                       .options(selectinload(QA.answers)))
          .first())

    if not qa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CustomerQA not found",
        )
    if qa.password != password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is not correct",
        )

    return qa


@answer_router.post("/", response_model=Answer)
async def create_answer(new_answer: Answer, qa_id: int, session=Depends(get_session)) -> Answer:
    raise_exception(new_answer.content, "Content cannot be blank")
    raise_exception(qa_id, 'qa_id cannot be null')

    qa_statement = select(QA).where(QA.id == qa_id)
    qa = session.exec(qa_statement).first()
    new_answer.qa = qa

    new_answer.qa_id = qa_id

    session.add(new_answer)
    session.commit()
    session.refresh(new_answer)

    return new_answer


# @answer_router.delete("/{id}")
# async def delete_event(id: int, session: Session = Depends(get_session)) -> dict:
#     event = session.get(Event, id)
#     if event:
#         session.delete(event)
#         session.commit()
#         return {
#             'message': 'Event deleted',
#         }
#     raise HTTPException(
#         status_code=status.HTTP_404_NOT_FOUND,
#         detail="Event not found",
#     )
#
#
# @answer_router.delete("/")
# async def delete_all_events() -> dict:
#     return {
#         'message': 'All event deleted',
#     }
#
#
# @answer_router.put("/{id}")
# async def update_event(id: int, update_event: EventUpdate, session: Session = Depends(get_session)) -> Event:
#     event = session.get(Event, id)
#     if event:
#         event_data = update_event.model_dump(exclude_unset=True)
#         for key, value in event_data.items():
#             setattr(event, key, value)
#         session.add(event)
#         session.commit()
#         session.refresh(event)
#
#         return event
#     raise HTTPException(
#         status_code=status.HTTP_404_NOT_FOUND,
#         detail="Event not found",
#     )

def raise_exception(val, message: str):
    if val == '' or not val:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )



def get_kr_date():
    # KST 타임존을 설정
    kst = pytz.timezone('Asia/Seoul')

    # 현재 KST 날짜와 시간 가져오기
    return datetime.now(kst).strftime('%Y-%m-%d')

