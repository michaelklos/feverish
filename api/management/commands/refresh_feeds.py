from django.core.management.base import BaseCommand
from api.models import Feed, FeverUser
from api.utils import refresh_feed


class Command(BaseCommand):
    help = 'Refresh RSS feeds'

    def add_arguments(self, parser):
        parser.add_argument('--feed-id', type=int, help='Refresh specific feed ID')
        parser.add_argument('--user', type=str, help='User email to refresh feeds for')

    def handle(self, *args, **options):
        feed_id = options.get('feed_id')
        user_email = options.get('user')

        if user_email:
            try:
                user = FeverUser.objects.get(email=user_email)
                feeds = Feed.objects.filter(user=user)
            except FeverUser.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User {user_email} not found'))
                return
        elif feed_id:
            feeds = Feed.objects.filter(id=feed_id)
        else:
            feeds = Feed.objects.all()

        for feed in feeds:
            self.stdout.write(f'Refreshing feed: {feed.title or feed.url}')
            try:
                new_items = refresh_feed(feed)
                self.stdout.write(self.style.SUCCESS(f'Successfully refreshed {feed.title}. Added {new_items} new items.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error refreshing {feed.title}: {str(e)}'))
