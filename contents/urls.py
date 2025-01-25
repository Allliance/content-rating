from django.urls import path
from .views import ContentListView, ContentRatingView

urlpatterns = [
    path('contents/', ContentListView.as_view(), name='content-list'),
    path('contents/<int:content_id>/rate/', ContentRatingView.as_view(), name='content-rate'),
]