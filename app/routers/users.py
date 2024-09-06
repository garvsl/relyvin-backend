from typing import Annotated
import uuid
import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from prisma import Prisma
from app.dependencies import DB
from app.prisma.db.user import create_session, get_user_full

router = APIRouter()

@router.post("/users/login", tags=["users"])
async def login_user(email:str, password:str, db: Prisma = DB):
    user = await get_user_full(email, db)
    if not user or not bcrypt.checkpw(password.encode(), user.hashedPassword.encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    session = create_session(uuid.uuid4(), {'userId':user.id}, db)
    
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