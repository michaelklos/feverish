# Fever - Modern Python/Django RSS Reader

A Python/Django port of the Fever RSS reader, maintaining full backward compatibility with the Fever API v3. This allows you to use modern RSS reader apps like Reeder with a self-hosted, up-to-date backend.

## Features

- ✅ Full Fever API v3 compatibility
- ✅ Works with Reeder and other Fever-compatible RSS readers
- ✅ Modern Python/Django codebase
- ✅ Database-agnostic (SQLite, PostgreSQL, MySQL supported)
- ✅ Easy deployment with uv package manager
- ✅ RSS/Atom feed parsing with feedparser
- ✅ Multi-user support
- ✅ Feed groups and organization
- ✅ Mark items as read/unread/saved
- ✅ Hot links calculation
- ✅ Comprehensive test suite (10 tests, all passing)
- ✅ Django admin interface
- ✅ Web-based reader interface

## Quick Start

```bash
# Clone and navigate to the repo
cd fever

# Install dependencies
pip install uv
uv sync

# Run migrations
uv run python manage.py migrate

# Set up demo data (optional)
uv run python setup_demo.py

# Refresh feeds
uv run python manage.py refresh_feeds --user demo@example.com

# Start server
uv run python manage.py runserver

# Visit http://localhost:8000/
# Login: demo@example.com / demopassword
```

## Requirements

- Python 3.12+
- uv package manager
- Database (SQLite by default, or PostgreSQL/MySQL)

## Installation

### 1. Clone and Setup

```bash
git clone https://github.com/michaelklos/fever.git
cd fever
```

### 2. Install Dependencies

The project uses `uv` for fast, reliable dependency management:

```bash
# Install uv if you haven't already
pip install uv

# Install project dependencies
uv sync
```

### 3. Configure Database

By default, the application uses SQLite. To use PostgreSQL or MySQL, update `fever_django/settings.py`:

**For PostgreSQL:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'fever_db',
        'USER': 'fever_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

**For MySQL:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'fever_db',
        'USER': 'fever_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 4. Initialize Database

```bash
# Run migrations
uv run python manage.py migrate

# Create a superuser (for Django admin)
uv run python manage.py createsuperuser
```

### 5. Create Fever User

You need to create a Fever user for API access. You can do this via Django shell:

```bash
uv run python manage.py shell
```

```python
from api.models import FeverUser

# Create user
user = FeverUser.objects.create_user(email='your@email.com', password='yourpassword')
user.save()

# Your API key will be: md5(your@email.com:yourpassword)
# You can use this in Reeder or other Fever-compatible clients
```

### 6. Add Feeds

You can add feeds via Django admin or shell:

**Via Django Admin:**
1. Run: `uv run python manage.py runserver`
2. Go to http://localhost:8000/admin/
3. Add feeds and groups

**Via Shell:**
```python
from api.models import Feed, Group, FeverUser
import hashlib

user = FeverUser.objects.first()

# Create a group
group = Group.objects.create(user=user, title="Tech News")

# Add a feed
feed = Feed.objects.create(
    user=user,
    title="Hacker News",
    url="https://news.ycombinator.com/rss",
    url_checksum=int(hashlib.md5("https://news.ycombinator.com/rss".encode()).hexdigest()[:8], 16)
)
feed.groups.add(group)
```

### 7. Refresh Feeds

```bash
# Refresh all feeds
uv run python manage.py refresh_feeds

# Refresh feeds for specific user
uv run python manage.py refresh_feeds --user your@email.com

# Refresh specific feed
uv run python manage.py refresh_feeds --feed-id 1
```

### 8. Run Server

```bash
uv run python manage.py runserver
```

The API will be available at: `http://localhost:8000/api/`

## API Configuration

### For Reeder (iOS/macOS)

1. Open Reeder
2. Go to Settings → Accounts → Add Account
3. Select "Fever"
4. Enter:
   - **Server**: `http://localhost:8000` (or your server URL)
   - **Email**: Your Fever user email
   - **Password**: Your Fever user password

### API Endpoint

The Fever API is available at: `http://your-server/api/`

### API Key Generation

The API key is calculated as: `md5(email:password_hash)`

You can test authentication with:
```bash
curl -X POST "http://localhost:8000/api/" \
  -d "api_key=YOUR_API_KEY"
```

## API Endpoints

The following Fever API v3 endpoints are supported:

- `POST /api/` - Main API endpoint
  - With `api_key` parameter for authentication
  - `?groups` - Get feed groups
  - `?feeds` - Get feeds
  - `?items` - Get items (with pagination)
  - `?favicons` - Get favicons
  - `?unread_item_ids` - Get unread item IDs
  - `?saved_item_ids` - Get saved item IDs
  - `?links` - Get hot links
  
- Mark operations:
  - `mark=item&as=read&id=123` - Mark item as read
  - `mark=item&as=unread&id=123` - Mark item as unread
  - `mark=item&as=saved&id=123` - Save item
  - `mark=feed&as=read&id=123` - Mark all feed items as read
  - `mark=group&as=read&id=123` - Mark all group items as read

## Automated Feed Refresh

To automatically refresh feeds, set up a cron job:

```bash
# Edit crontab
crontab -e

# Add this line to refresh every 15 minutes
*/15 * * * * cd /path/to/fever && uv run python manage.py refresh_feeds
```

Or use systemd timer, supervisor, or similar process managers.

## Development

```bash
# Run development server
uv run python manage.py runserver

# Run tests
uv run python manage.py test

# Create migrations after model changes
uv run python manage.py makemigrations

# Apply migrations
uv run python manage.py migrate
```

## Deployment

For production deployment:

1. Set `DEBUG = False` in `fever_django/settings.py`
2. Set a secure `SECRET_KEY`
3. Configure `ALLOWED_HOSTS`
4. Use a production database (PostgreSQL/MySQL)
5. Set up a production WSGI server (Gunicorn, uWSGI)
6. Configure a reverse proxy (Nginx, Apache)
7. Set up SSL/TLS certificates

Example with Gunicorn:
```bash
uv add gunicorn
uv run gunicorn fever_django.wsgi:application --bind 0.0.0.0:8000
```

## Backward Compatibility

This implementation maintains full backward compatibility with:
- Fever API v3 specification
- Fever-compatible RSS readers (Reeder, ReadKit, etc.)
- Original Fever database schema (with `fever_` prefix)

## Legacy PHP Code

The original PHP code is preserved in the `firewall/` directory for reference. The Django implementation in the `api/` app provides the same functionality with modern improvements.

## Troubleshooting

### API Key Issues
If you can't authenticate, verify your API key:
```python
import hashlib
email = "your@email.com"
password = "yourpassword"
api_key = hashlib.md5(f"{email}:{password}".encode()).hexdigest()
print(f"Your API key: {api_key}")
```

### Database Issues
- Ensure migrations are applied: `uv run python manage.py migrate`
- Check database connection settings in `fever_django/settings.py`

### Feed Refresh Issues
- Check feed URL is accessible
- Verify feed format (RSS/Atom)
- Check logs: `uv run python manage.py refresh_feeds --verbosity 2`

## Contributing

Contributions are welcome! Please ensure:
- Code follows Django best practices
- Tests are included for new features
- API compatibility is maintained
- Documentation is updated

## License

This project maintains the spirit of the original Fever by Shaun Inman while providing a modern, open-source implementation.

## Credits

- Original Fever by Shaun Inman (http://feedafever.com/)
- Django RSS reader port by the community
