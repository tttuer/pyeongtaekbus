import base64

from fastapi import APIRouter, UploadFile, File, Form, Response
from utils.logger import log
from fastapi.responses import RedirectResponse

from auth.authenticate import authenticate, check_admin
from models.bus_schedule import BusSchedule, BusSchedulePublic

schedule_router = APIRouter(
    tags=["BusSchedule"],
)

# qa의 전체 리스트 반환
from fastapi import Depends, Query
from sqlmodel import Session, select, func
from database.connection import get_session


@schedule_router.get("", response_model=dict)
async def get_schedules(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        session: Session = Depends(get_session)
):
    offset = (page - 1) * page_size

    # 전체 항목 수와 총 페이지 계산
    total_count = session.exec(select(func.count()).select_from(BusSchedule)).one()
    total_pages = (total_count + page_size - 1) // page_size

    statement = (
        select(BusSchedule)
        .offset(offset)
        .limit(page_size)
    )
    result = session.exec(statement).all()

    schedules = [
        {
            "id": row.id,
            "num": index + 1,
            "title": row.title,
            "image": base64.b64encode(row.image_data1).decode("cp949") if row.image_data1 else None

        }
        for index, row in enumerate(result)
    ]

    return {
        "schedules": schedules,
        "page": page,
        "total_pages": total_pages
    }


# qa 상세보기 클릭했을때 조회
@schedule_router.get("/{id}", response_model=BusSchedulePublic)
async def get_schedule(id: int, session: Session = Depends(get_session)):
    schedule = session.get(BusSchedule, id)

    if not schedule:
        log.error(f"버스 시간표를 찾을 수 없음: ID {id}")
        raise HTTPException(status_code=404, detail="Schedule not found")

    # QAPublic 또는 QAWithAnswer 모델로 반환
    return BusSchedulePublic(
        id=schedule.id,
        image_name1=schedule.image_name1,
        image_name2=schedule.image_name2,
        image_name3=schedule.image_name3,
        image_data1=base64.b64encode(schedule.image_data1).decode("cp949") if schedule.image_data1 else None,
        image_data2=base64.b64encode(schedule.image_data2).decode("cp949") if schedule.image_data2 else None,
        image_data3=base64.b64encode(schedule.image_data3).decode("cp949") if schedule.image_data3 else None,
        title=schedule.title
    )


# qa 생성
from fastapi import HTTPException, status


@schedule_router.post("", response_class=Response)
async def create_schedule(
        title: str = Form(...),
        image1: UploadFile = File(None),
        image2: UploadFile = File(None),
        image3: UploadFile = File(None),
        user: str = Depends(authenticate),
        session: Session = Depends(get_session)) -> Response:
    check_admin(user)

    # 파일이 존재하는 경우 이미지 파일인지 확인
    if image1 and image1.filename != '':
        if not image1.content_type.startswith("image/"):
            log.error(f"버스 시간표 생성 - 잘못된 파일 형식: {image1.content_type}, 파일명: {image1.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미지 파일만 업로드할 수 있습니다."
            )
        image1_data = await image1.read()
        image1_filename = image1.filename
    else:
        image1_data = None
        image1_filename = None
    if image2 and image2.filename != '':
        if not image2.content_type.startswith("image/"):
            log.error(f"버스 시간표 생성 - 잘못된 파일 형식: {image2.content_type}, 파일명: {image2.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미지 파일만 업로드할 수 있습니다."
            )
        image2_data = await image2.read()
        image2_filename = image2.filename
    else:
        image2_data = None
        image2_filename = None
    if image3 and image3.filename != '':
        if not image3.content_type.startswith("image/"):
            log.error(f"버스 시간표 생성 - 잘못된 파일 형식: {image3.content_type}, 파일명: {image3.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미지 파일만 업로드할 수 있습니다."
            )
        image3_data = await image3.read()
        image3_filename = image3.filename
    else:
        image3_data = None
        image3_filename = None

    # Create the QA object
    new_schedule = BusSchedule(
        title=title,
        image_data1=image1_data,
        image_name1=image1_filename,
        image_data2=image2_data,
        image_name2=image2_filename,
        image_data3=image3_data,
        image_name3=image3_filename,
    )

    # Add the object to the session and save to the database
    session.add(new_schedule)
    session.commit()
    session.refresh(new_schedule)

    return Response(status_code=200)


# qa 삭제
from fastapi.responses import JSONResponse


@schedule_router.delete("/{id}")
async def delete_schedule(id: int,
                          user: str = Depends(authenticate),
                          session: Session = Depends(get_session)):
    check_admin(user)

    schedule = session.get(BusSchedule, id)

    if schedule:
        session.delete(schedule)
        session.commit()
        return JSONResponse(content={"message": "삭제가 완료되었습니다."}, status_code=200)

    # QA가 존재하지 않는 경우, 404 응답 반환
    return JSONResponse(content={"message": "Schedule not found"}, status_code=404)


@schedule_router.put("/{id}", response_class=RedirectResponse)
async def update_schedule(
        id: int,
        title: str = Form(...),
        image_name1: str = Form(None),
        image_name2: str = Form(None),
        image_name3: str = Form(None),
        image1: UploadFile = File(None),
        image2: UploadFile = File(None),
        image3: UploadFile = File(None),
        user: str = Depends(authenticate),
        session: Session = Depends(get_session),
):
    check_admin(user)

    schedule = session.get(BusSchedule, id)
    if not schedule:
        log.error(f"버스 시간표 수정 - 존재하지 않는 ID: {id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer QA not found",
        )

    if not image_name1:
        schedule.image_name1 = None
        schedule.image_data1 = None
    if not image_name2:
        schedule.image_name2 = None
        schedule.image_data2 = None
    if not image_name3:
        schedule.image_name3 = None
        schedule.image_data3 = None

    if image1:
        if not image1.content_type.startswith("image/"):
            log.error(f"버스 시간표 수정 - 잘못된 파일 형식: {image1.content_type}, 파일명: {image1.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미지 파일만 업로드할 수 있습니다."
            )
        schedule.image_data1 = await image1.read()
        schedule.image_name1 = image1.filename
    if image2:
        if not image2.content_type.startswith("image/"):
            log.error(f"버스 시간표 수정 - 잘못된 파일 형식: {image2.content_type}, 파일명: {image2.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미지 파일만 업로드할 수 있습니다."
            )
        schedule.image_data2 = await image2.read()
        schedule.image_name2 = image2.filename
    if image3:
        if not image3.content_type.startswith("image/"):
            log.error(f"버스 시간표 수정 - 잘못된 파일 형식: {image3.content_type}, 파일명: {image3.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미지 파일만 업로드할 수 있습니다."
            )
        schedule.image_data3 = await image3.read()
        schedule.image_name3 = image3.filename

    schedule.title = title

    # 변경 사항 저장
    session.add(schedule)
    session.commit()

    # 리다이렉션 수행
    return RedirectResponse(url='/adm/schedule', status_code=303)


def raise_exception(empty_val, message: str):
    if empty_val == '':
        log.error(f"버스 시간표 유효성 검사 실패: {message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )
