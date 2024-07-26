from rest_framework import serializers
from .models import Post, Comment, Like, Activity, FeedAlgorithm
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

class PostSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'user', 'content', 'created_at', 'updated_at']

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'post', 'content', 'parent', 'created_at', 'updated_at']

class LikeSerializer(serializers.ModelSerializer):
    content_type = serializers.PrimaryKeyRelatedField(queryset=ContentType.objects.all())

    class Meta:
        model = Like
        fields = ['id', 'user', 'content_type', 'object_id', 'created_at']
        read_only_fields = ['user']

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ['id', 'user', 'content_type', 'object_id', 'action', 'created_at']

class FeedAlgorithmSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedAlgorithm
        fields = ['id', 'name', 'description', 'query', 'weight', 'is_active', 'created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user