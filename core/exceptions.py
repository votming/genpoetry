from rest_framework import serializers


class MinCharactersLessThanMaxCharactersError(serializers.ValidationError):
    default_detail = 'min_characters_number could not be less than max_characters_number'
