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
