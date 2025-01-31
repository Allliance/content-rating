from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Content, Rating
from .serializers import ContentSerializer
from django.conf import settings
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from .paginations import ContentsPagination
from kafka import KafkaProducer
import json

class ContentListView(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    
    serializer_class = ContentSerializer
    pagination_class = ContentsPagination
    
    def get_queryset(self):
        sort_by = self.request.query_params.get('sort_by', 'created_at')
        sort_order = self.request.query_params.get('order', 'desc')
        
        queryset = Content.objects.all()
        
        # Use the stored statistics for sorting
        if sort_by == 'rating_count':
            order_field = '-rating_count' if sort_order == 'desc' else 'rating_count'
            queryset = queryset.order_by(order_field)
        elif sort_by == 'rating_average':
            order_field = '-average_rating' if sort_order == 'desc' else 'average_rating'
            queryset = queryset.order_by(order_field)
        else:
            order_field = '-created_at' if sort_order == 'desc' else 'created_at'
            queryset = queryset.order_by(order_field)
        
        return queryset

class ContentDetailView(APIView):
    permission_classes = (AllowAny,)
    
    
    def get(self, request, content_id):
        try:
            content = Content.objects.get(id=content_id)
            serializer = ContentSerializer(content)
            return Response(serializer.data)
        except Content.DoesNotExist:
            return Response(
                {'error': 'Content not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class ContentCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        title = request.data.get('title')
        text = request.data.get('text')
        
        if not all([title, text]):
            return Response(
                {'error': 'Both title and text are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        content = Content.objects.create(
            title=title,
            text=text
        )
        
        serializer = ContentSerializer(content)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

class ContentRatingView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda m: json.dumps(m).encode('utf-8')
        )

    def post(self, request):
        content_id = request.data.get('content_id')
        rating_value = request.data.get('rating')
        user = request.user
        
        if not all([content_id, rating_value, user]):
            return Response(
                {'error': 'Missing required fields'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            rating_value = int(rating_value)
            if not (0 <= rating_value <= 5):
                return Response(
                    {'error': 'Rating must be between 0 and 5'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (TypeError, ValueError):
            return Response(
                {'error': 'Rating must be an integer'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            content = Content.objects.get(id=content_id)
        except Content.DoesNotExist:
            return Response(
                {'error': 'Content not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Try to get existing rating
            rating = Rating.objects.get(content=content, user=user)
            rating.rating = rating_value
            rating.processed = False
            rating.save()
            action = 'updated'
        except Rating.DoesNotExist:
            # Create new rating
            rating = Rating.objects.create(
                content=content,
                user=user,
                rating=rating_value,
                processed=False
            )
            action = 'created'
        
        # Send to Kafka for processing
        self.producer.send('ratings', {
            'content_id': content_id,
            'rating_id': rating.id,
            'user_id': user.id,
            'rating': rating_value
        })
        
        return Response({
            'status': 'success',
            'message': f'Rating {action}',
            'rating': rating_value
        })