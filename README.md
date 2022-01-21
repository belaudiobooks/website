# Audiobooks backend

This project is created to allow users quickly find audioboooks that are translated to Belarusian 

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
It is possible to run server using fresh temporary sqlite3 database initialized with full books data. This way you get view of production-like data. First, it requires cloning https://github.com/belaudiobooks/data repo. Let's say you cloned it as `belaudbiooks_data` repo that sits next to this repo. Then run the following command:

```shell
BOOKS_DATA_DIR=../audiobooks_data python manage.py runserver_with_tmp_db --settings=booksby.sqlite_settings
```

It will:
1. Create temporary database in `/tmp` directory.
2. Fill it with data from `../audiobooks_data` folder.
3. Start server using `../audiobooks_data` as `MEDIA_ROOT`.

## Books data

Data about books, authors, narrators, translators and so on is currently stored in separate project: https://github.com/belaudiobooks/data. This project contains scripts that manage and update that data: synchronizing its data with external resources such as https://knizhnyvoz.by, podcasts, https://litres.ru and others. To manage data run `sync.py` script like the following

1. Checkout belaudiobooks/data repo to separate folder, for example as `belaudbiooks_data`.
2. Run script:
    ```shell
    BOOKS_DATA_DIR=../audiobooks_data python -m data.sync podcasts
    ```
    Last argument is command to run. Check `sync.py` for the list of commands.
3. It will run maybe updates `belaudbiooks_data/data.json`. If it does - check changes and commit them.



