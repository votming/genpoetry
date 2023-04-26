import uuid

from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=150, unique=True)
    keywords = models.CharField(max_length=2000, default=None, null=True)
    object_words = models.CharField(max_length=2000, default='')
    subject_words = models.CharField(max_length=2000, default='')
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)


class Language(models.Model):
    name = models.CharField(max_length=50, unique=True)
    priority = models.IntegerField(default=1)

class Article(models.Model):
    title = models.CharField(max_length=250)
    text = models.CharField(max_length=10000)
    params = models.JSONField()
    shown_times = models.IntegerField(default=0)
    category = models.ForeignKey(Category, null=True, default=None, on_delete=models.SET_NULL)
    language = models.ForeignKey(Language, null=True, default=None, on_delete=models.SET_NULL)
    chat_id = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)
