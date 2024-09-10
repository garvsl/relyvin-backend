
import datetime
import os
import subprocess
from time import sleep
from celery import Celery


app = Celery(__name__)
app.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
app.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")

@app.task
def scraping(user) -> str:
    script_path = os.path.join(os.getcwd(), 'scraping_script', 'app.py')
    venv_path = os.path.join(os.getcwd(), 'scraping_script', 'venv', 'bin', 'python')
    if not os.path.exists(venv_path):
        venv_path = os.path.join(os.getcwd(), 'scraping_script', 'venv', 'Scripts', 'python.exe')
    if not os.path.exists(venv_path):
        raise FileNotFoundError(f"Virtual environment not found at {venv_path}")
    command = [venv_path, script_path, user]
    
    print(f"Executing command: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Script output: {result.stdout}")
        return f"Scraping completed successfully. Output: {result.stdout}"
    except subprocess.CalledProcessError as e:
        print(f"Script error output: {e.stderr}")
        return f"Scraping failed. Error: {e.stderr}"
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return f"Scraping failed due to unexpected error: {str(e)}"