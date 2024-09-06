from typing import Annotated
import bcrypt
from fastapi import APIRouter, Depends
from prisma import Prisma
from dependencies import DB
from ..prisma.db.user import get_user_full

router = APIRouter()

@router.post("/users/login", tags=["users"])
async def login_user(email:str, password:str, db: Prisma = DB):
    user = await get_user_full(email, db)

    if not user:
        return False
    if not bcrypt.checkpw(password.encode(), user.hashedPassword.encode()):
        return False
    
    return user.model_dump(exclude={"hashedPassword"})


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