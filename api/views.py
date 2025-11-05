from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import FeverUser, Feed, Group, Item, Favicon, FeedGroup, Link
import hashlib
import time


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
    Supports both GET and POST parameters as per Fever spec
    """
    # Merge GET and POST parameters
    params = request.GET.copy()
    params.update(request.POST)
    
    # Base response
    response_data = {
        'api_version': 3,
        'auth': 0
    }
    
    # Authentication
    api_key = params.get('api_key', '')
    user = authenticate_api_key(api_key)
    
    if user:
        response_data['auth'] = 1
        user.last_session_on_time = int(time.time())
        user.save(update_fields=['last_session_on_time'])
    else:
        # Return auth failure immediately
        return JsonResponse(response_data)
    
    # Get last refreshed time
    last_refreshed = Feed.objects.filter(user=user).order_by('-last_refreshed_on_time').first()
    if last_refreshed:
        response_data['last_refreshed_on_time'] = last_refreshed.last_refreshed_on_time
    
    # Handle mark operations (read/unread, saved/unsaved)
    if 'mark' in params and 'as' in params and 'id' in params:
        mark_type = params['mark']
        as_type = params['as']
        item_ids = params['id']
        before = params.get('before')
        
        if mark_type == 'item':
            ids = [int(i) for i in item_ids.split(',')]
            items = Item.objects.filter(id__in=ids, feed__user=user)
            
            if as_type == 'read':
                items.update(read_on_time=int(time.time()))
            elif as_type == 'unread':
                items.update(read_on_time=0)
            elif as_type == 'saved':
                items.update(is_saved=True)
            elif as_type == 'unsaved':
                items.update(is_saved=False)
                
        elif mark_type == 'feed':
            feed_id = int(item_ids)
            items = Item.objects.filter(feed_id=feed_id, feed__user=user)
            if before:
                items = items.filter(created_on_time__lte=int(before))
            
            if as_type == 'read':
                items.update(read_on_time=int(time.time()))
            elif as_type == 'unread':
                items.update(read_on_time=0)
                
        elif mark_type == 'group':
            group_id = int(item_ids)
            feed_ids = FeedGroup.objects.filter(group_id=group_id, group__user=user).values_list('feed_id', flat=True)
            items = Item.objects.filter(feed_id__in=feed_ids)
            if before:
                items = items.filter(created_on_time__lte=int(before))
            
            if as_type == 'read':
                items.update(read_on_time=int(time.time()))
            elif as_type == 'unread':
                items.update(read_on_time=0)
    
    # Groups
    if 'groups' in params:
        groups = Group.objects.filter(user=user).values('id', 'title')
        response_data['groups'] = [
            {'id': g['id'], 'title': g['title']}
            for g in groups
        ]
    
    # Feeds
    if 'feeds' in params or 'groups' in params:
        feeds = Feed.objects.filter(user=user).select_related('favicon')
        feeds_data = []
        
        for feed in feeds:
            feeds_data.append({
                'id': feed.id,
                'favicon_id': feed.favicon_id if feed.favicon_id else 0,
                'title': feed.title or feed.url,
                'url': feed.url,
                'site_url': feed.site_url or '',
                'is_spark': 1 if feed.is_spark else 0,
                'last_updated_on_time': feed.last_updated_on_time
            })
        
        if 'feeds' in params:
            response_data['feeds'] = feeds_data
        
        # Feed-group relationships
        feed_groups = FeedGroup.objects.filter(feed__user=user, feed__is_spark=False).values('group_id', 'feed_id')
        
        # Group feeds by group_id
        groups_dict = {}
        for fg in feed_groups:
            group_id = fg['group_id']
            if group_id not in groups_dict:
                groups_dict[group_id] = []
            groups_dict[group_id].append(str(fg['feed_id']))
        
        response_data['feeds_groups'] = [
            {'group_id': gid, 'feed_ids': ','.join(fids)}
            for gid, fids in groups_dict.items()
        ]
    
    # Favicons
    if 'favicons' in params:
        favicons = Favicon.objects.all().values('id', 'cache')
        response_data['favicons'] = [
            {'id': f['id'], 'data': f['cache']}
            for f in favicons
        ]
    
    # Items
    if 'items' in params:
        items_qs = Item.objects.filter(feed__user=user)
        
        response_data['total_items'] = items_qs.count()
        
        # Filter by feed_ids or group_ids
        if 'feed_ids' in params:
            feed_ids = [int(i) for i in params['feed_ids'].split(',')]
            items_qs = items_qs.filter(feed_id__in=feed_ids)
        
        if 'group_ids' in params:
            group_ids = [int(i) for i in params['group_ids'].split(',')]
            feed_ids = FeedGroup.objects.filter(group_id__in=group_ids).values_list('feed_id', flat=True)
            items_qs = items_qs.filter(feed_id__in=feed_ids)
        
        # Pagination
        if 'max_id' in params:
            max_id = int(params['max_id'])
            if max_id > 0:
                items_qs = items_qs.filter(id__lt=max_id)
            items_qs = items_qs.order_by('-id')[:50]
        elif 'with_ids' in params:
            item_ids = [int(i) for i in params['with_ids'].split(',')]
            items_qs = items_qs.filter(id__in=item_ids)
        elif 'since_id' in params:
            since_id = int(params['since_id'])
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
        
        response_data['items'] = items_data
    
    # Unread item IDs
    if 'unread_item_ids' in params:
        unread_ids = Item.objects.filter(
            feed__user=user,
            read_on_time=0
        ).values_list('id', flat=True)
        response_data['unread_item_ids'] = ','.join(map(str, unread_ids))
    
    # Saved item IDs
    if 'saved_item_ids' in params:
        saved_ids = Item.objects.filter(
            feed__user=user,
            is_saved=True
        ).values_list('id', flat=True)
        response_data['saved_item_ids'] = ','.join(map(str, saved_ids))
    
    # Links (for hot calculation)
    if 'links' in params:
        links = Link.objects.filter(feed__user=user).order_by('-weight')[:50]
        response_data['links'] = [
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
    
    return JsonResponse(response_data)
