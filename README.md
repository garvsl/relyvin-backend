# relyvin-backend

export PYTHONPATH="$PYTHONPATH:/Users/goofyahhgarv/Desktop/Projects/relyvin-backend"
python3 app/main.py
prisma db push --schema="./app/prisma/schema.prisma"

.env:
RESEND_API_KEY=
DATABASE_URL=

cd app

python3 main.py

redis-server

celery -A app.task worker -l INFO -f celery.logs

Scraping script:

root folder then run
export PYTHONPATH="$PYTHONPATH:/Users/goofyahhgarv/Desktop/Projects/relyvin-backend/scraping_script"
python3 -m scraping_script.final c58cd9c3-76da-4790-92f8-54e27d432cc2
