from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from database.connection import conn
from routes.events import event_router
from routes.users import users_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    conn()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(users_router, prefix='/users')
app.include_router(event_router, prefix='/events')

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)