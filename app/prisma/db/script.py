

from prisma import Prisma


async def get_scripts(id: str, prisma:Prisma):
    return await prisma.script.find_many(
        where={
            'userId': id
        },
        order={
        'created': 'desc',
        },
    )

# async def update_script(id: str, prisma:Prisma):
#     return await prisma.script.find_first(
#         where={
#             'id': id
#         },
#         order={
#         'created': 'desc',
#         },
#     )
