from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
from random import randint, uniform, choice
from django.utils import timezone

from contents.models import Content, Rating

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with fake data'

    def handle(self, *args, **kwargs):
        
        users_min_count = 20
        contents_min_count = 100
        ratings_min_count = 1000
        
        fake = Faker()

        all_users_count = User.objects.all().count()
        
        for _ in range(users_min_count - all_users_count):
            username = fake.user_name()
            email = fake.email()
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={'email': email}
            )


        all_contents_count = Content.objects.all().count()
        for _ in range(contents_min_count - all_contents_count):
            content = Content.objects.create(
                title=fake.sentence(nb_words=6),
                text=fake.text(max_nb_chars=1000),
                created_at=fake.date_time_between(
                    start_date='-1y',
                    end_date='now',
                    tzinfo=timezone.get_current_timezone()
                )
            )
            self.stdout.write(f'Created content: {content.title}')

        users = list(User.objects.all())
        contents = list(Content.objects.all())


        all_ratings_count = Rating.objects.all().count()
        # Create 1000 ratings
        for _ in range(ratings_min_count - all_ratings_count):
            content = choice(contents)
            user = choice(users)
            
            # Try to create rating, skip if user already rated this content
            try:
                rating = randint(1, 5)
                weight = uniform(0.5, 2.0)
                Rating.objects.create(
                    content=content,
                    user=user,
                    rating=rating,
                    weight=weight,
                    created_at=fake.date_time_between(
                        start_date=content.created_at,
                        end_date='now',
                        tzinfo=timezone.get_current_timezone()
                    )
                )
                self.stdout.write(f'User with {user.username} username rated the content with title {content.title} {rating}/5')
            except Exception as e:
                self.stdout.write(f'An error occured while saving a rating: {str(e)}')
                continue

        self.stdout.write(self.style.SUCCESS('Successfully populated database'))