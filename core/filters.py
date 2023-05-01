from core.models import Article
from django_filters import rest_framework as filters


class ArticleFilter(filters.FilterSet):
    shown_times = filters.NumberFilter()
    category = filters.CharFilter(field_name='category__name')
    language = filters.CharFilter(field_name='language__name')

    ordering = filters.OrderingFilter(fields=(('shown_times', 'shown_times'),))

    class Meta:
        model = Article
        fields = ('id', 'shown_times', 'category', 'language')
