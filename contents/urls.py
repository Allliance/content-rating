from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContentListView, ContentRatingView

# Create a router and register the viewset
router = DefaultRouter()
router.register(r'contents', ContentListView, basename='content')

# Define the urlpatterns
urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
    # Add the rating endpoint
    path('rate/', ContentRatingView.as_view(), name='content-rate'),
]