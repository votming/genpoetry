import time
import os, django
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "genpoetry.settings")
django.setup()
from celery import Celery

from core.models import Article
from core.models import Category
from core.models import Language
from core.services.articles import GenerateArticleService

celery = Celery()
celery.conf.broker_url = 'redis://localhost:6379/0'

from core.serializers import SpecificArticleCreateSerializer, ArticleSerializer, ArticleCreateSerializer


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
    try:
        if 3 < Article.objects.filter(category=category, language=language, shown_times=0).count():
            print(f'No more articles for {category.name} ({language.name})')
            return
        print(f'creating a new article [{category.name}, {language.name}]')
        data = dict(language=language.name, category=category.name)
        article = GenerateArticleService(data=data).generate()
        print(f'created {article}')
    except Exception as ex:
        time.sleep(10)
        print(f'error on creating an article: {ex}')


@celery.task
def generate_specific_article_async(data):
    try:
        print('start generate_specific_article_async')
        serializer = SpecificArticleCreateSerializer(data=data)
        serializer.is_valid(raise_exception=False)
        instance = serializer.save()
        instance.save()
        print('generate_specific_article_async finished')
    except Exception as ex:
        print(f'generate_specific_article_async FAILED {ex}')
        print(traceback.format_exc())
        article = Article.objects.get(id=data['id'])
        article.status = 'failed'
        article.save()


@celery.task
def generate_article_async(data):
    try:
        print('start generate_article_async')
        print(data)
        serializer = ArticleCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        instance.save()
        #article = GenerateArticleService(**data).generate()
        print('generate_article_async finished')
    except Exception as ex:
        print(f'generate_article_async FAILED {ex}')
        print(traceback.format_exc())
        article = Article.objects.get(id=data['id'])
        article.status = 'failed'
        article.text = str(ex)
        article.save()
