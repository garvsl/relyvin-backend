from typing import Annotated
from fastapi import APIRouter, Depends
from prisma import Prisma
from dependencies import DB

router = APIRouter()


@router.get("/users/", tags=["users"])
async def read_users(db: Prisma = DB):
    # users = await db.user.find_many()
    # return users
    print('hello')

@router.get("/users/me", tags=["users"])
async def read_user_me():
    return {"username": "fakecurrentuser"}


@router.get("/users/{username}", tags=["users"])
async def read_user(username: str):
    return {"username": username}