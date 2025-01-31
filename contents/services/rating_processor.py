from kafka import KafkaConsumer
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg
from ..models import Rating, Content
import json
import logging

logger = logging.getLogger(__name__)

class RatingProcessor:
    def __init__(self):
        self.consumer = KafkaConsumer(
            'ratings',
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='rating_processor_group'
        )
    
    def check_rating_anomaly(self, content_id, rating_value):
        """Check if there's an unusual spike in specific rating value"""
        time_threshold = timezone.now() - timedelta(hours=1)
        
        recent_ratings = Rating.objects.filter(
            content_id=content_id,
            created_at__gte=time_threshold
        )
        
        total_recent = recent_ratings.count()
        if total_recent < 10:  # Not enough data to detect anomaly
            return False
            
        rating_value_count = recent_ratings.filter(rating=rating_value).count()
        
        # If more than 80% of recent ratings are the same value, consider it suspicious
        return (rating_value_count / total_recent) > 0.8
    
    def process_ratings_batch(self, content_id):
        """Process all unprocessed ratings for a content"""
        try:
            content = Content.objects.get(id=content_id)
            unprocessed_ratings = Rating.objects.filter(
                content_id=content_id,
                processed=False
            )
            
            for rating in unprocessed_ratings:
                # Check for anomaly and adjust weight if necessary
                if self.check_rating_anomaly(content_id, rating.rating):
                    rating.weight = settings.ANOMALY_WEIGHT_PENALTY
                    rating.save()
            
            all_ratings = Rating.objects.filter(content_id=content_id)
            
            # Calculate weighted average
            weighted_sum = sum(r.rating * r.weight for r in all_ratings)
            weight_sum = sum(r.weight for r in all_ratings)
            new_average = weighted_sum / weight_sum if weight_sum > 0 else 0
            
            # Get rating distribution
            distribution = dict(all_ratings.values('rating')
                              .annotate(count=Count('rating'))
                              .values_list('rating', 'count'))
            
            # Update content statistics
            content.average_rating = new_average
            content.rating_count = all_ratings.count()
            content.rating_distribution = distribution
            content.save()
            
            # Mark all processed
            unprocessed_ratings.update(processed=True)
            
        except Exception as e:
            logger.error(f"Error processing ratings for content {content_id}: {str(e)}")
    
    def run(self):
        """Main processing loop"""
        logger.info("Rating processor started")
        for message in self.consumer:
            try:
                rating_data = message.value
                content_id = rating_data['content_id']
                self.process_ratings_batch(content_id)
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")