import datetime
import json
from fastapi import Depends, FastAPI, HTTPException, Request
from typing import Union
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from prisma import Prisma
from app.routers import influencers, scrapers, scraping, scripts, usernames
from app.routers import users
from app.dependencies import prisma, redis_client

# c53008b6-0d30-49e3-8f72-1cd33c1c0905

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
    
    session_id = session_id.split(" ")[1]

    session_data = redis_client.get(f"session:{session_id}")

    if session_data:
        session = json.loads(session_data)
        print("Found cache")
    else:

        session = await prisma.session.find_unique(
            where={
                'sid':session_id
            }
        )
        
        if not session:
            return JSONResponse(
                status_code=401,
                content={"detail":"Invalid session"}
            )
        
        session = json.loads(session.data)

        print("Creating cache")
        redis_client.setex(
            f"session:{session_id}",
            31536000,  #1 year
            json.dumps(session)
        )

    
    if 'expiresAt' in session and session['expiresAt'] < datetime.datetime.now(datetime.UTC).isoformat():
        return JSONResponse(
            status_code=401,
            content={"detail": "Expired session"}
        )
    
    redis_client.expire(f"session:{session_id}", 31536000) #refresh session

    request.state.session = session
    response = await call_next(request)
    return response
    


@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(users.router)
app.include_router(scripts.router)
app.include_router(scrapers.router)
app.include_router(influencers.router)
app.include_router(scraping.router)
app.include_router(usernames.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True)