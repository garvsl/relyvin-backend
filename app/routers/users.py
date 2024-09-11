import json
from typing import Annotated
import uuid
import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from prisma import Prisma
import redis
from app.dependencies import DB, REDIS, USER
from app.db.user import create_session, get_user, get_user_full, get_users

router = APIRouter()

@router.post("/users/login", tags=["users"])
async def login_user(email:str, password:str, db: Prisma = DB, redis_client: redis = REDIS):
    user = await get_user_full(email, db)
    if not user or not bcrypt.checkpw(password.encode(), user.hashedPassword.encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    session = await create_session(str(uuid.uuid4()), {'userId':user.id}, db)
    redis_client.setex(
        f"session:{session.sid}",
        31536000,  #1 year
        json.dumps({'userId':user.id})
    )
    return {
        'user': user.model_dump(exclude={"hashedPassword"}),
        'session_id': session.sid
    }


@router.get("/users/", tags=["users"])
async def read_users(db: Prisma = DB, user:str = USER):
    return await get_users(db)

    
@router.get("/users/me", tags=["users"])
async def read_user_me(db:Prisma = DB, user:str = USER):
    return await get_user(user, db)


