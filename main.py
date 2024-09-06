from fastapi import FastAPI
from typing import Union
from contextlib import asynccontextmanager
from prisma import Prisma

@asynccontextmanager
async def lifespan(app:FastAPI):
    prisma = Prisma()
    await prisma.connect()
    print('Connecting to Prisma')

    yield

    await prisma.disconnect()
    print('Disconnecting from Prisma')


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True)