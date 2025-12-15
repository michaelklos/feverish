from django.contrib import admin
from datetime import datetime
from zoneinfo import ZoneInfo
from .models import FeverUser, Config, Feed, Group, FeedGroup, Item, Favicon, Link


def format_ts(ts):
    if not ts:
        return '-'
    return datetime.fromtimestamp(ts, tz=ZoneInfo("America/New_York")).strftime('%Y-%m-%d %H:%M:%S %Z')


@admin.register(FeverUser)
class FeverUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'installed_date', 'last_session_date', 'version')
    search_fields = ('email',)
    readonly_fields = ('installed_date', 'last_viewed_date', 'last_session_date')

    def installed_date(self, obj):
        return format_ts(obj.installed_on_time)
    installed_date.admin_order_field = 'installed_on_time'

    def last_session_date(self, obj):
        return format_ts(obj.last_session_on_time)
    last_session_date.admin_order_field = 'last_session_on_time'

    def last_viewed_date(self, obj):
        return format_ts(obj.last_viewed_on_time)
    last_viewed_date.admin_order_field = 'last_viewed_on_time'


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ('user',)
    raw_id_fields = ('user',)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'user')
    list_filter = ('user',)
    search_fields = ('title',)
    raw_id_fields = ('user',)


@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'user', 'is_spark', 'last_refreshed_date')
    list_filter = ('user', 'is_spark')
    search_fields = ('title', 'url', 'domain')
    raw_id_fields = ('user', 'favicon')
    readonly_fields = ('last_refreshed_date', 'last_updated_date', 'last_added_date')

    def last_refreshed_date(self, obj):
        return format_ts(obj.last_refreshed_on_time)
    last_refreshed_date.admin_order_field = 'last_refreshed_on_time'

    def last_updated_date(self, obj):
        return format_ts(obj.last_updated_on_time)
    last_updated_date.admin_order_field = 'last_updated_on_time'

    def last_added_date(self, obj):
        return format_ts(obj.last_added_on_time)
    last_added_date.admin_order_field = 'last_added_on_time'


@admin.register(FeedGroup)
class FeedGroupAdmin(admin.ModelAdmin):
    list_display = ('feed', 'group')
    raw_id_fields = ('feed', 'group')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'feed', 'author', 'is_saved', 'read_date', 'created_date')
    list_filter = ('is_saved', 'feed__user')
    search_fields = ('title', 'author', 'description')
    raw_id_fields = ('feed',)
    readonly_fields = ('created_date', 'added_date', 'read_date')

    def read_date(self, obj):
        return format_ts(obj.read_on_time)
    read_date.admin_order_field = 'read_on_time'

    def created_date(self, obj):
        return format_ts(obj.created_on_time)
    created_date.admin_order_field = 'created_on_time'

    def added_date(self, obj):
        return format_ts(obj.added_on_time)
    added_date.admin_order_field = 'added_on_time'


@admin.register(Favicon)
class FaviconAdmin(admin.ModelAdmin):
    list_display = ('url', 'url_checksum', 'last_cached_date')
    search_fields = ('url',)
    readonly_fields = ('last_cached_date',)

    def last_cached_date(self, obj):
        return format_ts(obj.last_cached_on_time)
    last_cached_date.admin_order_field = 'last_cached_on_time'


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'feed', 'item', 'weight', 'created_date')
    list_filter = ('is_blacklisted', 'is_item', 'is_local', 'is_first')
    search_fields = ('title', 'url')
    raw_id_fields = ('feed', 'item')
    readonly_fields = ('created_date',)

    def created_date(self, obj):
        return format_ts(obj.created_on_time)
    created_date.admin_order_field = 'created_on_time'
