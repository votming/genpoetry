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
    for category in categories:
        for language in languages:
            for _ in range(language.priority):
                if 50 < Article.objects.filter(category=category, language=language, shown_times=0).count():
                    continue
                print('creating new article')
                data = dict(language=language.name, category=category.name)
                article = GenerateArticleService(data=data).generate()
                print(f'created {article}')
                time.sleep(20)
    print('generating finished')
