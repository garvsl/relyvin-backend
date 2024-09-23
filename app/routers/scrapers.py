
from typing import Optional
from fastapi import APIRouter
from prisma import Prisma

from app.dependencies import DB, USER
from app.db.scraper import create_scraper, delete_scraper, get_scrapers


router = APIRouter()

@router.get("/scrapers/me", tags=["scrapers"])
async def read_scrapers_me(db:Prisma = DB, user:str = USER):
    return await get_scrapers(user, db)


@router.post("/scrapers/me/create", tags=["scrapers"])
async def create_scraper_me(email:str, password:str, db:Prisma = DB, user:str = USER):
    return await create_scraper(user, db, email, password)

@router.delete("/scrapers/me/delete", tags=["scrapers"])
async def delete_scraper_me(id:str, db:Prisma = DB, user:str = USER):
    return await delete_scraper(user, db, id)