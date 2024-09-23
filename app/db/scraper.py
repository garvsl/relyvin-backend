


from typing import Optional
import bcrypt
from prisma import Prisma


async def get_scrapers(id: str, prisma:Prisma):
    return await prisma.scraper.find_many(
        where={
            'userId': id
        },
        # order={
        # 'created': 'asc',
        # },
    )


async def create_scraper(id: str, prisma:Prisma, email:str, password:str):
    return await prisma.scraper.create(
        data={
            'email':email,
            'password':password,
            'userId':id
        }
    )

async def delete_scraper(userId: str, prisma:Prisma, id:str):
    return await prisma.scraper.delete(
        where={
            'id':id,
            'userId':userId
        }
    )