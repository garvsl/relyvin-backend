from typing import Optional
from prisma import Prisma


async def get_usernames(prisma:Prisma, skip:Optional[int] = 0 ):
    return await prisma.username.find_many(
        take=100,
        skip=skip
    )

async def get_usernames_count(prisma:Prisma):
    return await prisma.username.count(
        where={
            'checked':False
        }
    )