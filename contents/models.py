from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Avg, Count
import json

class Content(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # New fields for storing rating statistics
    rating_count = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    rating_distribution = models.JSONField(default=dict)  # Stores count for each rating value
    
    class Meta:
        indexes = [
            models.Index(fields=['rating_count']),
            models.Index(fields=['average_rating']),
        ]

class Rating(models.Model):
    content = models.ForeignKey(Content, related_name='ratings', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    weight = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['content', 'user']