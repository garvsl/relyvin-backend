from fastapi import Depends, FastAPI
from typing import Union
from contextlib import asynccontextmanager
from prisma import Prisma
from routers import users
from dependencies import prisma

@asynccontextmanager
async def lifespan(app:FastAPI):
    await prisma.connect()
    print('Connecting to Prisma')
    yield

    await prisma.disconnect()
    print('Disconnecting from Prisma')


app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(users.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True)