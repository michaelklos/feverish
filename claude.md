# Feverish - Claude Code Context

## Project Overview

Feverish is a self-hosted RSS reader backend implementing the Fever API v3 specification. It's a personal tool for the owner, deployed on Azure Container Apps, allowing use of Fever-compatible RSS clients like Reeder.

**Production URL:** `https://news.klos.wtf`

## Tech Stack

- **Framework:** Django 6.0 / Python 3.12+
- **Database:** PostgreSQL via Neon Serverless (production), SQLite (local dev)
- **Hosting:** Azure Container Apps (scale-to-zero)
- **Package Manager:** uv
- **CI/CD:** GitHub Actions

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  Reeder / RSS   │────▶│  feverish-web   │
│     Client      │     │  (Django API)   │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Neon Postgres  │
                        └────────┬────────┘
                                 │
┌─────────────────┐              │
│ feverish-worker │──────────────┘
│  (Hourly Cron)  │
└─────────────────┘
```

- **feverish-web:** Django app serving the Fever API (scale-to-zero, 10-15s cold start)
- **feverish-worker:** Azure Container Apps Job running `refresh_feeds` hourly
- **Database:** Neon Serverless PostgreSQL (chosen over Azure Files SQLite due to file locking issues)

## Key Files

### API & Models
- `api/models.py` - Database models: FeverUser, Feed, Group, Item, Link, Favicon, Config, FeedGroup
- `api/views.py` - Fever API v3 implementation (authentication, queries, mark operations)
- `api/web_views.py` - Basic web interface views
- `api/utils.py` - Feed parsing and refresh logic
- `api/admin.py` - Django admin configuration

### Configuration
- `feverish/settings.py` - Django settings (uses `DATABASE_URL` env var, `dj-database-url`)
- `feverish/urls.py` - URL routing

### Deployment
- `.github/workflows/deploy.yml` - CI/CD pipeline
- `deploy/*.yaml` - Azure Container Apps templates (use `envsubst` for variable injection)
- `scripts/setup_azure_infra.sh` - Initial Azure infrastructure setup
- `scripts/deploy_azure.sh` - Deployment script
- `Dockerfile` - Container image definition
- `entrypoint.sh` - Container entrypoint (runs migrations on startup)

### Management Commands
- `api/management/commands/refresh_feeds.py` - Feed refresh command

## Database Schema

All tables use `fever_` prefix for Fever API compatibility.

| Model | Table | Purpose |
|-------|-------|---------|
| FeverUser | fever_users | Custom user model (email as username) |
| Config | fever_config | User settings (JSON in TextField) |
| Feed | fever_feeds | RSS/Atom feed subscriptions |
| Group | fever_groups | Feed categories |
| FeedGroup | fever_feeds_groups | Many-to-many relationship |
| Item | fever_items | Individual articles |
| Link | fever_links | Extracted links for "hot" calculation |
| Favicon | fever_favicons | Cached favicons |

**Key conventions:**
- All timestamps are Unix epoch (BigIntegerField) for Fever API compatibility
- URL checksums use first 15 hex chars of MD5 (fits in signed 64-bit int)
- `user_title` on Feed allows custom display names separate from canonical RSS title

## Authentication

The Fever API uses a specific auth scheme:
```python
api_key = md5(f"{email}:{password}".encode()).hexdigest()
```

- User passwords are stored securely with Django's PBKDF2 hashing
- The MD5 API key is stored in `fever_api_key` field for fast lookup
- This is a Fever spec requirement, not a security choice

## Common Tasks

### Local Development
```bash
uv sync                                    # Install dependencies
uv run python manage.py runserver          # Start dev server
uv run python manage.py test               # Run tests
uv run python manage.py refresh_feeds      # Refresh all feeds
uv run python setup_demo.py                # Create demo user/data
```

### Docker Development
```bash
docker compose up --build                  # Start services
docker compose run --rm web python manage.py migrate
```

### Azure Operations
```bash
# View logs
az containerapp logs show --name feverish-web --resource-group feverish-rg --follow

# Connect to console
az containerapp exec --name feverish-web --resource-group feverish-rg --command bash

# Trigger feed refresh manually
az containerapp job start --name feverish-worker --resource-group feverish-rg
```

## Design Decisions

1. **Database-agnostic:** Uses pure Django ORM with no PostgreSQL-specific features. Supports SQLite, PostgreSQL, MySQL without code changes.

2. **Unix timestamps:** All time fields use BigIntegerField with Unix epoch seconds (not Django DateTimeField) for Fever API compatibility.

3. **No raw SQL:** All database operations use Django ORM for portability.

4. **Scale-to-zero:** Web app uses `minReplicas: 0` to minimize Azure costs. Cold starts take 10-15 seconds.

5. **Neon over Azure Files:** SQLite on Azure Files had severe locking issues with container concurrency. Switched to Neon Serverless PostgreSQL.

6. **Separate worker job:** Feed refresh runs as a scheduled Azure Container Apps Job (hourly) rather than in-process to avoid blocking web requests.

## API Endpoints

All via `POST /api/` with `api_key` parameter:

- `?groups`, `?feeds`, `?items`, `?favicons` - Data queries
- `?unread_item_ids`, `?saved_item_ids` - ID lists
- `?links` - Hot links
- `mark=item&as=read&id=X` - Mark operations (read/unread/saved/unsaved)
- `mark=feed&as=read&id=X` - Mark all feed items
- `mark=group&as=read&id=X` - Mark all group items

## Testing

```bash
uv run python manage.py test               # Django test runner
uv run pytest                              # pytest (if configured)
```

Tests cover API authentication, all endpoints, and mark operations.

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| DATABASE_URL | Database connection string | sqlite:///db.sqlite3 |
| SECRET_KEY | Django secret key | (required in prod) |
| DEBUG | Debug mode | False |
| DJANGO_ALLOWED_HOSTS | Comma-separated hostnames | localhost |

## Related Documentation

- `SECURITY.md` - Security considerations and CodeQL findings
- `CONVERSION.md` - Historical: PHP to Django migration details
- `IOS_CLIENT_PLAN.md` - Future: Native iOS client development plan

## Infrastructure Details

- **Resource Group:** `feverish-rg`
- **Container Registry:** `kloshost.azurecr.io` (shared in `personal-rg`)
- **Environment:** `klos-apps-env` (shared in `personal-rg`)
- **Secrets:** `SECRET_KEY`, `DATABASE_URL`, `ACR_PASSWORD` injected via GitHub Secrets
