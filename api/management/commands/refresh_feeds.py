from django.core.management.base import BaseCommand
from api.models import Feed, Item, FeverUser
import feedparser
import time
import hashlib
from urllib.parse import urlparse


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
                self.refresh_feed(feed)
                self.stdout.write(self.style.SUCCESS(f'Successfully refreshed {feed.title}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error refreshing {feed.title}: {str(e)}'))
    
    def refresh_feed(self, feed):
        """Fetch and parse RSS feed"""
        parsed = feedparser.parse(feed.url)
        
        current_time = int(time.time())
        feed.last_refreshed_on_time = current_time
        
        # Update feed metadata
        if hasattr(parsed, 'feed'):
            if hasattr(parsed.feed, 'title') and parsed.feed.title:
                feed.title = parsed.feed.title
            if hasattr(parsed.feed, 'link') and parsed.feed.link:
                feed.site_url = parsed.feed.link
                feed.domain = urlparse(parsed.feed.link).netloc
        
        feed.save()
        
        # Process entries
        new_items = 0
        for entry in parsed.entries:
            # Generate unique ID
            item_link = entry.get('link', '')
            item_title = entry.get('title', '')
            item_uid = entry.get('id', item_link)
            
            # Check if item already exists
            url_checksum = self.calculate_checksum(item_link)
            
            if Item.objects.filter(feed=feed, uid=item_uid).exists():
                continue
            
            # Create new item
            description = entry.get('summary', '') or entry.get('description', '')
            if hasattr(entry, 'content') and entry.content:
                description = entry.content[0].value
            
            published_time = entry.get('published_parsed') or entry.get('updated_parsed')
            if published_time:
                created_on_time = int(time.mktime(published_time))
            else:
                created_on_time = current_time
            
            Item.objects.create(
                feed=feed,
                uid=item_uid,
                title=item_title,
                author=entry.get('author', ''),
                description=description,
                link=item_link,
                url_checksum=url_checksum,
                created_on_time=created_on_time,
                added_on_time=current_time
            )
            new_items += 1
        
        if new_items > 0:
            feed.last_updated_on_time = current_time
            feed.save()
        
        self.stdout.write(f'  Added {new_items} new items')
    
    def calculate_checksum(self, text):
        """Calculate checksum for URL/text"""
        if not text:
            return 0
        return int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
