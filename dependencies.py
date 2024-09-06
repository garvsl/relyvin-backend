from fastapi import Depends
from prisma import Prisma

prisma = Prisma()

async def get_db() -> Prisma:
    return prisma

DB = Depends(get_db)