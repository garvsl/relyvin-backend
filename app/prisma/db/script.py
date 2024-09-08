

from typing import Optional
from prisma import Prisma


async def get_scripts(id: str, prisma:Prisma):
    return await prisma.script.find_many(
        where={
            'userId': id
        },
        order={
        'created': 'asc',
        },
    )

async def update_script(id: str, prisma:Prisma, title:Optional[str] = None, body:Optional[str] = None ):
    data = {}
    if title:
        data['title'] = title
    if body:
        data['body'] = body

    return await prisma.script.update(
        where={
            'id': id
        },
        data=data
    )


async def create_script(id: str, prisma:Prisma, title:str, body:str):
    return await prisma.script.create(
        data={
            'title':title,
            'body':body,
            'userId':id
        }
    )