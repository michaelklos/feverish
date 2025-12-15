#!/usr/bin/env python
"""
Quick setup script for Fever Django
Creates a demo user with sample feeds for testing
"""
import os
import sys
import django
import hashlib

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'feverish.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from api.models import FeverUser, Feed, Group, Item, FeedGroup
import time


def setup_demo_data():
    """Create demo user and sample feeds"""

    print("=" * 60)
    print("Feverish - Quick Setup")
    print("=" * 60)

    # Create demo user
    email = "demo@example.com"
    password = "demopassword"

    print(f"\n1. Creating demo user...")
    print(f"   Email: {email}")
    print(f"   Password: {password}")

    # Check if user exists
    if FeverUser.objects.filter(email=email).exists():
        print(f"   ✓ User already exists")
        user = FeverUser.objects.get(email=email)
        # Ensure user is superuser
        if not user.is_superuser or not user.is_staff:
            user.is_superuser = True
            user.is_staff = True
            user.save()
            print(f"   ✓ Updated user to superuser")
    else:
        user = FeverUser.objects.create_superuser(email=email, password=password)
        user.installed_on_time = int(time.time())
        user.save()
        print(f"   ✓ User created successfully")

    # Calculate and display API key
    api_key = user.fever_api_key
    print(f"   API Key: {api_key}")

    # Create groups
    print(f"\n2. Creating sample groups...")
    groups_data = [
        "Tech News",
        "Blogs",
        "Development"
    ]

    groups = {}
    for group_name in groups_data:
        if Group.objects.filter(user=user, title=group_name).exists():
            print(f"   ✓ Group '{group_name}' already exists")
            groups[group_name] = Group.objects.get(user=user, title=group_name)
        else:
            group = Group.objects.create(user=user, title=group_name)
            groups[group_name] = group
            print(f"   ✓ Created group '{group_name}'")

    # Create sample feeds
    print(f"\n3. Creating sample feeds...")
    feeds_data = [
        {
            "title": "Hacker News",
            "url": "https://news.ycombinator.com/rss",
            "site_url": "https://news.ycombinator.com",
            "group": "Tech News"
        },
        {
            "title": "Python Insider",
            "url": "https://blog.python.org/feeds/posts/default",
            "site_url": "https://blog.python.org",
            "group": "Development"
        },
        {
            "title": "Django Weblog",
            "url": "https://www.djangoproject.com/rss/weblog/",
            "site_url": "https://www.djangoproject.com",
            "group": "Development"
        },
    ]

    for feed_data in feeds_data:
        url = feed_data["url"]
        url_checksum = int(hashlib.md5(url.encode()).hexdigest()[:8], 16)

        if Feed.objects.filter(user=user, url=url).exists():
            print(f"   ✓ Feed '{feed_data['title']}' already exists")
            feed = Feed.objects.get(user=user, url=url)
        else:
            feed = Feed.objects.create(
                user=user,
                title=feed_data["title"],
                url=url,
                url_checksum=url_checksum,
                site_url=feed_data["site_url"],
                domain=feed_data["site_url"].replace("https://", "").replace("http://", "").split("/")[0]
            )

            # Add to group
            if feed_data["group"] in groups:
                feed.groups.add(groups[feed_data["group"]])

            print(f"   ✓ Created feed '{feed_data['title']}'")

    print(f"\n4. Setup complete!")
    print(f"\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print(f"\n1. Refresh feeds to fetch articles:")
    print(f"   uv run python manage.py refresh_feeds --user {email}")
    print(f"\n2. Start the development server:")
    print(f"   uv run python manage.py runserver")
    print(f"\n3. Access the web interface:")
    print(f"   http://localhost:8000/")
    print(f"   Login with: {email} / {password}")
    print(f"\n4. Access the admin panel:")
    print(f"   http://localhost:8000/admin/")
    print(f"   (Create superuser first: uv run python manage.py createsuperuser)")
    print(f"\n5. Configure RSS reader app (like Reeder):")
    print(f"   Server: http://localhost:8000")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    print(f"   API Key: {api_key}")
    print(f"\n" + "=" * 60)


if __name__ == '__main__':
    try:
        setup_demo_data()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
