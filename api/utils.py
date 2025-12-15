import feedparser
import time
import hashlib
from urllib.parse import urlparse
from .models import Feed, Item

def calculate_checksum(text):
    """Calculate checksum for URL/text"""
    if not text:
        return 0
    # Use BigIntegerField compatible checksum (64-bit signed)
    # We take first 15 hex chars (60 bits) to be safe within 63 bits (signed 64-bit)
    return int(hashlib.md5(text.encode()).hexdigest()[:15], 16)

def refresh_feed(feed):
    """Fetch and parse RSS feed"""
    print(f"Refreshing feed: {feed.title or feed.url}")
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
    new_items_count = 0
    for entry in parsed.entries:
        # Generate unique ID
        item_link = entry.get('link', '')
        item_title = entry.get('title', '')
        item_uid = entry.get('id', item_link)

        # Check if item already exists
        # We use the uid to check for existence, which is more reliable
        if Item.objects.filter(feed=feed, uid=item_uid).exists():
            continue

        url_checksum = calculate_checksum(item_link)

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
        new_items_count += 1

    if new_items_count > 0:
        feed.last_updated_on_time = current_time
        feed.save()

    print(f"  Added {new_items_count} new items")
    return new_items_count
