# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

司法监管系统 (Judiciary Supervision System) - A Django 4.2 + DRF backend serving both mini-program/app clients and two Django Admin backends.

## Development Commands

All commands must be run from the `judicial_system/` directory:

```bash
cd judicial_system

# Install dependencies (uses uv package manager)
uv sync

# Run development server
uv run python manage.py runserver

# Database migrations
uv run python manage.py makemigrations
uv run python manage.py migrate

# Create superuser (role must be 'admin')
uv run python manage.py createsuperuser

# Collect static files (production)
uv run python manage.py collectstatic --noinput
```

## Project Structure

```
judiciary-backend/
├── judicial_system/          # Django project root (working directory)
│   ├── manage.py
│   ├── config/               # Project configuration
│   │   ├── settings/         # Split settings (base/development/production)
│   │   ├── urls.py
│   │   └── admin_sites.py    # Two custom admin sites
│   ├── apps/                 # Django applications
│   └── utils/                # Shared utilities
├── admin-html/               # Static HTML for admin frontend
└── pyproject.toml            # uv dependencies
```

## Architecture

### Settings Module
- `config.settings.development` - Default, uses SQLite, DEBUG=True
- `config.settings.production` - Reads from env vars, uses BACKEND_BASE_URL for file URLs

### Authentication
Custom token auth (`utils/authentication.py`) - NOT JWT. Uses `Bearer <token>` header.
Tokens are stored in Django cache (LocMemCache) via `utils/token_manager.py`.

### Two Admin Sites
- `/admin/` - AdminSite: Full admin, requires `role='admin'`
- `/grid-admin/` - GridManagerSite: Limited, requires `role='grid_manager'` with managed grid

### User Roles (users.User.Role)
- `admin` - System administrator
- `grid_manager` - Grid manager (manages mediators in their grid)
- `mediator` - Field mediator (handles tasks)

### Apps
- **users**: Custom User model (AUTH_USER_MODEL), Organization, TrainingRecord, PerformanceScore
- **cases**: Task (纠纷/法律援助), task lifecycle: reported → assigned → processing → completed
- **grids**: Grid with boundary coordinates, center point, current_manager
- **content**: Article, Activity, Document with categories, CKEditor rich text
- **common**: Generic Attachment, MapConfig

### Key Patterns
- Attachments use `*_ids` CharField (comma-separated IDs) referencing common.Attachment
- Proxy models for admin filtering (e.g., `UnassignedTask`, `PerformanceHistory`)
- API endpoints under `/api/v1/`

## Environment Variables (Production)

Key variables in `.env` or Docker environment:
- `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DEBUG`
- `BACKEND_BASE_URL` - Used to generate absolute file URLs
- `TENCENT_MAP_KEY` - For geocoding in `utils/tencent_map.py`
- `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`

## Database Scripts

`db_scripts/` contains Python scripts for seeding test data. Run via `python db_scripts/01_基础信息.py` etc.
