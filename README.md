# Audiobooks backend

This project is created to allow users quickly find audioboooks that are translated to Belarusian

![Django CI](https://github.com/belaudiobooks/website/actions/workflows/django.yml/badge.svg)

## Project structure
* `booksby` - main project folder with settings and project top url setup. Doesn't contain actual .
* `books` - folder containing the main part of the site. That's where the most work is done.
* `user` - app containing user model for admin page.
* `templates` - html templates, used by views in `books`.
* `functions` - python functions for Google Cloud batch processing. See [README](https://github.com/belaudiobooks/website/blob/main/functions/README.md).
* `locale` - contains localization (text in lacinka). See Lacinization section below in this file.
* `seed_media` - folder containing images for local development (fake book cover, people photo).
* `tests` - webdriver tests.

## Setup

**Note: You should have Python installed on your local env**

### Update ENV

Rename .env.dist to .env
Update values:
* DEBUG=True for dev env
* SECRET_KEY=_any symbols for dev, don't change in prod_
* ALLOWED_HOSTS=localhost for local

### Create Python virtual enviroment

Ensure venv is installed:
```
apt-get install python3-venv
```

In the project folder run:
```
python -m venv ./venv
source ./venv/bin/activate
```

### Install all dependencies

When virtual enviroment is activated in the step above:
**Note: comment psycopg2 in requirements.txt if you're using Mac with M1 chip**
```
pip install -r requirements.txt
```

### Seed DB with fake data

For local development we use SQLite so that developers don't need to install anything extra. To seed DB run the following:
```
python manage.py seed_db
```

This command does two things:
* Create `db.sqlite3` and seeds it with fake data.
* Copies `seed_media` dir to `media`.
* Creates superuser `admin@example.com` with password `12345`.

Running `seed_db` will overwrite existing `db.sqlite3` and `media`.

### Algolia setup (optional)

We use http://algolia.com to implement fast, fuzzy search. Algolia is a cloud service where we push JSON built from books/people and then use HTTP API to search over that data. For local development algolia is not necessary unless you work on the search part. To setup algolia you need to set a few variables, check .env.dist. To get app id and API keys - ask @nbeloglazov to add you to the algolia project.

To push data to algolia you can use the following command:

```shell
python manage.py push_data_to_algolia
```

Also that command can be triggered by visiting `/job/push_data_to_algolia` url. This is used by hourly GCP job that triggers sync with algolia. Currently we don't update algolia on every DB write. The job is setup via `cron.yaml` file. To deploy it run `gcloud app deploy cron.yaml`.

## Running

### Run the website
```
python manage.py runserver
```

And open: http://127.0.0.1:8000/

Also checkout admin page: http://127.0.0.1:8000/admin. Use `admin@example.com` and pass `12345`.

### Run tests

```shell
python manage.py test --verbosity=2
```

We have only integration webdriver tests that launch server, fill it with test data and then use webdriver to interact with the site and verify that it's behaving correctly.

## Linting and formatting

We use [Black](https://github.com/psf/black) for Python code formatting and [Flake8](https://flake8.pycqa.org/en/latest/) for linting.

One-time install:

```bash
pip install pre-commit
pre-commit install
```

To run formatter and linter:

```
pre-commit
```

Additionally it will automatically run formatter and linter on `git commit`.

## Google Cloud Setup and Deployment
Setup was followed by this tutorial: https://cloud.google.com/python/django/appengine with the adjustment to the our application.

The major issue is to setup DB as you have to use Cloud SQL Auth proxy in order to connect to the DB and do all migrations required.

1. Install and initialize the Google Cloud CLI
2. From the root app folder run

```
./deploy_site.sh
```

3. Select Y to start deployment

4. Verify that new version is working correctly and migrate traffic to the new version using https://console.cloud.google.com/appengine/versions

## Lacinization

We support two languages - cyrillic Belarusian and Lacinka. Lacinization is done programmatically. We use `belorthography` library for automatic lacinization. Interface language is implemented using standard Django internalization tools: https://docs.djangoproject.com/en/5.0/topics/i18n/translation/.

In development use the following patterns:

### Static text in templates

If text is static (hardcoded) use Django `translate` and `blocktranslate` tags:

```html
<div>{% translate "Тут тэкст" %}</div>
```

### Dynamic text in templates

If text is dynamic (comes from database) like book description or author name use our custom `dtranslate` tag. It will run lacinizator during page rendering:

```html
<div>{% dtranslate person.name %}</div>
```

### Renegenerating translations

When updating or adding new static strings (used with `translate` and `blocktranslate`) tags you need to regenerate translations. Translations are stored in `locale/be_Latn/LC_MESSAGES/django.po` file. To do it run:

```bash
python manage.py update_translations
```

## Image resizing

Book, photos and other images uploaded in size 500x500px. This is too big for catalog view where we show 150x150px covers. In order to reduce bandwidth images are automatically scaled down upon upload. Scaled down versions are used on pages like catalog. Here is the process:

1. Upon Book object modification in Book.save() we trigger a [Cloud Function](https://cloud.google.com/functions/docs/concepts/overview) using http request.

2. The function creates resized versions of all images. It skips already resized images so it should affect only newly added or updated image. See [functions/main.py](functions/main.py) for the function. [Deployed functions](https://console.cloud.google.com/functions/list).

3. Upon finishing the function triggers `/job/sync_image_cache` endpoint on the website. This forces the site to update its in-memory cache and build a mapping of original image names to the scaled-down versions.
