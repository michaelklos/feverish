from django.test import TestCase, Client
from django.urls import reverse
from api.models import FeverUser, Feed, Group, Item, FeedGroup
import hashlib
import time
import json


class FeverAPITestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = Client()

        # Create test user
        self.email = 'test@example.com'
        self.password = 'testpassword'
        self.user = FeverUser.objects.create_user(
            email=self.email,
            password=self.password
        )
        self.user.installed_on_time = int(time.time())
        self.user.save()

        # Calculate API key
        self.api_key = hashlib.md5(f"{self.email}:{self.password}".encode()).hexdigest()

        # Create test group
        self.group = Group.objects.create(
            user=self.user,
            title='Test Group'
        )

        # Create test feed
        feed_url = 'https://example.com/feed.rss'
        self.feed = Feed.objects.create(
            user=self.user,
            title='Test Feed',
            url=feed_url,
            url_checksum=int(hashlib.md5(feed_url.encode()).hexdigest()[:8], 16),
            site_url='https://example.com',
            domain='example.com'
        )
        self.feed.groups.add(self.group)

        # Create test items
        for i in range(5):
            item_link = f'https://example.com/item-{i}'
            Item.objects.create(
                feed=self.feed,
                uid=f'item-{i}',
                title=f'Test Item {i}',
                author='Test Author',
                description=f'<p>Test description {i}</p>',
                link=item_link,
                url_checksum=int(hashlib.md5(item_link.encode()).hexdigest()[:8], 16),
                created_on_time=int(time.time()) - (i * 3600),
                added_on_time=int(time.time()) - (i * 3600),
                is_saved=(i % 2 == 0)
            )

    def test_api_version(self):
        """Test that API returns version 3"""
        response = self.client.post('/api/')
        data = json.loads(response.content)

        self.assertEqual(data['api_version'], 3)
        self.assertEqual(data['auth'], 0)

    def test_authentication_failure(self):
        """Test authentication with invalid API key"""
        response = self.client.post('/api/', {'api_key': 'invalid_key'})
        data = json.loads(response.content)

        self.assertEqual(data['auth'], 0)
        self.assertNotIn('groups', data)

    def test_authentication_success(self):
        """Test authentication with valid API key"""
        response = self.client.post('/api/', {'api_key': self.api_key})
        data = json.loads(response.content)

        self.assertEqual(data['auth'], 1)

    def test_groups_endpoint(self):
        """Test groups endpoint"""
        response = self.client.get('/api/', {'api_key': self.api_key, 'groups': ''})
        data = json.loads(response.content)

        self.assertEqual(data['auth'], 1)
        self.assertIn('groups', data)
        self.assertEqual(len(data['groups']), 1)
        self.assertEqual(data['groups'][0]['title'], 'Test Group')

    def test_feeds_endpoint(self):
        """Test feeds endpoint"""
        response = self.client.get('/api/', {'api_key': self.api_key, 'feeds': ''})
        data = json.loads(response.content)

        self.assertEqual(data['auth'], 1)
        self.assertIn('feeds', data)

    def test_feed_title_override(self):
        """Test that user_title overrides canonical title in API response"""
        # Set user_title
        self.feed.user_title = "My Custom Title"
        self.feed.save()

        response = self.client.get('/api/', {'api_key': self.api_key, 'feeds': ''})
        data = json.loads(response.content)

        self.assertEqual(data['auth'], 1)
        self.assertIn('feeds', data)
        # Find the feed
        feed_data = next(f for f in data['feeds'] if f['id'] == self.feed.id)
        self.assertEqual(feed_data['title'], "My Custom Title")

        # Unset user_title
        self.feed.user_title = None
        self.feed.save()

        response = self.client.get('/api/', {'api_key': self.api_key, 'feeds': ''})
        data = json.loads(response.content)
        feed_data = next(f for f in data['feeds'] if f['id'] == self.feed.id)
        self.assertEqual(feed_data['title'], "Test Feed")
        self.assertEqual(len(data['feeds']), 1)
        self.assertEqual(data['feeds'][0]['title'], 'Test Feed')
        self.assertIn('feeds_groups', data)

    def test_items_endpoint(self):
        """Test items endpoint"""
        response = self.client.get('/api/', {'api_key': self.api_key, 'items': ''})
        data = json.loads(response.content)

        self.assertEqual(data['auth'], 1)
        self.assertIn('items', data)
        self.assertEqual(data['total_items'], 5)
        self.assertGreater(len(data['items']), 0)

    def test_unread_item_ids(self):
        """Test unread_item_ids endpoint"""
        response = self.client.get('/api/', {'api_key': self.api_key, 'unread_item_ids': ''})
        data = json.loads(response.content)

        self.assertEqual(data['auth'], 1)
        self.assertIn('unread_item_ids', data)
        # All items are unread by default
        item_ids = data['unread_item_ids'].split(',') if data['unread_item_ids'] else []
        self.assertEqual(len(item_ids), 5)

    def test_saved_item_ids(self):
        """Test saved_item_ids endpoint"""
        response = self.client.get('/api/', {'api_key': self.api_key, 'saved_item_ids': ''})
        data = json.loads(response.content)

        self.assertEqual(data['auth'], 1)
        self.assertIn('saved_item_ids', data)
        # Items with even indices are saved (0, 2, 4) = 3 items
        if data['saved_item_ids']:
            item_ids = data['saved_item_ids'].split(',')
            self.assertEqual(len(item_ids), 3)

    def test_mark_item_as_read(self):
        """Test marking an item as read"""
        item = Item.objects.first()

        response = self.client.post('/api/', {
            'api_key': self.api_key,
            'mark': 'item',
            'as': 'read',
            'id': str(item.id)
        })
        data = json.loads(response.content)

        self.assertEqual(data['auth'], 1)

        # Verify item is marked as read
        item.refresh_from_db()
        self.assertGreater(item.read_on_time, 0)

    def test_mark_item_as_saved(self):
        """Test marking an item as saved"""
        item = Item.objects.filter(is_saved=False).first()

        response = self.client.post('/api/', {
            'api_key': self.api_key,
            'mark': 'item',
            'as': 'saved',
            'id': str(item.id)
        })
        data = json.loads(response.content)

        self.assertEqual(data['auth'], 1)

        # Verify item is marked as saved
        item.refresh_from_db()
        self.assertTrue(item.is_saved)


