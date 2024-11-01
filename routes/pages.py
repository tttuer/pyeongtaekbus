# routes/pages.py
from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

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
    return templates.TemplateResponse("location.html", {"request": request})

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