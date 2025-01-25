from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import OuterRef, Subquery, Count, Avg, StdDev
from .models import Content, Rating
from .serializers import ContentSerializer, RatingSerializer
from django.utils import timezone
from datetime import timedelta

class ContentListView(viewsets.ReadOnlyModelViewSet):
    serializer_class = ContentSerializer
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        user_rating = Rating.objects.filter(
            content=OuterRef('pk'),
            user_id=self.request.user.id
        ).values('rating')[:1]
        
        queryset = Content.objects.annotate(
            user_rating=Subquery(user_rating)
        ).select_related()
        
        return queryset
    
class RatingSubmissionView(APIView):
    
    def detect_rating_bombing(self, content_id, rating_value, time_window_minutes=60):
        time_threshold = timezone.now() - timedelta(minutes=time_window_minutes)
        
        return False

    def calculate_rating_weight(self, content_id, user_id, rating_value):
        """
        Calculate weight for a rating based on various factors
        """
        base_weight = 1.0
        
        if self.detect_rating_bombing(content_id, rating_value):
            base_weight *= 0.1
            
        return base_weight

    def post(self, request):
        content_id = request.data.get('content_id')
        rating_value = request.data.get('rating')
        user_id = request.user.id
        
        if not all([content_id, rating_value, user_id]):
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
        
        weight = self.calculate_rating_weight(content_id, user_id, rating_value)
        
        # Update or create rating with weight
        Rating.objects.update_or_create(
            content=content,
            user_id=user_id,
            defaults={
                'rating': rating_value,
                'weight': weight
            }
        )
        
        return Response({
            'status': 'success',
            'rating': rating_value,
            'weight': weight
        })