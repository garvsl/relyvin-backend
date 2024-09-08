

from prisma import Prisma


async def get_script(id: str, prisma:Prisma):
    return await prisma.script.find_first(
        where={
            'userId': id
        },
        order={
        'created': 'desc',
        },
    )
