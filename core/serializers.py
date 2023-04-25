import uuid

from rest_framework import serializers

from configuration import Config
from core.exceptions import MinCharactersLessThanMaxCharactersError
from core.models import Category, Article, Language
from core.services.chatgpt import GenerateChatGPTQuote


class LanguageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Language
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = '__all__'


class ArticleSerializer(serializers.ModelSerializer):
    params = serializers.JSONField(read_only=True)
    category = serializers.CharField(source='category.name')
    language = serializers.CharField(source='language.name')

    class Meta:
        model = Article
        fields = '__all__'


class ArticleCreateSerializer(serializers.Serializer):
    model = serializers.CharField(default='gpt-3.5-turbo', required=False, max_length=50)
    min_characters_number = serializers.IntegerField(required=False, default=400, min_value=10, max_value=9000)
    max_characters_number = serializers.IntegerField(required=False, default=900, min_value=20, max_value=10000)
    category = serializers.CharField(default=None, required=False)#serializers.SlugRelatedField(default=None, slug_field='name', queryset=Category.objects.all(), required=False)
    language = serializers.CharField(default='English', required=False)#serializers.SlugRelatedField(default=None, slug_field='name', queryset=Language.objects.all(), required=False)
    key_words = serializers.CharField(default=None, max_length=2000, required=False, allow_null=True)
    objectivity = serializers.BooleanField(default=False, required=False)
    officiality = serializers.BooleanField(default=False, required=False)
    temperature = serializers.FloatField(default=0.3, min_value=0, max_value=2, required=False)
    request = serializers.CharField(default=Config.DEFAULT_CHATGPT_PROMPT, max_length=10000, allow_null=True)
    chat_id = serializers.CharField(default=None, max_length=100, allow_null=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs['request'] = self._generate_request(attrs)
        if attrs['max_characters_number'] < attrs['min_characters_number']:
            raise serializers.ValidationError({'min_characters_number': MinCharactersLessThanMaxCharactersError()})

        return attrs

    def create(self, validated_data) -> list[Article]:
        category = Category.objects.filter(name=validated_data.get('category')).first()
        language = Language.objects.get(name=validated_data.get('language'))
        title_request = f'{Config.TITLE_PROMPT} ' + (f'Theme: {category.name}' if category is not None else '')
        title = GenerateChatGPTQuote(request=title_request).generate()
        validated_data['request'] = validated_data["request"] or f'{Config.DEFAULT_CHATGPT_PROMPT} Title is: {title}'
        text = GenerateChatGPTQuote(**validated_data).generate()
        chat_id = validated_data['chat_id'] or uuid.uuid4()

        return Article.objects.create(params=validated_data, text=text, title=title, category=category,
                                      language=language, chat_id=chat_id)

    def _generate_request(self, validated_data):
        settings = ''
        if validated_data['objectivity'] is True:
            settings += 'You should add true facts in the article.'
        if validated_data['officiality'] is True:
            settings += 'You should use official and formal language in the article.'
        if validated_data['key_words'] is not None:
            settings += f'You have to use this words in the article: {validated_data["key_words"]}.'
        if validated_data['category'] is not None:
            settings += f'The main theme of the text should be "{validated_data["category"]}"'
        out = f' The number of symbols of the text must be between {validated_data["min_characters_number"]} and ' \
              f'{validated_data["max_characters_number"]}. Use only {validated_data["language"]} language. {settings}'

        return f'{validated_data["request"]} {out}'
