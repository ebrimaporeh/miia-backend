# utils/serializers.py

from rest_framework import serializers

class AbsoluteImageField(serializers.ImageField):
    def to_representation(self, value):
        request = self.context.get('request')

        if not value:
            return None

        url = value.url

        if request:
            return request.build_absolute_uri(url)

        return url