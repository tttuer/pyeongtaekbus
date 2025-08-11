from datetime import datetime

import pytz
from fastapi import APIRouter, HTTPException, status, Depends
from utils.logger import log
from sqlmodel import select, Session

from auth.authenticate import authenticate
from database.connection import get_session
from models import Answer
from models.answers import AnswerUpdate
from models.qa import QA

answer_router = APIRouter(
    tags=["Answer"],
)


@answer_router.post("", response_model=Answer)
async def create_answer(new_answer: Answer, qa_id: int, user: str = Depends(authenticate),
                        session=Depends(get_session)) -> Answer:
    if user != 'bsbus':
        log.error(f"답변 작성 권한 없음: {user}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    raise_exception(new_answer.content, "Content cannot be blank")
    raise_exception(qa_id, 'qa_id cannot be null')

    qa_statement = select(QA).where(QA.id == qa_id)
    qa = session.exec(qa_statement).first()
    qa.done = True

    new_answer.qa = qa
    new_answer.creator = user
    new_answer.qa_id = qa_id

    session.add(qa)
    session.add(new_answer)
    session.commit()
    session.refresh(new_answer)

    return new_answer


@answer_router.delete("/{id}")
async def delete_answer(id: int, user: str = Depends(authenticate), session: Session = Depends(get_session)) -> dict:
    answer_exist = session.get(Answer, id)
    if answer_exist.creator != user:
        log.error(f"답변 삭제 권한 없음: {user} != {answer_exist.creator}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You do not have permission to perform this action",
        )
    if answer_exist:
        qa = session.get(QA, answer_exist.qa_id)
        qa.done = False

        session.add(qa)
        session.delete(answer_exist)
        session.commit()
        return {
            'message': 'Answer deleted',
        }
    log.error(f"삭제할 답변을 찾을 수 없음: ID {id}")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Event not found",
    )


@answer_router.patch("/{id}")
async def update_answer(id: int, update_answer: AnswerUpdate, user: str = Depends(authenticate),
                        session: Session = Depends(get_session)) -> Answer:
    answer = session.get(Answer, id)
    if answer.creator != user:
        log.error(f"답변 수정 권한 없음: {user} != {answer.creator}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You do not have permission to perform this action",
        )
    if answer:
        answer_data = update_answer.model_dump(exclude_unset=True)
        for key, value in answer_data.items():
            setattr(answer, key, value)
        session.add(answer)
        session.commit()
        session.refresh(answer)

        return answer
    log.error(f"수정할 답변을 찾을 수 없음: ID {id}")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Answer not found",
    )


def raise_exception(val, message: str):
    if val == '' or not val:
        log.error(f"입력 값 검증 오류: {message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )


def get_kr_date():
    # KST 타임존을 설정
    kst = pytz.timezone('Asia/Seoul')

    # 현재 KST 날짜와 시간 가져오기
    return datetime.now(kst).strftime('%Y-%m-%d')
