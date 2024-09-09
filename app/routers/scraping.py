from multiprocessing.pool import AsyncResult
from fastapi import APIRouter
from prisma import Prisma
from pydantic import BaseModel
from app import task
from app.dependencies import DB, USER


router = APIRouter()

class TaskOut(BaseModel):
    id: str
    status: str

    
def _to_task_out(r: AsyncResult) -> TaskOut:
    return TaskOut(id=r.task_id, status=r.status)


@router.get("/scraping/start", tags=["scraping"])
def start() -> TaskOut:
    r = task.dummy_task.delay()
    return _to_task_out(r)


@router.get("/scraping/status", tags=["scraping"])
def status(task_id: str) -> TaskOut:
    r = task.app.AsyncResult(task_id)
    return _to_task_out(r)



@router.post("/scraping/me/start", tags=["scraping"])
async def start_scraping(db:Prisma = DB, user:str = USER):
    # current user scraper exists check
    # current user script exists check
    # usernames num and ensure greater than zero
    # make sure there can only be certain number of tasks running from a user
    # error tracking on the scraper proper
    print('hi')