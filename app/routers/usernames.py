from typing import Optional
from fastapi import APIRouter
from prisma import Prisma

from app.dependencies import DB, USER
from app.db.username import get_usernames, get_usernames_count


router = APIRouter()


@router.get("/usernames/", tags=["usernames"])
async def read_usernames(db: Prisma = DB, user:str = USER, skip:Optional[int] = 0 ):
    return await get_usernames(db, skip)

@router.get("/usernames/count", tags=["usernames"])
async def read_usernames_count(db: Prisma = DB, user:str = USER):
    return await get_usernames_count(db)