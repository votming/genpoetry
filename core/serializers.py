import json
import random
import re
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
    category = serializers.CharField(source='category.name', allow_null=True)
    language = serializers.CharField(source='language.name', allow_null=True)

    class Meta:
        model = Article
        fields = '__all__'


class SpecificArticleCreateSerializer(serializers.Serializer):
    id = serializers.IntegerField(default=None, required=False)
    model = serializers.CharField(default='gpt-4', required=False, max_length=50)
    query = serializers.CharField(max_length=20000, default=None)
    title = serializers.CharField(max_length=1000, default=None)
    status = serializers.CharField(max_length=15, default='done', required=False)
    key_terms = serializers.CharField(max_length=10000, default=None)
    language = serializers.CharField(max_length=100, default='english')
    required_phrases = serializers.CharField(max_length=10000, default=None)
    min_characters_number = serializers.IntegerField(required=False, default=400, min_value=10, max_value=9000)
    max_characters_number = serializers.IntegerField(required=False, default=900, min_value=20, max_value=10000)

    def create(self, validated_data: dict) -> Article:
        language = Language.objects.filter(name=validated_data["language"].capitalize()).first()
        language_name = language.name.lower() if language is not None else validated_data["language"]
        query = f'Description: {validated_data["query"]}\n' if validated_data['query'] else ''
        title = f'Title: {validated_data["title"]}\n' if validated_data['title'] else ''
        key_terms = f'Keyterms: {validated_data["key_terms"]}\n' if validated_data['key_terms'] else ''
        language_text = f'Language: {language_name}\n'
        required_phrases = f'These words/phrases must be contained in the text literally, as is: ' \
                           f'{validated_data["required_phrases"]}\n' if validated_data['required_phrases'] else ''

        prompt = f"""Write an article, corresponding to this: \n{query}{title}{key_terms}{language_text}{required_phrases}
From {validated_data["min_characters_number"]} to {validated_data["max_characters_number"]} characters. Also generate me a random person's name (language: {language.name}). The name should contain two words.
In response return JSON with fields: title, text, author_name"""
        print(f"PROMPT IS: {prompt}")
        title, text, author_name = self.generate_text(prompt)
        params = {
            'params': dict(model=validated_data['model'], language=validated_data["language"],
                           query=validated_data["query"], key_terms=validated_data["key_terms"],
                           required_phrases=validated_data["required_phrases"]),
            'language': language, 'text': text, 'status': validated_data['status'],
            'title': title, 'author_name': author_name
        }

        if validated_data.get('id'):
            Article.objects.filter(id=validated_data['id']).update(**params)
            article = Article.objects.get(id=validated_data['id'])
        else:
            article = Article.objects.create(**params)
        return article
        # (params=dict(model=validated_data['model'], language=validated_data["language"],
        #             query=validated_data["query"], key_terms=validated_data["key_terms"],
        #             required_phrases=validated_data["required_phrases"]),
        # language=language, text=text,
        # title=validated_data["title"] or 'No title')

    def generate_text(self, prompt):
        chatgpt_response_text = GenerateChatGPTQuote(request=prompt).generate()
        data = json.loads(chatgpt_response_text)
        # matches = re.findall(r'Content:(.+)', chatgpt_response_text, re.DOTALL)
        # if len(matches) == 0:
        #     chatgpt_response_text = GenerateChatGPTQuote(request=prompt).generate()
        #     matches = re.findall(r'Content:(.+)', chatgpt_response_text, re.DOTALL)
        # if len(matches) == 0:
        #     chatgpt_response_text = GenerateChatGPTQuote(request=prompt).generate()
        #     matches = re.findall(r'Content:(.+)', chatgpt_response_text, re.DOTALL)
        # text = matches[0]
        # if text.startswith('\n'):
        #     text = text[1:]
        return data['title'], data['text'], data['author_name']


class ArticleCreateSerializer(serializers.Serializer):
    id = serializers.IntegerField(default=None, required=False)
    model = serializers.CharField(default='gpt-4', required=False, max_length=50)
    min_characters_number = serializers.IntegerField(required=False, default=400, min_value=10, max_value=9000)
    max_characters_number = serializers.IntegerField(required=False, default=900, min_value=20, max_value=10000)
    category = serializers.CharField(default='Business', required=False)
    language = serializers.CharField(default='English', required=False)
    status = serializers.CharField(max_length=15, default='done', required=False)
    key_words = serializers.CharField(default=None, max_length=2000, required=False, allow_null=True)
    objectivity = serializers.BooleanField(default=False, required=False)
    officiality = serializers.BooleanField(default=False, required=False)
    temperature = serializers.FloatField(default=1, min_value=0, max_value=2, required=False)
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
        data = json.loads(chatgpt_response_text)
        # author_name_request = GenerateChatGPTQuote(
        #     request=f"Generate me a random person's name. Language: {language.name}. In the response write only the name (two words only)").generate()
        # author_name = ' '.join(author_name_request.split(' ')[:2])
        # chatgpt_response_text = chatgpt_response_text.replace('[', '').replace(']', '')
        # if '[' in chatgpt_response_text and ']' in chatgpt_response_text or \
        #         str(min_chars) in chatgpt_response_text and str(max_chars) in chatgpt_response_text:
        #     raise Exception('Appropriate text was not generated')
        # title, text = parse_article_response(chatgpt_response_text)
        chat_id = validated_data['chat_id'] or uuid.uuid4()
        params = {
            'params': validated_data, 'text': data['text'], 'title': data['title'], 'category': category,
            'language': language, 'chat_id': chat_id, 'author_name': data['author_name'], 'status': validated_data['status']
        }
        if validated_data.get('id'):
            Article.objects.filter(id=validated_data['id']).update(**params)
            article = Article.objects.get(id=validated_data['id'])
        else:
            article = Article.objects.create(**params)
        return article
        # return Article.objects.create(params=validated_data, text=text, title=title, category=category,
        #                               language=language, chat_id=chat_id, author_name=author_name)

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
