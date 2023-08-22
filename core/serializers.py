import random
import uuid

from rest_framework import serializers

from configuration import Config
from core.exceptions import MinCharactersLessThanMaxCharactersError
from core.models import Category, Article, Language
from core.services.chatgpt import GenerateChatGPTQuote
from core.utils import parse_article_response


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
    category = serializers.CharField(default='Business', required=False)
    language = serializers.CharField(default='English', required=False)
    key_words = serializers.CharField(default=None, max_length=2000, required=False, allow_null=True)
    objectivity = serializers.BooleanField(default=False, required=False)
    officiality = serializers.BooleanField(default=False, required=False)
    temperature = serializers.FloatField(default=0.3, min_value=0, max_value=2, required=False)
    request = serializers.CharField(default=None, max_length=10000, allow_null=True)
    chat_id = serializers.CharField(default=None, max_length=100, allow_null=True)

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        attrs['request'] = self._generate_request(attrs) if attrs['request'] is None else attrs['request']
        if attrs['max_characters_number'] < attrs['min_characters_number']:
            raise serializers.ValidationError({'min_characters_number': MinCharactersLessThanMaxCharactersError()})
        return attrs

    def create(self, validated_data: dict) -> Article:
        category = Category.objects.filter(name=validated_data.get('category')).first()
        language = Language.objects.get(name=validated_data.get('language'))
        min_chars, max_chars = validated_data['min_characters_number'], validated_data['max_characters_number']
        chatgpt_response_text = GenerateChatGPTQuote(**validated_data).generate()
        author_name = GenerateChatGPTQuote(request=f"Generate me a random person's name. Language: {language.name}. In the response write only the name (two words only)").generate()
        if '[' in chatgpt_response_text and ']' in chatgpt_response_text or \
                str(min_chars) in chatgpt_response_text and str(max_chars) in chatgpt_response_text:
            raise Exception('Appropriate text was not generated')
        title, text = parse_article_response(chatgpt_response_text)
        chat_id = validated_data['chat_id'] or uuid.uuid4()

        return Article.objects.create(params=validated_data, text=text, title=title, category=category,
                                      language=language, chat_id=chat_id, author_name=author_name)

    def _generate_request(self, validated_data: dict) -> str:
        """settings = ''
        if validated_data['objectivity'] is True:
           settings += 'You should add true facts in the article.'
        if validated_data['officiality'] is True:
           settings += 'You should use official and formal language in the article.'
        if validated_data['key_words'] is not None:
           settings += f'You have to use this words in the article: {validated_data["key_words"]}.''"""
        category = Category.objects.get(name=validated_data['category'])
        category_object = random.choice(category.object_words.replace(', ', ',').split(','))
        category_subject = random.choice(category.subject_words.replace(', ', ',').split(','))
        return Config.TITLE_PROMPT.format(
            category=category.name,
            category_object=category_object,
            category_subject=category_subject,
            chars_min=validated_data['min_characters_number'],
            chars_max=validated_data['max_characters_number'],
            language=validated_data['language'],
        )
