from django.urls import path
from core.views.channel import CategoryViewSet, ArticleViewSet, SpecificArticleViewSet
from core.views.channel import LanguageViewSet


urlpatterns = [
    path('categories', CategoryViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('categories/<pk>', CategoryViewSet.as_view({'get': 'retrieve', 'patch': 'update'})),
    path('languages', LanguageViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('languages/<pk>', LanguageViewSet.as_view({'get': 'retrieve', 'patch': 'update'})),
    path('articles', ArticleViewSet.as_view({'get': 'list'})),
    path('articles/generate', ArticleViewSet.as_view({'get': 'generate_article'})),
    path('articles/generate/specific', SpecificArticleViewSet.as_view({'get': 'generate_specific_article'})),
    path('articles/<pk>', ArticleViewSet.as_view({'get': 'retrieve', 'patch': 'update'})),
]
