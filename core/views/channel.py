from django.db.models import QuerySet
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from core.models import Category, Article
from core.serializers import CategorySerializer, ArticleSerializer, ArticleCreateSerializer
from genpoetry.permissions import TokenPermission


class CategoryViewSet(ModelViewSet):
    model = Category
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (TokenPermission,)


class ArticleViewSet(ModelViewSet):
    model = Article
    serializer_class = ArticleSerializer
    queryset = Article.objects.all()
    permission_classes = (TokenPermission,)

    def generate_article(self, request, *args, **kwargs) -> Response:
        kwargs['context'] = self.get_serializer_context()
        kwargs['data'] = {**request.data, **self.request.query_params.dict()}
        serializer = ArticleCreateSerializer(*args, **kwargs)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = ArticleSerializer(serializer.instance, many=True).data
        headers = self.get_success_headers(data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)
