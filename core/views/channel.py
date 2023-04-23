from django.db.models import F

from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from core.filters import ArticleFilter
from core.models import Category, Article
from core.models import Language
from core.serializers import CategorySerializer, ArticleSerializer, ArticleCreateSerializer
from core.serializers import LanguageSerializer
from core.services.articles import GenerateArticleService
from genpoetry.permissions import TokenPermission


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
        if self.action == 'list' and 'dont_count' not in self.request.query_params:
            Article.objects.filter(id__in=queryset.values_list('id')).update(shown_times=F('shown_times') + 1)
        return queryset

    def generate_article(self, request, *args, **kwargs) -> Response:
        kwargs['context'] = self.get_serializer_context()
        kwargs['data'] = {**request.data, **self.request.query_params.dict()}
        articles_number = kwargs['data'].get('articles_number', 1)
        articles = []
        for _ in range(articles_number):
            article = GenerateArticleService(*args, **kwargs).generate()
            articles.append(article)
        data = ArticleSerializer(articles, many=True).data
        headers = self.get_success_headers(data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)
