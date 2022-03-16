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

### Test initial state
**Note: Depends on your python installation you might need to user `python3` instead of `python` in the commands below**
```
python manage.py runserver
```
check in the browser that you can see home page: http://127.0.0.1:8000/

### Setup django and project:

Run in the project folder:
```
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```
Create superuser creds to access Admin site at: http://127.0.0.1:8000/admin

### Run the project:
```
python manage.py runserver
```

### Run the project with fullbooks data
It is possible to run server using fresh temporary sqlite3 database initialized with full books data. This way you get view of production-like data. First, make sure that 'data' submodule is cloned. Then run the following command:

```shell
python manage.py runserver_with_tmp_db --settings=booksby.sqlite_settings
```

It will:
1. Create temporary database in `/tmp` directory.
2. Fill it with data from `data` submodule folder.
3. Start server using `data` as `MEDIA_ROOT`.

### Run tests

To run tests you need to have chromedriver installed and available on path. Install chromedriver that matches your current chrome version from here: https://chromedriver.chromium.org/downloads. Then run tests:

```shell
python manage.py test --settings=booksby.sqlite_settings --verbosity=2
```

### Algolia setup

We use http://algolia.com to implement fast, fuzzy book and people search. Algolia is a cloud service where we push JSON built from books/people and then use HTTP API to search over that data. For local development algolia is not necessary unless you work on the search part. To setup algolia you need to set a few variables, check .env.dist. To get app id and API keys - ask @nbeloglazov to add you to the algolia project. 

To push data to algolia you can use the following command:

```shell
python manage.py push_data_to_algolia --settings=booksby.sqlite_settings
```

Also that command can be triggered by visiting `/push_data_to_algolia` url. This is used by hourly GCP job that triggers sync with algolia. Currently we don't update algolia on every DB write. The job is setup via `cron.yaml` file. To deploy it run `gcloud app deploy cron.yaml`.

## Books data

Data about books, authors, narrators, translators and so on is currently stored in separate project: https://github.com/belaudiobooks/data. This project contains scripts that manage and update that data: synchronizing its data with external resources such as https://knizhnyvoz.by, podcasts, https://litres.ru and others. To manage data run `sync.py` script like the following

1. [Clone](https://github.blog/2016-02-01-working-with-submodules/) `data` repo to separate folder, 
    for example as `data`.
2. Run script:
    ```shell
    python -m data_scripts.sync podcasts
    ```
    Last argument is command to run. Check `sync.py` for the list of commands.
3. It will run maybe updates `data/data.json`. If it does - check changes and commit them.

### Remote sync scripts

There are 2 scripts that allow to pull or push data between JSON format `data/data.json` and database (usually remote, postgresql running on GCP). 

Pull data. Connects to database and pulls objects and media files and stores them in JSON file and corresponding media files. Usage:

```shell
python manage.py pull_data_from_prod --settings=booksby.sqlite_settings
```

Push data. Connects to database and pushes objects and media files from JSON file.

```shell
python manage.py push_data_to_prod  --settings=booksby.sqlite_settings 
```