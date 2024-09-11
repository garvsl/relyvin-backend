from typing import Optional
from fastapi import APIRouter
from prisma import Prisma

from app.dependencies import DB, USER
from app.db.script import create_script, get_scripts, update_script


router = APIRouter()

@router.get("/scripts/me", tags=["scripts"])
async def read_scripts_me(db:Prisma = DB, user:str = USER):
    return await get_scripts(user, db)

@router.post("/scripts/me/update", tags=["scripts"])
async def update_script_me(id:str, db:Prisma = DB, user:str = USER, title:Optional[str] = None, body:Optional[str] = None):
    return await update_script(id, db, title, body)

@router.post("/scripts/me/create", tags=["scripts"])
async def create_script_me(title:str, body:str, db:Prisma = DB, user:str = USER):
    return await create_script(user, db, title, body)