
import datetime
import os
from time import sleep
from celery import Celery


app = Celery(__name__)
app.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
app.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")

@app.task
def dummy_task() -> str:
    sleep(10)
    # folder = "/Users/goofyahhgarv/Desktop/Projects/relyvin-backend/app/tmp/celery"
    # os.makedirs(folder, exist_ok=True)
    # now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%s")
    # with open(f"{folder}/task-{now}.txt", "w") as f:
    #     f.write("hello!")
    return print('hello')

