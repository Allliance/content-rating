from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from .models import Content, Rating
from .constants import RATE_LIMIT_PER_HOUR
from django.db.utils import IntegrityError
User = get_user_model()

class ContentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.content = Content.objects.create(
            title='Test Content',
            text='Test Content Text'
        )

    def tearDown(self):
        cache.clear()

    def test_content_creation(self):
        self.assertEqual(self.content.title, 'Test Content')
        self.assertEqual(self.content.text, 'Test Content Text')
        self.assertTrue(isinstance(self.content.created_at, timezone.datetime))

    def test_rating_stats_no_ratings(self):
        stats = self.content.get_rating_stats()
        self.assertEqual(stats['average_rating'], 0.0)
        self.assertEqual(stats['rating_count'], 0)

    def test_rating_stats_with_ratings(self):
        Rating.objects.create(
            content=self.content,
            user=self.user,
            rating=4,
            weight=1.0
        )
        stats = self.content.get_rating_stats()
        self.assertEqual(stats['average_rating'], 4.0)
        self.assertEqual(stats['rating_count'], 1)

    def test_cache_invalidation(self):
        # Create initial rating
        Rating.objects.create(
            content=self.content,
            user=self.user,
            rating=4,
            weight=1.0
        )
        
        # Get stats (this will cache them)
        initial_stats = self.content.get_rating_stats()
        
        # Create new rating
        new_user = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        Rating.objects.create(
            content=self.content,
            user=new_user,
            rating=2,
            weight=1.0
        )
        
        # Get stats again (should be different due to cache invalidation)
        new_stats = self.content.get_rating_stats()
        self.assertNotEqual(initial_stats['average_rating'], new_stats['average_rating'])

class ContentAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.content = Content.objects.create(
            title='Test Content',
            text='Test Content Text'
        )
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        cache.clear()

    def test_list_contents(self):
        url = reverse('content-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Content')

    def test_rate_content_success(self):
        url = reverse('content-rate')
        data = {
            'content_id': self.content.id,
            'rating': 4
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(int(response.data['rating']), 4)
        self.assertTrue(0 < response.data['weight'] <= 1)

    def test_rate_content_missing_fields(self):
        url = reverse('content-rate')
        data = {'content_id': self.content.id}  # Missing rating
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rate_content_invalid_content(self):
        url = reverse('content-rate')
        data = {
            'content_id': 999,  # Non-existent content
            'rating': 4
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_rate_limit_weight(self):
        url = reverse('content-rate')
        rating_value = 4

        # Create multiple ratings within the time window
        for i in range(RATE_LIMIT_PER_HOUR//100):
            print(i)
            Rating.objects.create(
                content=self.content,
                user=User.objects.create_user(
                    username=f'testuser{i}',
                    password='testpass123'
                ),
                rating=rating_value,
                created_at=timezone.now()
            )

        data = {
            'content_id': self.content.id,
            'rating': rating_value
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['weight'] < 1.0)

class RatingModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.content = Content.objects.create(
            title='Test Content',
            text='Test Content Text'
        )

    def test_rating_creation(self):
        rating = Rating.objects.create(
            content=self.content,
            user=self.user,
            rating=4,
            weight=1.0
        )
        self.assertEqual(rating.rating, 4)
        self.assertEqual(rating.weight, 1.0)
        self.assertTrue(isinstance(rating.created_at, timezone.datetime))
        self.assertTrue(isinstance(rating.updated_at, timezone.datetime))

    def test_rating_validation(self):
        with self.assertRaises(Exception):
            Rating.objects.create(
                content=self.content,
                user=self.user,
                rating=6,  # Invalid rating value
                weight=1.0
            )
        
        with self.assertRaises(Exception):
            Rating.objects.create(
                content=self.content,
                user=self.user,
                rating=-1,  # Invalid rating value
                weight=1.0
            )
        
        with self.assertRaises(Exception):
            Rating.objects.create(
                content=self.content,
                user=self.user,
                rating=2,
                weight=1.2,   # Invalid weight value
            )
        
        with self.assertRaises(Exception):
            Rating.objects.create(
                content=self.content,
                user=self.user,
                rating=2,
                weight=-0.3,   # Invalid weight value
            )
        