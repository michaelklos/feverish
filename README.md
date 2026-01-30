# Feverish - Modern Python/Django Fever API Implementation

A Python/Django implementation of the Fever API, maintaining full backward compatibility with the Fever API v3. This allows you to use modern RSS reader apps like Reeder with a self-hosted, up-to-date backend.

> **Note:** This project is primarily designed as a backend API for Fever-compatible clients (like Reeder, ReadKit, etc.). While it includes a basic web interface for administration and debugging, the web UI is minimal and not intended as the primary way to consume feeds.

## Features

- Full Fever API v3 compatibility
- Works with Reeder and other Fever-compatible RSS readers
- Modern Python/Django codebase (Python 3.12+, Django 6.0)
- Database-agnostic (SQLite, PostgreSQL, MySQL)
- Easy deployment with Docker or Azure Container Apps
- RSS/Atom feed parsing with feedparser
- Multi-user support with custom feed titles
- Feed groups and organization
- Mark items as read/unread/saved
- Hot links calculation
- Comprehensive test suite
- Django admin interface

## Quick Start (Docker)

```bash
# Build and start the services
docker compose up --build

# Run migrations (in a new terminal)
docker compose run --rm web python manage.py migrate

# Set up demo data (optional)
docker compose run --rm web python setup_demo.py

# Refresh feeds
docker compose run --rm web python manage.py refresh_feeds --user demo@example.com

# Visit http://localhost:8000/
# Login: demo@example.com / demopassword
```

## Quick Start (Local Development)

```bash
# Install dependencies
pip install uv
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Run migrations
uv run python manage.py migrate

# Set up demo data (optional)
uv run python setup_demo.py

# Start server
uv run python manage.py runserver
```

## Production Deployment

### Azure Container Apps (Recommended)

The project is optimized for Azure Container Apps with scale-to-zero for cost efficiency.

**Prerequisites:**
- Azure CLI (`az`)
- GitHub CLI (`gh`)
- An Azure Subscription

**Architecture:**
- **Web App:** Django application (scale-to-zero enabled, expect 10-15s cold start)
- **Worker Job:** Scheduled feed refreshes (hourly cron: `0 * * * *`)
- **Database:** PostgreSQL via Neon Serverless (switched from SQLite due to file locking issues with container concurrency)
- **Registry:** Azure Container Registry
- **Environment:** Azure Container Apps Environment

**Deployment:**

1. Login to Azure:
   ```bash
   az login
   ```

2. Run the setup script:
   ```bash
   ./scripts/setup_azure_infra.sh
   ```

3. Deploy via GitHub Actions (push to `main`) or manually:
   ```bash
   ./scripts/deploy_azure.sh <web-image-tag> <worker-image-tag>
   ```

**Useful Commands:**
```bash
# View logs
az containerapp logs show --name feverish-web --resource-group feverish-rg --follow

# Connect to console
az containerapp exec --name feverish-web --resource-group feverish-rg --command bash

# Manually trigger feed refresh
az containerapp job start --name feverish-worker --resource-group feverish-rg

# Create superuser
az containerapp exec --name feverish-web --resource-group feverish-rg \
  --command "python manage.py createsuperuser"
```

### Generic Production Deployment

For VPS, DigitalOcean, or other environments:

1. Set environment variables:
   ```bash
   DEBUG=False
   SECRET_KEY=your-secure-random-key
   ALLOWED_HOSTS=yourdomain.com
   DATABASE_URL=postgres://user:pass@host:5432/dbname
   ```

2. Use a production WSGI server:
   ```bash
   uv add gunicorn
   uv run gunicorn feverish.wsgi:application --bind 0.0.0.0:8000
   ```

3. Set up a reverse proxy (Nginx/Apache) with SSL/TLS

## Client Configuration

### Reeder (iOS/macOS)

1. Open Reeder → Settings → Accounts → Add Account
2. Select "Fever"
3. Enter:
   - **Server**: `https://your-server.com` (include `/api/` if needed)
   - **Email**: Your Fever user email
   - **Password**: Your Fever user password

### API Key

The Fever API key is: `md5(email:password)`

Test authentication:
```bash
curl -X POST "https://your-server.com/api/" -d "api_key=YOUR_API_KEY"
```

## API Reference

All endpoints use `POST /api/` with `api_key` parameter.

**Query endpoints:**
- `?groups` - Feed groups
- `?feeds` - Feeds with group relationships
- `?items` - Items (supports `max_id`, `since_id`, `with_ids`, `feed_ids`, `group_ids`)
- `?favicons` - Favicon data
- `?unread_item_ids` - Comma-separated unread IDs
- `?saved_item_ids` - Comma-separated saved IDs
- `?links` - Hot links

**Mark operations:**
- `mark=item&as=read&id=123`
- `mark=item&as=unread&id=123`
- `mark=item&as=saved&id=123`
- `mark=item&as=unsaved&id=123`
- `mark=feed&as=read&id=123`
- `mark=group&as=read&id=123`

## Feed Management

```bash
# Refresh all feeds
uv run python manage.py refresh_feeds

# Refresh for specific user
uv run python manage.py refresh_feeds --user your@email.com

# Refresh specific feed
uv run python manage.py refresh_feeds --feed-id 1

# Verbose output
uv run python manage.py refresh_feeds --verbosity 2
```

For automated refresh, set up a cron job:
```bash
*/15 * * * * cd /path/to/feverish && uv run python manage.py refresh_feeds
```

## Development

```bash
# Run tests
uv run python manage.py test

# Run tests with coverage
uv run pytest --cov=api

# Create migrations
uv run python manage.py makemigrations

# Apply migrations
uv run python manage.py migrate
```

## Security

See [SECURITY.md](SECURITY.md) for detailed security considerations.

**Key points:**
- Passwords are stored using Django's PBKDF2 hashing (secure)
- The Fever API key uses MD5 per the original spec (compatibility trade-off)
- Always use HTTPS in production
- API key is transmitted with each request - HTTPS is critical

## Project Structure

```
feverish/
├── api/                    # Main Django app
│   ├── models.py           # Database models (FeverUser, Feed, Item, etc.)
│   ├── views.py            # Fever API implementation
│   ├── web_views.py        # Web interface
│   └── management/commands/
│       └── refresh_feeds.py
├── feverish/               # Django project settings
├── templates/              # HTML templates
├── static/                 # CSS, JS, images
├── deploy/                 # Azure deployment templates
├── scripts/                # Deployment scripts
└── firewall/               # Original PHP code (preserved for reference)
```

## Credits

- Original Fever by Shaun Inman (http://feedafever.com/)
- Django port and modernization by the community
