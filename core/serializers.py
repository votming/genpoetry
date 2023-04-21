from rest_framework import serializers

from configuration import Config
from core.exceptions import MinCharactersLessThanMaxCharactersError
from core.models import Category, Article
from core.services.articles import GenerateArticleService
from core.services.chatgpt import GenerateChatGPTQuote


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = '__all__'


class ArticleSerializer(serializers.ModelSerializer):
    params = serializers.JSONField(read_only=True)

    class Meta:
        model = Article
        fields = '__all__'


class ArticleCreateSerializer(serializers.Serializer):
    articles_number = serializers.IntegerField(required=False, default=1, min_value=1, max_value=10)
    model = serializers.CharField(default='gpt-3.5-turbo', required=False, max_length=50)
    min_characters_number = serializers.IntegerField(required=False, default=400, min_value=10, max_value=9000)
    max_characters_number = serializers.IntegerField(required=False, default=900, min_value=20, max_value=10000)
    category = serializers.PrimaryKeyRelatedField(default=None, queryset=Category.objects.all(), required=False)
    key_words = serializers.CharField(default=None, max_length=2000, required=False, allow_null=True)
    objectivity = serializers.BooleanField(default=False, required=False)
    officiality = serializers.BooleanField(default=False, required=False)
    temperature = serializers.FloatField(default=1.5, min_value=0, max_value=2, required=False)
    language = serializers.CharField(default='English', max_length=100)
    request = serializers.CharField(default=Config.DEFAULT_CHATGPT_PROMPT, max_length=10000, allow_null=True)
    chat_id = serializers.CharField(default=None, max_length=100, allow_null=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs['max_characters_number'] < attrs['min_characters_number']:
            raise serializers.ValidationError({'min_characters_number': MinCharactersLessThanMaxCharactersError()})
        return attrs

    def create(self, validated_data) -> list[Article]:
        if validated_data['request'] is None:
            validated_data['request'] = Config.DEFAULT_CHATGPT_PROMPT

        validated_data['request'] = self._generate_request(validated_data)

        #texts = [x for x in range(validated_data['articles_number'])]
        texts = GenerateChatGPTQuote(**validated_data).generate()

        data = dict(params=validated_data)
        if validated_data['chat_id'] is not None:
            data['chat_id'] = validated_data['chat_id']
        articles = [Article(text=text, **data) for text in texts]
        #self.output = Article.objects.bulk_create(articles)
        #return self.output
        return Article.objects.bulk_create(articles)

    def _generate_request(self, validated_data):
        settings = ''
        if validated_data['objectivity'] is True:
            settings += 'You should add true facts in the article.'
        if validated_data['officiality'] is True:
            settings += 'You should use official and formal language in the article.'
        if validated_data['key_words'] is not None:
            settings += f'You have to use this words in the article: {validated_data["key_words"]}.'
        if validated_data['category'] is None:
            validated_data['category'] = 'the wealth'
        settings += f'The main theme of the article should be "{validated_data["category"]}"'
        out = f'. Number of characters of the article must be between {validated_data["min_characters_number"]} and ' \
              f'{validated_data["max_characters_number"]}. Use only {validated_data["language"]} language. {settings}'

        return f'{validated_data["request"]} {out}'
