
from typing import Optional
from fastapi import APIRouter
from prisma import Prisma

from app.dependencies import DB, USER
from app.db.influencer import get_influencer, get_influencers, get_influencers_count


router = APIRouter()


@router.get("/influencers/", tags=["influencers"])
async def read_influencers(db: Prisma = DB, user:str = USER, skip:Optional[int] = 0 ):
    return await get_influencers(db, skip)

@router.get("/influencers/count", tags=["influencers"])
async def read_influencers_count(db: Prisma = DB, user:str = USER):
    return await get_influencers_count(db)

@router.get("/influencers/find", tags=["influencers"])
async def find_influencer(handle:Optional[str] = None, email:Optional[str] = None, db: Prisma = DB, user:str = USER):
    return await get_influencer(db, handle, email)
    
    