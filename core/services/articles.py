from core.serializers import ArticleCreateSerializer


class GenerateArticleService:

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def generate(self):
        serializer = ArticleCreateSerializer(*self.args, **self.kwargs)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer.instance

