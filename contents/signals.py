from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Rating

@receiver(post_save, sender=Rating)
def invalidate_content_rating_cache(sender, instance, **kwargs):
    """
    Signal handler to invalidate content rating cache when a rating is created or updated
    """
    instance.content.invalidate_rating_stats()
