import time
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "genpoetry.settings")
django.setup()
from celery import Celery

from core.models import Article
from core.models import Category
from core.models import Language
from core.services.articles import GenerateArticleService

celery = Celery()
celery.conf.broker_url = 'redis://localhost:6379/0'


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(30.0, generate_articles.s(), expires=60, name='Generate articles')


@celery.task
def generate_articles():
    print('start generating')
    categories = Category.objects.all()
    languages = Language.objects.all()
    for language in languages:
        for _ in range(language.priority):
            for category in categories:
                for _ in range(category.priority):
                    generate_article(category, language)
    print('generating finished')


def generate_article(category, language):
    if 20 < Article.objects.filter(category=category, language=language, shown_times=0).count():
        print(f'No more articles for {category.name} ({language.name})')
        return
    print(f'creating a new article [{category.name}, {language.name}]')
    data = dict(language=language.name, category=category.name)
    article = GenerateArticleService(data=data).generate()
    print(f'created {article}')
    time.sleep(18)
