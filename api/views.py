from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import FeverUser, Feed, Group, Item, Favicon, FeedGroup, Link
from .utils import refresh_feed
import hashlib
import time
import logging

logger = logging.getLogger(__name__)


def authenticate_api_key(api_key):
    """
    Authenticate user by API key.
    The Fever API key is md5(email:password) where password is the plain text password.
    We store this in fever_api_key field for quick lookup.
    """
    if not api_key:
        return None

    try:
        user = FeverUser.objects.get(fever_api_key=api_key.lower())
        return user
    except FeverUser.DoesNotExist:
        return None


@csrf_exempt
@require_http_methods(["GET", "POST"])
def fever_api(request):
    """
    Fever API endpoint compatible with version 3
    """
    # Authentication
    params = request.GET.copy()
    params.update(request.POST)
    api_key = params.get('api_key', '')
    user = authenticate_api_key(api_key)

    if not user:
        return JsonResponse({'api_version': 3, 'auth': 0})

    handler = FeverAPIHandler(request, user)
    response_data = handler.process()

    return JsonResponse(response_data)


class FeverAPIHandler:
    def __init__(self, request, user):
        self.request = request
        self.user = user
        self.params = request.GET.copy()
        self.params.update(request.POST)
        self.response_data = {
            'api_version': 3,
            'auth': 1
        }

    def process(self):
        """Process the request and return response data"""
        # Update last session time
        self.user.last_session_on_time = int(time.time())
        self.user.save(update_fields=['last_session_on_time'])

        # Handle actions
        if 'refresh' in self.params:
            self.handle_refresh()

        if 'mark' in self.params:
            self.handle_mark()

        # Add last refreshed time
        last_refreshed = Feed.objects.filter(user=self.user).order_by('-last_refreshed_on_time').first()
        if last_refreshed:
            self.response_data['last_refreshed_on_time'] = last_refreshed.last_refreshed_on_time

        # Data retrieval
        if 'groups' in self.params:
            self.get_groups()

        if 'feeds' in self.params or 'groups' in self.params:
            self.get_feeds()

        if 'favicons' in self.params:
            self.get_favicons()

        if 'items' in self.params:
            self.get_items()

        if 'unread_item_ids' in self.params:
            self.get_unread_item_ids()

        if 'saved_item_ids' in self.params:
            self.get_saved_item_ids()

        if 'links' in self.params:
            self.get_links()

        return self.response_data

    def handle_refresh(self):
        logger.info(f"Refresh requested via API for user {self.user.email}")
        feeds = Feed.objects.filter(user=self.user)
        for feed in feeds:
            try:
                refresh_feed(feed)
            except Exception as e:
                logger.error(f"Error refreshing feed {feed.id}: {e}")
                pass

    def handle_mark(self):
        if 'as' not in self.params or 'id' not in self.params:
            return

        mark_type = self.params['mark']
        as_type = self.params['as']
        item_ids = self.params['id']
        before = self.params.get('before')

        if mark_type == 'item':
            ids = [int(i) for i in item_ids.split(',')]
            if as_type == 'read':
                Item.objects.mark_as_read(self.user, ids)
            elif as_type == 'unread':
                Item.objects.mark_as_unread(self.user, ids)
            elif as_type == 'saved':
                Item.objects.mark_as_saved(self.user, ids)
            elif as_type == 'unsaved':
                Item.objects.mark_as_unsaved(self.user, ids)

        elif mark_type == 'feed':
            feed_id = int(item_ids)
            if as_type == 'read':
                Item.objects.mark_feed_as_read(self.user, feed_id, before)
            elif as_type == 'unread':
                items = Item.objects.filter(feed_id=feed_id, feed__user=self.user)
                if before:
                    items = items.filter(created_on_time__lte=int(before))
                items.update(read_on_time=0)

        elif mark_type == 'group':
            group_id = int(item_ids)
            if as_type == 'read':
                Item.objects.mark_group_as_read(self.user, group_id, before)
            elif as_type == 'unread':
                feed_ids = FeedGroup.objects.filter(group_id=group_id, group__user=self.user).values_list('feed_id', flat=True)
                items = Item.objects.filter(feed_id__in=feed_ids)
                if before:
                    items = items.filter(created_on_time__lte=int(before))
                items.update(read_on_time=0)

    def get_groups(self):
        groups = Group.objects.filter(user=self.user).values('id', 'title')
        self.response_data['groups'] = [
            {'id': g['id'], 'title': g['title']}
            for g in groups
        ]

    def get_feeds(self):
        feeds = Feed.objects.filter(user=self.user).select_related('favicon')
        feeds_data = []

        for feed in feeds:
            feeds_data.append({
                'id': feed.id,
                'favicon_id': feed.favicon_id if feed.favicon_id else 0,
                'title': feed.user_title or feed.title or feed.url,
                'url': feed.url,
                'site_url': feed.site_url or '',
                'is_spark': 1 if feed.is_spark else 0,
                'last_updated_on_time': feed.last_updated_on_time
            })

        if 'feeds' in self.params:
            self.response_data['feeds'] = feeds_data

        # Feed-group relationships
        feed_groups = FeedGroup.objects.filter(feed__user=self.user, feed__is_spark=False).values('group_id', 'feed_id')

        # Group feeds by group_id
        groups_dict = {}
        for fg in feed_groups:
            group_id = fg['group_id']
            if group_id not in groups_dict:
                groups_dict[group_id] = []
            groups_dict[group_id].append(str(fg['feed_id']))

        self.response_data['feeds_groups'] = [
            {'group_id': gid, 'feed_ids': ','.join(fids)}
            for gid, fids in groups_dict.items()
        ]

    def get_favicons(self):
        favicons = Favicon.objects.all().values('id', 'cache')
        self.response_data['favicons'] = [
            {'id': f['id'], 'data': f['cache']}
            for f in favicons
        ]

    def get_items(self):
        items_qs = Item.objects.filter(feed__user=self.user)

        self.response_data['total_items'] = items_qs.count()

        # Filter by feed_ids or group_ids
        if 'feed_ids' in self.params:
            feed_ids = [int(i) for i in self.params['feed_ids'].split(',')]
            items_qs = items_qs.filter(feed_id__in=feed_ids)

        if 'group_ids' in self.params:
            group_ids = [int(i) for i in self.params['group_ids'].split(',')]
            feed_ids = FeedGroup.objects.filter(group_id__in=group_ids).values_list('feed_id', flat=True)
            items_qs = items_qs.filter(feed_id__in=feed_ids)

        # Pagination
        if 'max_id' in self.params:
            max_id = int(self.params['max_id'])
            if max_id > 0:
                items_qs = items_qs.filter(id__lt=max_id)
            items_qs = items_qs.order_by('-id')[:50]
        elif 'with_ids' in self.params:
            item_ids = [int(i) for i in self.params['with_ids'].split(',')]
            items_qs = items_qs.filter(id__in=item_ids)
        elif 'since_id' in self.params:
            since_id = int(self.params['since_id'])
            items_qs = items_qs.filter(id__gt=since_id).order_by('id')[:50]
        else:
            items_qs = items_qs.order_by('-id')[:50]

        items_data = []
        for item in items_qs:
            items_data.append({
                'id': item.id,
                'feed_id': item.feed_id,
                'title': item.title or '',
                'author': item.author or '',
                'html': item.description or '',
                'url': item.link or '',
                'is_saved': 1 if item.is_saved else 0,
                'is_read': 1 if item.read_on_time > 0 else 0,
                'created_on_time': item.created_on_time
            })

        self.response_data['items'] = items_data

    def get_unread_item_ids(self):
        unread_ids = Item.objects.filter(
            feed__user=self.user,
            read_on_time=0
        ).values_list('id', flat=True)
        self.response_data['unread_item_ids'] = ','.join(map(str, unread_ids))

    def get_saved_item_ids(self):
        saved_ids = Item.objects.filter(
            feed__user=self.user,
            is_saved=True
        ).values_list('id', flat=True)
        self.response_data['saved_item_ids'] = ','.join(map(str, saved_ids))

    def get_links(self):
        links = Link.objects.filter(feed__user=self.user).order_by('-weight')[:50]
        self.response_data['links'] = [
            {
                'id': link.id,
                'feed_id': link.feed_id,
                'item_id': link.item_id,
                'url': link.url or '',
                'title': link.title or '',
                'weight': link.weight,
                'created_on_time': link.created_on_time
            }
            for link in links
        ]
