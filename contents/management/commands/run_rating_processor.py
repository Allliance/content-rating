from django.core.management.base import BaseCommand
from contents.services.rating_processor import RatingProcessor

class Command(BaseCommand):
    help = 'Runs the rating processor service'

    def handle(self, *args, **options):
        self.stdout.write('Starting rating processor service...')
        processor = RatingProcessor()
        processor.run()