from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import OuterRef, Subquery
from .models import Content, Rating
from .serializers import ContentSerializer

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