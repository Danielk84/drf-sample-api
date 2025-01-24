from rest_framework import serializers

from .models import Article


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        exclude = ["is_active",]
        read_only_fields = ["user", "slug"]

    def update(self, instance, validated_data):
        instance.is_active = False
        return super().update(instance, validated_data)


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=64)
    password = serializers.CharField(max_length=32)


class AdminArticlesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["title", "slug", "is_active", "user"]
        read_only_fields = ["title", "slug", "user"]
        extra_kwargs = {
            'is_active': {'required': True}
        }