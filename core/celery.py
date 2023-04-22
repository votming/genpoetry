import time

from celery import Celery
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'genpoetry.settings')

import django
django.setup()
from core.models import Category
from core.models import Language
from core.services.articles import GenerateArticleService

app = Celery()
app.conf.broker_url = 'redis://localhost:6379/0'


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(300.0, generate_articles.s(), expires=5, name='Generate articles')


@app.task
def generate_articles():
    categories = Category.objects.all()
    languages = Language.objects.all()
    for category in categories:
        for language in languages:
            print('creating new article')
            data = dict(language=language.name, category=category.name)
            article = GenerateArticleService(data=data).generate()
            print(f'created {article}')
            time.sleep(15)
