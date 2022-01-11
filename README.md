# Audiobooks backend

This project is created to allow users quickly find audioboooks that are translated to Belarusian 

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
**Note: Depends on your python installation you might need to user `python3` instead of `python` in the commands below
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





