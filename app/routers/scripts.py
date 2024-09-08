from fastapi import APIRouter
from prisma import Prisma

from app.dependencies import DB, USER
from app.prisma.db.script import get_scripts


router = APIRouter()

@router.get("/scripts/me", tags=["scripts"])
async def read_script_me(db:Prisma = DB, user:str = USER):
    return await get_scripts(user, db)