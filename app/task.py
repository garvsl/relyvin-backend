import datetime
import os
import subprocess
from celery import Celery
from app.dependencies import process_dict

app = Celery(__name__)
app.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
app.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")


@app.task(bind=True)
def scraping(self, user) -> str:
    script_path = os.path.join(os.getcwd(), 'scraping_script', 'app.py')
    venv_path = os.path.join(os.getcwd(), 'scraping_script', 'venv', 'bin', 'python')
    if not os.path.exists(venv_path):
        venv_path = os.path.join(os.getcwd(), 'scraping_script', 'venv', 'Scripts', 'python.exe')
    if not os.path.exists(venv_path):
        raise FileNotFoundError(f"Virtual environment not found at {venv_path}")
    command = [venv_path, script_path, user]
    
    print(f"Executing command: {' '.join(command)}")

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        process_dict[self.request.id] = process  
    
        stdout, stderr = process.communicate()

  
        if process.returncode == 0:
            print(f"Script output: {stdout}")
            return f"Scraping completed successfully. Output: {stdout}"
        else:
            print(f"Script error output: {stderr}")
            return f"Scraping failed. Error: {stderr}"
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return f"Scraping failed due to unexpected error: {str(e)}"
    finally:
      
        if self.request.id in process_dict:
            del process_dict[self.request.id]



@app.task(bind=True)
def usernames_scrape(self, user) -> str:
    script_path = os.path.join(os.getcwd(), 'scraping_script', 'usernames.py')
    venv_path = os.path.join(os.getcwd(), 'scraping_script', 'venv', 'bin', 'python')
    if not os.path.exists(venv_path):
        venv_path = os.path.join(os.getcwd(), 'scraping_script', 'venv', 'Scripts', 'python.exe')
    if not os.path.exists(venv_path):
        raise FileNotFoundError(f"Virtual environment not found at {venv_path}")
    command = [venv_path, script_path, user]
    
    print(f"Executing command: {' '.join(command)}")

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        process_dict[self.request.id] = process  
    
        stdout, stderr = process.communicate()

  
        if process.returncode == 0:
            print(f"Script output: {stdout}")
            return f"Scraping completed successfully. Output: {stdout}"
        else:
            print(f"Script error output: {stderr}")
            return f"Scraping failed. Error: {stderr}"
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return f"Scraping failed due to unexpected error: {str(e)}"
    finally:
      
        if self.request.id in process_dict:
            del process_dict[self.request.id]