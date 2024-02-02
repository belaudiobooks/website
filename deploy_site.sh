python manage.py collectstatic --no-input
python manage.py update_translations
gcloud app deploy --verbosity=info --no-promote
