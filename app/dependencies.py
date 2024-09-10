import datetime
import json
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prisma import Prisma
import redis

prisma = Prisma()

async def get_db() -> Prisma:
    return prisma

DB = Depends(get_db)


redis_client = redis.Redis(host='localhost', port=6379, db=0)

async def get_redis() -> redis:
    return redis_client

REDIS = Depends(get_redis)


security = HTTPBearer()

async def get_current_user(request:Request, credentials:HTTPAuthorizationCredentials = Depends(security)):
    if not hasattr(request.state, 'session'):
        raise HTTPException(status_code=401, detail="Auth Required")
    return request.state.session['userId']

USER = Depends(get_current_user)

process_dict = {}