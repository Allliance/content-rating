from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.cache import cache
from django.db.models import Avg, Count


class Content(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_rating_stats(self):
        """
        Get rating statistics from cache or calculate and cache them
        """
        cache_key = f'content_rating_stats_{self.id}'
        stats = cache.get(cache_key)
        
        if stats is None:
            # Calculate stats
            rating_data = self.ratings.aggregate(
                avg_rating=Avg('rating'),
                rating_count=Count('id')
            )
            
            stats = {
                'average_rating': float(rating_data['avg_rating'] or 0),
                'rating_count': rating_data['rating_count']
            }
            
            # Cache for 1 hour
            cache.set(cache_key, stats, 3600)
        
        return stats

    def update_rating_stats(self):
        """
        Force update of rating statistics in cache
        """
        cache_key = f'content_rating_stats_{self.id}'
        cache.delete(cache_key)
        return self.get_rating_stats()
    
    @property
    def average_rating(self):
        return self.get_rating_stats()['average_rating']
    
    @property
    def rating_count(self):
        return self.get_average_rating()['rating_count']
    

class Rating(models.Model):
    user_id = models.IntegerField()
    content = models.ForeignKey(Content, related_name='ratings', on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['content', 'user_id']