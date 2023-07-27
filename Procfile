release: python manage.py migrate
web: gunicorn --workers=10 core.wsgi
celery: celery -A core worker -l INFO
beat: celery -A core beat -l info -S django