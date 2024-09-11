

from typing import Optional
from prisma import Prisma


async def get_influencer(prisma:Prisma, handle:Optional[str] = None, email:Optional[str] = None):

    where = {}
    if handle:
        where['handle'] = handle
    if email:
        where['email'] = email

    return await prisma.influencer.find_unique(
        where=where
    )

async def get_influencers(prisma:Prisma, skip:Optional[int] = 0 ):
    return await prisma.influencer.find_many(
        take=100,
        skip=skip
    )

async def get_influencers_count(prisma:Prisma):
    return await prisma.influencer.count()