class ItemManagerTestCase(TestCase):
    def setUp(self):
        self.user = FeverUser.objects.create_user(email='test@example.com', password='password')
        self.feed = Feed.objects.create(user=self.user, title='Test Feed', url='http://example.com')
        self.item1 = Item.objects.create(
            feed=self.feed,
            title='Item 1',
            url_checksum=1,
            created_on_time=1000,
            added_on_time=1000
        )
        self.item2 = Item.objects.create(
            feed=self.feed,
            title='Item 2',
            url_checksum=2,
            created_on_time=2000,
            added_on_time=2000
        )

    def test_mark_as_read(self):
        Item.objects.mark_as_read(self.user, [self.item1.id])
        self.item1.refresh_from_db()
        self.item2.refresh_from_db()
        self.assertGreater(self.item1.read_on_time, 0)
        self.assertEqual(self.item2.read_on_time, 0)

    def test_mark_as_unread(self):
        self.item1.read_on_time = 12345
        self.item1.save()
        Item.objects.mark_as_unread(self.user, [self.item1.id])
        self.item1.refresh_from_db()
        self.assertEqual(self.item1.read_on_time, 0)

    def test_mark_as_saved(self):
        Item.objects.mark_as_saved(self.user, [self.item1.id])
        self.item1.refresh_from_db()
        self.assertTrue(self.item1.is_saved)

    def test_mark_as_unsaved(self):
        self.item1.is_saved = True
        self.item1.save()
        Item.objects.mark_as_unsaved(self.user, [self.item1.id])
        self.item1.refresh_from_db()
        self.assertFalse(self.item1.is_saved)


class UtilsTestCase(TestCase):
    def setUp(self):
        self.user = FeverUser.objects.create_user(email='utils@example.com', password='password')
        self.feed = Feed.objects.create(user=self.user, title='Utils Feed', url='http://example.com/rss')

    def test_refresh_feed_timestamp_calculation(self):
        """Test that published_parsed (UTC struct_time) is correctly converted to timestamp"""
        import time
        import calendar
        from unittest.mock import patch, MagicMock
        from api.utils import refresh_feed

        # Create a mock entry with a known UTC time
        # 2023-01-01 12:00:00 UTC
        utc_struct = time.struct_time((2023, 1, 1, 12, 0, 0, 6, 1, 0))
        expected_timestamp = calendar.timegm(utc_struct)

        mock_entry = MagicMock()
        mock_entry.get.side_effect = lambda k, default=None: {
            'link': 'http://example.com/item1',
            'title': 'Test Item',
            'id': 'item1',
            'published_parsed': utc_struct,
            'updated_parsed': None,
            'summary': 'summary',
            'description': 'description'
        }.get(k, default)
        # Mock content attribute access
        del mock_entry.content

        mock_parsed = MagicMock()
        mock_parsed.feed.title = 'Updated Title'
        mock_parsed.feed.link = 'http://example.com'
        mock_parsed.entries = [mock_entry]

        with patch('api.utils.feedparser.parse', return_value=mock_parsed):
            refresh_feed(self.feed)

        item = Item.objects.get(uid='item1')
        self.assertEqual(item.created_on_time, expected_timestamp)
