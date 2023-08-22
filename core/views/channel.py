from distutils.util import strtobool

from django.db.models import F
from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg.utils import swagger_auto_schema

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from core.filters import ArticleFilter
from core.models import Category, Article
from core.models import Language
from core.serializers import CategorySerializer, ArticleSerializer, ArticleCreateSerializer, \
    SpecificArticleCreateSerializer
from core.serializers import LanguageSerializer
from core.services.articles import GenerateArticleService
from genpoetry.permissions import TokenPermission


dont_count_param = openapi.Parameter('dont_count', openapi.IN_QUERY,
                                     description="Do not increase the counter of usages", type=openapi.TYPE_BOOLEAN)
query = openapi.Parameter('query', openapi.IN_QUERY, description="query", type=openapi.TYPE_STRING)
title = openapi.Parameter('title', openapi.IN_QUERY, description="title", type=openapi.TYPE_STRING)
key_terms = openapi.Parameter('key_terms', openapi.IN_QUERY, description="key_terms", type=openapi.TYPE_STRING)
language = openapi.Parameter('language', openapi.IN_QUERY, description="language", type=openapi.TYPE_STRING, default='english')
required_phrases = openapi.Parameter('required_phrases', openapi.IN_QUERY, description="required_phrases", type=openapi.TYPE_STRING)
min_characters_number = openapi.Parameter('min_characters_number', openapi.IN_QUERY, description="min_characters_number", type=openapi.TYPE_STRING)
max_characters_number = openapi.Parameter('max_characters_number', openapi.IN_QUERY, description="max_characters_number", type=openapi.TYPE_STRING)


class LanguageViewSet(ModelViewSet):
    model = Language
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = (TokenPermission,)
    pagination_class = None


class CategoryViewSet(ModelViewSet):
    model = Category
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (TokenPermission,)
    pagination_class = None


class ArticleViewSet(ModelViewSet):
    model = Article
    serializer_class = ArticleSerializer
    queryset = Article.objects.all()
    filterset_class = ArticleFilter
    permission_classes = (TokenPermission,)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        dont_update_usage = strtobool(self.request.query_params.get('dont_count', 'false'))
        if self.action == 'list' and not dont_update_usage:
            Article.objects.filter(id__in=queryset.values_list('id')).update(shown_times=F('shown_times') + 1)
        return queryset

    @swagger_auto_schema(manual_parameters=[dont_count_param])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def generate_article(self, request, *args, **kwargs) -> Response:
        kwargs['context'] = self.get_serializer_context()
        kwargs['data'] = {**request.data, **self.request.query_params.dict()}
        articles_number = int(kwargs['data'].get('articles_number', 1))
        articles = []
        for _ in range(articles_number):
            article = GenerateArticleService(*args, **kwargs).generate()
            articles.append(article)
        data = ArticleSerializer(articles, many=True).data
        headers = self.get_success_headers(data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class SpecificArticleViewSet(ArticleViewSet):
    serializer_class = SpecificArticleCreateSerializer
    queryset = Article.objects.all()
    filterset_class = None
    pagination_class = None

    permission_classes = (TokenPermission,)
    @swagger_auto_schema(manual_parameters=[query, title, key_terms, language, required_phrases, min_characters_number, max_characters_number])
    def generate_specific_article(self, request, *args, **kwargs) -> Response:
        serializer = SpecificArticleCreateSerializer(data=request.GET.dict())
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = ArticleSerializer(serializer.instance).data
        headers = self.get_success_headers(data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)