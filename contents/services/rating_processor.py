from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg
from ..models import Rating, Content
import json
import logging
import time

logger = logging.getLogger(__name__)

class RatingProcessor:
    def __init__(self):
        self.topic_name = 'ratings'
        self.connect_with_retry()

    def connect_with_retry(self, max_retries=5, retry_delay=5):
        """Attempt to connect to Kafka with retries"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to Kafka brokers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
                self.consumer = KafkaConsumer(
                    self.topic_name,
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    group_id='rating_processor_group',
                    auto_offset_reset='earliest',
                    enable_auto_commit=True,
                    session_timeout_ms=30000,
                    heartbeat_interval_ms=10000
                )
                logger.info("Successfully connected to Kafka")
                return
            except NoBrokersAvailable:
                if attempt < max_retries - 1:
                    logger.warning(f"Failed to connect to Kafka. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    logger.error("Failed to connect to Kafka after maximum retries")
                    raise

    def run(self):
        """Main processing loop"""
        logger.info("Rating processor started")
        while True:
            try:
                logger.info("Waiting for messages...")
                for message in self.consumer:
                    try:
                        rating_data = message.value
                        content_id = rating_data['content_id']
                        logger.info(f"Processing rating for content_id: {content_id}")
                        self.process_ratings_batch(content_id)
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
            except Exception as e:
                logger.error(f"Consumer error: {str(e)}")
                time.sleep(5)  # Wait before attempting to reconnect
                self.connect_with_retry()


    def check_rating_anomaly(self, content_id, rating_value):
        """Check if there's an unusual spike in specific rating value"""
        time_threshold = timezone.now() - timedelta(hours=1)
        
        recent_ratings = Rating.objects.filter(
            content_id=content_id,
            created_at__gte=time_threshold
        )
        
        total_recent = recent_ratings.count()
        if total_recent < settings.MIN_RATE_COUNT:  # Not enough data to detect anomaly
            return False
            
        rating_value_count = recent_ratings.filter(rating=rating_value).count()
        
        # If more than 80% of recent ratings are the same value, consider it suspicious
        return (rating_value_count / total_recent) > settings.ANOMALY_THRESHOLD
    
    def process_ratings_batch(self, content_id):
        """Process all unprocessed ratings for a content"""
        try:
            content = Content.objects.get(id=content_id)
            unprocessed_ratings = Rating.objects.filter(
                content_id=content_id,
                processed=False
            )
            
            # Process each unprocessed rating
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
            
            content.average_rating = new_average
            content.rating_count = all_ratings.count()
            content.save()
            
            # Mark all processed
            unprocessed_ratings.update(processed=True)
            
        except Exception as e:
            logger.error(f"Error processing ratings for content {content_id}: {str(e)}")
    