from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver


User = get_user_model()

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
            # Calculate weighted average
            ratings = self.ratings.all()
            if not ratings:
                stats = {
                    'average_rating': 0.0,
                    'rating_count': 0
                }
            else:
                total_weighted_rating = sum(r.rating * r.weight for r in ratings)
                total_weight = sum(r.weight for r in ratings)
                
                stats = {
                    'average_rating': total_weighted_rating / total_weight if total_weight > 0 else 0,
                    'rating_count': ratings.count()
                }
            
            # Cache for 1 hour
            cache.set(cache_key, stats, 3600)
        
        return stats

    def invalidate_rating_stats(self):
        cache_key = f'content_rating_stats_{self.id}'
        cache.delete(cache_key)
        

    def update_rating_stats(self):
        """
        Force update of rating statistics in cache
        """
        self.invalidate_rating_stats()
        
        return self.get_rating_stats()
    
    @property
    def average_rating(self):
        return self.get_rating_stats()['average_rating']
    
    @property
    def rating_count(self):
        return self.get_rating_stats()['rating_count']
    

class Rating(models.Model):
    content = models.ForeignKey(Content, related_name='ratings', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5)
        ],
    )
    weight = models.FloatField(default=1.0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(1)
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # To ensure validation is done
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    class Meta:
        unique_together = ['content', 'user']

@receiver(post_save, sender=Rating)
def invalidate_content_rating_cache(sender, instance, **kwargs):
    """
    Signal handler to invalidate content rating cache when a rating is created or updated
    """
    instance.content.invalidate_rating_stats()
