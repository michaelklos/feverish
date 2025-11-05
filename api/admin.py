from django.contrib import admin
from .models import FeverUser, Config, Feed, Group, FeedGroup, Item, Favicon, Link


@admin.register(FeverUser)
class FeverUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'installed_on_time', 'last_session_on_time', 'version')
    search_fields = ('email',)
    readonly_fields = ('installed_on_time', 'last_viewed_on_time', 'last_session_on_time')


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
    list_display = ('title', 'url', 'user', 'is_spark', 'last_refreshed_on_time')
    list_filter = ('user', 'is_spark')
    search_fields = ('title', 'url', 'domain')
    raw_id_fields = ('user', 'favicon')


@admin.register(FeedGroup)
class FeedGroupAdmin(admin.ModelAdmin):
    list_display = ('feed', 'group')
    raw_id_fields = ('feed', 'group')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'feed', 'author', 'is_saved', 'read_on_time', 'created_on_time')
    list_filter = ('is_saved', 'feed__user')
    search_fields = ('title', 'author', 'description')
    raw_id_fields = ('feed',)
    readonly_fields = ('created_on_time', 'added_on_time')


@admin.register(Favicon)
class FaviconAdmin(admin.ModelAdmin):
    list_display = ('url', 'url_checksum', 'last_cached_on_time')
    search_fields = ('url',)
    readonly_fields = ('last_cached_on_time',)


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'feed', 'item', 'weight', 'created_on_time')
    list_filter = ('is_blacklisted', 'is_item', 'is_local', 'is_first')
    search_fields = ('title', 'url')
    raw_id_fields = ('feed', 'item')
