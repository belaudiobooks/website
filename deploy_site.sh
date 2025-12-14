python manage.py collectstatic --no-input
python manage.py update_translations
gcloud app deploy --verbosity=info --no-promote

echo "To update deployed version:"
echo "https://console.cloud.google.com/appengine/versions?serviceId=default&project=audiobooksbysite"
