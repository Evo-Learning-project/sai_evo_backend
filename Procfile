release: python manage.py migrate
web: daphne core.asgi:application --port $PORT --bind 0.0.0.0 -v2
celery: celery -A core worker -l INFO