from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import hashlib


class FeverUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        # Store the API key for Fever compatibility (MD5 required by Fever API spec)
        if password:
            # Note: MD5 is used here for API key generation per Fever spec, not for password storage
            user.fever_api_key = hashlib.md5(f"{email}:{password}".encode()).hexdigest()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class FeverUser(AbstractBaseUser, PermissionsMixin):
    """User model for Fever authentication"""
    email = models.EmailField(unique=True)
    fever_api_key = models.CharField(max_length=32, blank=True, db_index=True)  # MD5 hash
    activation_key = models.CharField(max_length=255, blank=True)
    installed_on_time = models.BigIntegerField(default=0)
    last_viewed_on_time = models.BigIntegerField(default=0)
    last_session_on_time = models.BigIntegerField(default=0)
    version = models.IntegerField(default=143)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = FeverUserManager()

    USERNAME_FIELD = 'email'

    def set_password(self, raw_password):
        """
        Override to also set fever_api_key.

        Note: The Fever API spec requires MD5 hashing for API keys (md5(email:password)).
        This is less secure than modern password hashing but necessary for API compatibility.
        The actual Django password is stored securely using Django's password hashing.
        """
        super().set_password(raw_password)
        if raw_password:
            # MD5 required for Fever API compatibility - not for password storage
            self.fever_api_key = hashlib.md5(f"{self.email}:{raw_password}".encode()).hexdigest()

    def get_api_key(self):
        """Get Fever API key"""
        return self.fever_api_key

    class Meta:
        db_table = 'fever_users'


class Config(models.Model):
    """Configuration storage"""
    user = models.OneToOneField(FeverUser, on_delete=models.CASCADE, related_name='config')
    cfg = models.TextField()  # JSON serialized config
    prefs = models.TextField()  # JSON serialized preferences

    class Meta:
        db_table = 'fever_config'


class Favicon(models.Model):
    """Favicon storage"""
    cache = models.TextField()  # Base64 encoded favicon data
    url = models.CharField(max_length=255)
    url_checksum = models.BigIntegerField(unique=True)
    last_cached_on_time = models.BigIntegerField(default=0)

    class Meta:
        db_table = 'fever_favicons'
        indexes = [
            models.Index(fields=['last_cached_on_time']),
        ]


class Group(models.Model):
    """Feed groups"""
    user = models.ForeignKey(FeverUser, on_delete=models.CASCADE, related_name='fever_groups')
    title = models.CharField(max_length=255)
    item_excerpts = models.SmallIntegerField(default=-1)
    item_allows = models.SmallIntegerField(default=-1)
    unread_counts = models.SmallIntegerField(default=-1)
    sort_order = models.SmallIntegerField(default=-1)

    class Meta:
        db_table = 'fever_groups'
        indexes = [
            models.Index(fields=['title']),
        ]


class Feed(models.Model):
    """RSS/Atom feeds"""
    user = models.ForeignKey(FeverUser, on_delete=models.CASCADE, related_name='feeds')
    favicon = models.ForeignKey(Favicon, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    url_checksum = models.BigIntegerField(unique=True, blank=True)
    site_url = models.CharField(max_length=255, null=True, blank=True)
    domain = models.CharField(max_length=255, null=True, blank=True)
    requires_auth = models.BooleanField(default=False)
    auth = models.CharField(max_length=255, null=True, blank=True)  # username:password
    is_spark = models.BooleanField(default=False)
    prevents_hotlinking = models.BooleanField(default=False)
    item_excerpts = models.SmallIntegerField(default=-1)
    item_allows = models.SmallIntegerField(default=-1)
    unread_counts = models.SmallIntegerField(default=-1)
    sort_order = models.SmallIntegerField(default=-1)
    last_refreshed_on_time = models.BigIntegerField(default=0)
    last_updated_on_time = models.BigIntegerField(default=0)
    last_added_on_time = models.BigIntegerField(default=0)
    groups = models.ManyToManyField(Group, through='FeedGroup', related_name='feeds')

    def save(self, *args, **kwargs):
        if not self.url_checksum and self.url:
            # Calculate checksum compatible with BigIntegerField (signed 64-bit)
            # We take first 15 hex chars (60 bits) to be safe
            self.url_checksum = int(hashlib.md5(self.url.encode()).hexdigest()[:15], 16)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'fever_feeds'
        indexes = [
            models.Index(fields=['favicon']),
            models.Index(fields=['title']),
            models.Index(fields=['domain']),
            models.Index(fields=['is_spark']),
            models.Index(fields=['last_refreshed_on_time']),
            models.Index(fields=['last_updated_on_time']),
            models.Index(fields=['last_added_on_time']),
        ]


class FeedGroup(models.Model):
    """Many-to-many relationship between feeds and groups"""
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        db_table = 'fever_feeds_groups'
        indexes = [
            models.Index(fields=['feed', 'group']),
        ]
        unique_together = ['feed', 'group']


class Item(models.Model):
    """Feed items (articles)"""
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE, related_name='items')
    uid = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    author = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    link = models.CharField(max_length=255, null=True, blank=True)
    url_checksum = models.BigIntegerField()
    read_on_time = models.BigIntegerField(default=0)
    is_saved = models.BooleanField(default=False)
    created_on_time = models.BigIntegerField()
    added_on_time = models.BigIntegerField()

    class Meta:
        db_table = 'fever_items'
        indexes = [
            models.Index(fields=['feed']),
            models.Index(fields=['feed', 'uid']),
            models.Index(fields=['title']),
            models.Index(fields=['url_checksum']),
            models.Index(fields=['read_on_time']),
            models.Index(fields=['is_saved']),
            models.Index(fields=['created_on_time']),
            models.Index(fields=['added_on_time']),
        ]


class Link(models.Model):
    """Links extracted from items for hot calculation"""
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE, related_name='links')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='extracted_links')
    is_blacklisted = models.BooleanField(default=False)
    is_item = models.BooleanField(default=False)
    is_local = models.BooleanField(default=False)
    is_first = models.BooleanField(default=False)
    title = models.CharField(max_length=255, null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)
    url_checksum = models.BigIntegerField()
    title_url_checksum = models.BigIntegerField()
    weight = models.IntegerField(default=0)
    created_on_time = models.BigIntegerField()

    class Meta:
        db_table = 'fever_links'
        indexes = [
            models.Index(fields=['feed']),
            models.Index(fields=['item']),
            models.Index(fields=['created_on_time']),
            models.Index(fields=['weight']),
            models.Index(fields=['url_checksum']),
            models.Index(fields=['title_url_checksum']),
            models.Index(fields=['is_blacklisted']),
            models.Index(fields=['is_item']),
            models.Index(fields=['is_local']),
            models.Index(fields=['is_first']),
        ]
