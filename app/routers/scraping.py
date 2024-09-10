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
def start(user:str = USER) -> TaskOut:
    r = task.scraping.delay(user)
    return _to_task_out(r)

@router.get("/scraping/stop", tags=['scraping'])
def stop(task_id: str, user:str = USER) -> TaskOut:
    task.app.control.revoke(task_id, terminate=True, signal="SIGKILL")
    r = task.app.AsyncResult(task_id)
    return _to_task_out(r)

@router.get("/scraping/status", tags=["scraping"])
def status(task_id: str, user:str = USER) -> TaskOut:
    r = task.app.AsyncResult(task_id)
    return _to_task_out(r)



