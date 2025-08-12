# routes/pages.py
import os

from fastapi import APIRouter, Request
from pydantic_settings import BaseSettings
from starlette.responses import HTMLResponse, FileResponse
from starlette.templating import Jinja2Templates


class Settings(BaseSettings):
    kakao_api_key: str
    db_user: str
    db_password: str
    db_host: str

    class Config:
        env_file = ".env"


settings = Settings()

# 템플릿 디렉토리 설정
templates = Jinja2Templates(directory="templates")

page_router = APIRouter()


@page_router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@page_router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@page_router.get("/schedule", response_class=HTMLResponse)
async def schedule(request: Request):
    return templates.TemplateResponse("schedule.html", {"request": request})


@page_router.get("/ddock", response_class=HTMLResponse)
async def ddock(request: Request):
    return templates.TemplateResponse("ddock.html", {"request": request})


@page_router.get("/location", response_class=HTMLResponse)
async def location(request: Request):
    return templates.TemplateResponse("location.html", {"request": request, "kakao_api_key": settings.kakao_api_key})


@page_router.get("/qa", response_class=HTMLResponse)
async def qa(request: Request):
    return templates.TemplateResponse("qa.html", {"request": request})


@page_router.get("/lost", response_class=HTMLResponse)
async def lost(request: Request):
    return templates.TemplateResponse("lost.html", {"request": request})


@page_router.get("/recruit", response_class=HTMLResponse)
async def recruit(request: Request):
    return templates.TemplateResponse("recruit.html", {"request": request})


@page_router.get("/notice", response_class=HTMLResponse)
async def notice(request: Request):
    return templates.TemplateResponse("notice.html", {"request": request})


@page_router.get("/qa-form", response_class=HTMLResponse)
async def notice(request: Request):
    return templates.TemplateResponse("qa-form.html", {"request": request})


@page_router.get("/lost-form", response_class=HTMLResponse)
async def notice(request: Request):
    return templates.TemplateResponse("lost-form.html", {"request": request})


@page_router.get("/qa/detail", response_class=HTMLResponse)
async def qa_detail(request: Request):
    return templates.TemplateResponse("qa-detail.html", {"request": request})


@page_router.get("/qa/update", response_class=HTMLResponse)
async def qa_detail(request: Request):
    return templates.TemplateResponse("qa-update.html", {"request": request})


@page_router.get("/schedule", response_class=HTMLResponse)
async def qa_detail(request: Request):
    return templates.TemplateResponse("schedule.html", {"request": request})


@page_router.get("/schedule/detail", response_class=HTMLResponse)
async def qa_detail(request: Request):
    return templates.TemplateResponse("schedule-detail.html", {"request": request})


@page_router.get("/notice", response_class=HTMLResponse)
async def qa_detail(request: Request):
    return templates.TemplateResponse("notice.html", {"request": request})


@page_router.get("/notice/detail", response_class=HTMLResponse)
async def qa_detail(request: Request):
    return templates.TemplateResponse("notice-detail.html", {"request": request})


# admin
@page_router.get("/adm/login", response_class=HTMLResponse)
async def admin_login(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request})


@page_router.get("/adm", response_class=HTMLResponse)
async def admin(request: Request):
    return templates.TemplateResponse("admin/admin.html", {"request": request})


@page_router.get("/adm/schedule", response_class=HTMLResponse)
async def admin(request: Request):
    return templates.TemplateResponse("admin/schedule.html", {"request": request})


@page_router.get("/adm/ddock", response_class=HTMLResponse)
async def admin(request: Request):
    return templates.TemplateResponse("admin/ddock.html", {"request": request})


@page_router.get("/adm/customer", response_class=HTMLResponse)
async def admin(request: Request):
    return templates.TemplateResponse("admin/customer.html", {"request": request})


@page_router.get("/adm/lost", response_class=HTMLResponse)
async def admin(request: Request):
    return templates.TemplateResponse("admin/lost.html", {"request": request})


@page_router.get("/adm/notice", response_class=HTMLResponse)
async def admin(request: Request):
    return templates.TemplateResponse("admin/notice.html", {"request": request})


# robots, sitemap
# sitemap.xml을 루트(`/sitemap.xml`)에서 제공하도록 라우트 추가
@page_router.get("/sitemap.xml", response_class=FileResponse)
async def sitemap():
    sitemap_path = os.path.join("static", "sitemap.xml")
    return FileResponse(sitemap_path, media_type="application/xml")


@page_router.get("/robots.txt", response_class=FileResponse)
async def sitemap():
    robots_path = os.path.join("static", "robots.txt")
    return FileResponse(robots_path, media_type="text/plain")
