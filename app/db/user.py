import datetime
import json
from prisma import Prisma


async def get_user_full(email: str, prisma: Prisma):
    return await prisma.user.find_unique(
        where={
            "email":email
        },
        include={
            "Scraper":True,
            "Script":True
        }
    )

async def get_user(id: str, prisma: Prisma):
    user = await prisma.user.find_unique(
        where={
            "id":id
        },
        include={
            "Scraper":True,
            "Script":True
        }
    )
    return user.model_dump(exclude={"hashedPassword"}) 

async def get_users(prisma: Prisma):
    users = await prisma.user.find_many()
    return [user.model_dump(exclude={"hashedPassword"}) for user in users]

async def create_session(sid: str, data:dict, prisma: Prisma):
    session = await prisma.session.create(
        data={
            'sid':sid,
            'data':json.dumps(data),
            'expiresAt':datetime.datetime(9999,12,31)
        }
      );
    return session
    