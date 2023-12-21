# Audiobooks backend

This project is created to allow users quickly find audioboooks that are translated to Belarusian

![Django CI](https://github.com/belaudiobooks/website/actions/workflows/django.yml/badge.svg)

## Project structure
* booksby - main project folder with settings and project top url setup
* books, user, person - apps for each instance 
* templates - all html templates based on each other
* static - static files, css, js, images
* data - contains data.json with books data and scripts that synchronize data. See Books Data section below.

## Backend setup

**Note: You should have Python and Postgresql installed on your local env**

### Update ENV

Rename .env.dist to .env
Update values:
* DEBUG=True for dev env
* SECRET_KEY=_any symbols for dev, don't change in prod_
* ALLOWED_HOSTS=localhost for local
* DATABASE - your Postgres DB values to connect to local DB

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

### Run the project:
```
python manage.py runserver
```

And open: http://127.0.0.1:8000/

Also checkout admin page: http://127.0.0.1:8000/admin. Use `admin@example.com` and pass `12345`.

### Run tests

To run tests you need to have chromedriver installed and available on path. Install chromedriver that matches your current chrome version from here: https://chromedriver.chromium.org/downloads. Then run tests:

```shell
python manage.py test --verbosity=2
```

### Algolia setup

We use http://algolia.com to implement fast, fuzzy book and people search. Algolia is a cloud service where we push JSON built from books/people and then use HTTP API to search over that data. For local development algolia is not necessary unless you work on the search part. To setup algolia you need to set a few variables, check .env.dist. To get app id and API keys - ask @nbeloglazov to add you to the algolia project.

To push data to algolia you can use the following command:

```shell
python manage.py push_data_to_algolia
```

Also that command can be triggered by visiting `/job/push_data_to_algolia` url. This is used by hourly GCP job that triggers sync with algolia. Currently we don't update algolia on every DB write. The job is setup via `cron.yaml` file. To deploy it run `gcloud app deploy cron.yaml`.

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

## Image resizing

Book, photos and other images uploaded in size 500x500px. This is too big for catalog view where we show 150x150px covers. In order to reduce bandwidth images are automatically scaled down upon upload. Scaled down versions are used on pages like catalog. Here is the process:

1. Upon Book object modification in Book.save() we trigger a [Cloud Function](https://cloud.google.com/functions/docs/concepts/overview) using http request.

2. The function creates resized versions of all images. It skips already resized images so it should affect only newly added or updated image. See [functions/main.py](functions/main.py) for the function. [Deployed functions](https://console.cloud.google.com/functions/list).

3. Upon finishing the function triggers `/job/sync_image_cache` endpoint on the website. This forces the site to update its in-memory cache and build a mapping of original image names to the scaled-down versions.