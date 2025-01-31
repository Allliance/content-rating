from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContentListView, ContentRatingView, ContentCreateView, ContentDetailView

router = DefaultRouter()
router.register(r'contents', ContentListView, basename='content')

urlpatterns = [
    path('contents/', ContentListView.as_view({'get': 'list'}), name='content-list'),
    path('contents/<int:content_id>/', ContentDetailView.as_view(), name='content-detail'),
    path('contents/create/', ContentCreateView.as_view(), name='content-create'),
    path('contents/rate/', ContentRatingView.as_view(), name='content-rate'),
]