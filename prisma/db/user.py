from prisma import Prisma


async def get_user_full(email: str, prisma: Prisma):
    return await prisma.user.find_unique(
        where={
            "email":email
        }
    )

async def get_user(id: str, prisma: Prisma):
    user = await prisma.user.find_unique(
        where={
            "id":id
        }
    )
    return user.model_dump(exclude={"hashedPassword"}) 