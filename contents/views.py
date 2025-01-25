from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import OuterRef, Subquery
from .models import Content, Rating
from .serializers import ContentSerializer
from django.utils import timezone
from datetime import timedelta
from .constants import RATE_LIMIT_PER_HOUR

class ContentListView(viewsets.ReadOnlyModelViewSet):
    serializer_class = ContentSerializer
    pagination_class = PageNumberPagination
    queryset = Content.objects.all()
    
    def get_queryset(self):
        user_rating = Rating.objects.filter(
            content=OuterRef('pk'),
            user=self.request.user.id
        ).values('rating')[:1]
        
        queryset = Content.objects.annotate(
            user_rating=Subquery(user_rating)
        ).select_related()
        
        return queryset
    
class ContentRatingView(APIView):

    def calculate_rating_weight(self, content_id, rating_value, time_window_minutes=60):
        time_threshold = timezone.now() - timedelta(minutes=time_window_minutes)
        
        recent_similar_ratings = Rating.objects.filter(
            content_id=content_id,
            created_at__gte=time_threshold,
            rating=rating_value,
        )
        
        recent_similar_ratings_count = recent_similar_ratings.count()
        
        print(recent_similar_ratings_count)
        
        return max(1, RATE_LIMIT_PER_HOUR - recent_similar_ratings_count) / RATE_LIMIT_PER_HOUR
        

    def post(self, request):
        
        content_id = request.data.get('content_id')
        rating_value = request.data.get('rating')
        user = request.user
        
        if not all([content_id, rating_value, user]):
            print([content_id, rating_value, user])
            return Response(
                {'error': 'Missing required fields'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            content = Content.objects.get(id=content_id)
        except Content.DoesNotExist:
            return Response(
                {'error': 'Content not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        weight = self.calculate_rating_weight(content_id, rating_value)
        print(weight)
        # Update or create rating with weight
        Rating.objects.update_or_create(
            content=content,
            user=user,
            defaults={
                'rating': rating_value,
                'weight': weight
            }
        )
        
        return Response({
            'status': 'success',
            'rating': rating_value,
            'weight': weight,
        })