from django.urls import path

from core.views.channel import CategoryViewSet, ArticleViewSet

urlpatterns = [
    path('categories', CategoryViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('categories/<pk>', CategoryViewSet.as_view({'get': 'retrieve', 'patch': 'update'})),
    path('articles', ArticleViewSet.as_view({'get': 'list'})),
    path('articles/generate', ArticleViewSet.as_view({'get': 'generate_article'})),
    path('articles/<pk>', ArticleViewSet.as_view({'get': 'retrieve', 'patch': 'update'})),
]