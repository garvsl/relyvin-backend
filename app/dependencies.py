import datetime
import json
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prisma import Prisma

prisma = Prisma()

async def get_db() -> Prisma:
    return prisma

DB = Depends(get_db)

security = HTTPBearer()

async def get_current_user(request:Request, credentials:HTTPAuthorizationCredentials = Depends(security)):
    if not hasattr(request.state, 'session'):
        raise HTTPException(status_code=401, detail="Auth Required")
    return request.state.session['user_id']

USER = Depends(get_current_user)