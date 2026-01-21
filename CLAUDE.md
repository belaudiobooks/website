# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django web application for discovering Belarusian-language audiobooks. The site features bilingual support (Cyrillic and Lacinka), search powered by Algolia, and deployment on Google Cloud Platform.

## Development Commands

### Initial Setup

```bash
# Create and activate virtual environment
python -m venv ./venv
source ./venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed database with fake data (creates db.sqlite3, copies seed_media to media, creates superuser)
python manage.py seed_db
# Superuser credentials: admin@example.com / 12345
```

### Running the Application

```bash
# Start development server
python manage.py runserver
# Access at http://127.0.0.1:8000/
# Admin panel at http://127.0.0.1:8000/admin
```

### Testing

```bash
# Run all integration tests (webdriver tests that launch server and interact with UI)
python manage.py test --verbosity=2

# Run tests for a specific module
python manage.py test books.tests.tests_book_page --verbosity=2
```

### Linting and Formatting

```bash
# One-time setup
pip install pre-commit
pre-commit install

# Run manually (also runs automatically on git commit via pre-commit hook)
pre-commit run --all-files
```

Uses Black for formatting and Flake8 for linting.

### Custom Management Commands

```bash
# Update Algolia search index
python manage.py push_data_to_algolia

# Regenerate lacinka translations after updating static strings
python manage.py update_translations

# Data sync commands (for production)
python manage.py pull_data_from_prod
python manage.py push_data_to_prod
```

### Deployment

```bash
# Deploy to Google App Engine
./deploy_site.sh
```

After deployment, verify the new version and migrate traffic via the Google Cloud Console.

## Architecture

### App Structure

- **booksby/** - Main Django project settings and root URL configuration
- **books/** - Core application containing models, views, templates, and business logic
- **user/** - Custom user model for admin (uses email instead of username)
- **partners/** - Partners app (accessible at `/partners`)
- **books/templates/** - HTML templates used by views
- **functions/** - Google Cloud Functions for batch processing (primarily image resizing)
- **locale/** - Lacinka translations for static text
- **books/tests/** - Integration tests using Selenium WebDriver

### Database

- **Local development**: SQLite (`db.sqlite3`)
- **Production**: Cloud SQL (PostgreSQL)
- Environment controlled by `ENV` variable in `.env` file

### Key Models

Defined in `books/models.py`:

- **Book** - Central model representing audiobooks with metadata
- **Person** - Represents authors, translators, narrators (roles derived from relationships)
- **Narration** - Specific recording of a book (one book can have multiple narrations)
- **Publisher** - Publishing houses/organizations
- **Tag** - Categorization for books (genres, themes)

Each model includes a `slug` field for SEO-friendly URLs.

### Bilingual Support (Lacinka)

The site supports two Belarusian orthographies:
- Cyrillic (standard)
- Lacinka (Latin script)

**Implementation:**

1. **Static text**: Use Django's `{% translate %}` and `{% blocktranslate %}` template tags. Translations stored in `locale/be_Latn/LC_MESSAGES/django.po`

2. **Dynamic text** (from database): Use custom `{% dtranslate %}` template tag which applies automatic lacinization at render time using the `belorthography` library

3. **Regenerating translations**: After adding/updating static strings, run:
   ```bash
   python manage.py update_translations
   ```

The `lacinify()` function in `books/models.py` converts Cyrillic to Latin using `belorthography.Orthography.LATIN_NO_DIACTRIC`.

### Template Tags and Filters

Custom template utilities in `books/templatetags/books_extras.py`:

- **dtranslate** - Dynamic lacinization for database content
- **gender** - Gender-aware word endings (Belarusian has grammatical gender)
- **by_plural** - Belarusian plural forms (complex rules: 1/2-4/5+)
- **duration** - Format narration duration (timedelta to "X гадзін Y хвілін")
- **resized_image** - Get URL for resized image versions
- **cite_source** - Render attribution for photos/text from external sources

### Search (Algolia)

Search is powered by Algolia cloud service:

- Data pushed to Algolia via `python manage.py push_data_to_algolia`
- Hourly GCP cron job syncs data (triggered via `/job/push_data_to_algolia` endpoint)
- Configuration in `.env`: `ALGOLIA_APPLICATION_ID`, `ALGOLIA_SEARCH_KEY`, `ALGOLIA_MODIFY_KEY`, `ALGOLIA_INDEX`
- Optional for local development unless working on search features

### Image Handling

Images are automatically resized for bandwidth optimization:

1. When Book is saved, triggers Google Cloud Function via HTTP request
2. Function (`functions/main.py`) creates resized versions (e.g., 300px for catalog view instead of 500px original)
3. Function calls back to `/job/sync_image_cache` endpoint to update in-memory cache
4. Templates use `resized_image` filter to get appropriate size

**Storage:**
- Local: Files in `media/` directory
- Production: Google Cloud Storage bucket

### URL Structure

Main routes defined in `books/urls.py`:

- `/` - Homepage/index
- `/catalog` - All books catalog
- `/catalog/<tag_slug>` - Filtered by tag
- `/books/<slug>` - Book detail page
- `/person/<slug>` - Person (author/narrator) detail page
- `/publisher/<slug>` - Publisher detail page
- `/search` - Search interface
- `/job/*` - Background job endpoints (Algolia sync, image cache, etc.)
- `/api/*` - API endpoints (markdown preview, livelib integration, orthography conversion)
- `/partners` - Partners section

### Testing Strategy

Tests are integration-focused using Selenium WebDriver (`books/tests/` directory). Tests:
1. Launch development server
2. Seed with test data
3. Use WebDriver to interact with pages
4. Verify correct behavior

Example test files:
- `tests_book_page.py`
- `tests_person_page.py`
- `tests_header_and_search.py`

### Google Cloud Functions

Defined in `functions/main.py`. To test locally:

```bash
cd functions
gcloud auth application-default login
functions-framework-python --target $FUNCTION_NAME --debug
curl localhost:8080
```

Deploy with `functions/deploy.sh`.

## Important Notes

- **Security**: Recent XSS vulnerability was patched (see commit 69a3c5b). Be careful with user input sanitization.
- **Middleware**: Custom `WwwRedirectMiddleware` in `books/middleware.py` handles www redirects
- **Admin customization**: Uses custom User model from `user` app (email-based auth instead of username)
- **Static files**: Local static files in `books/static/`, collected to `static/` on deployment
- **Debug toolbar**: Available but disabled by default. Set `ENABLE_DEBUG_TOOLBAR = True` in `booksby/settings.py` to enable.
