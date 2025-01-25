from rest_framework import serializers
from .models import Content, Rating

class ContentSerializer(serializers.ModelSerializer):
    user_rating = serializers.FloatField(read_only=True, allow_null=True)
    average_rating = serializers.FloatField(read_only=True)
    rating_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Content
        fields = ['id', 'title', 'user_rating', 'average_rating', 'rating_count', 'created_at']

class RatingSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    rating = serializers.IntegerField(min_value=0, max_value=5)