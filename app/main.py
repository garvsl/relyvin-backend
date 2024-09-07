import datetime
import json
from fastapi import Depends, FastAPI, HTTPException, Request
from typing import Union
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from prisma import Prisma
from routers import users
from app.dependencies import prisma

@asynccontextmanager
async def lifespan(app:FastAPI):
    await prisma.connect()
    print('Connecting to Prisma')
    yield

    await prisma.disconnect()
    print('Disconnecting from Prisma')


app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def session_middleware(request: Request, call_next):
    session_id = request.headers.get("Authorization")

    if not session_id:
        return await call_next(request)

    session = await prisma.session.find_unique(
        where={
            'sid':session_id
        }
    )
    
    if not session or session.expiresAt < datetime.now(datetime.UTC):
        return JSONResponse(
            status_code=401,
            content={"detail":"Invalid or expired session"}
        )
    
    request.state.session = json.loads(session.data)    
    response = await call_next(request)
    return response
    


@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(users.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True)