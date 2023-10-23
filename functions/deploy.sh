gcloud functions deploy resize-images \
    --gen2 \
    --runtime=python311 \
    --region=europe-west1 \
    --source=. \
    --entry-point=resize_images \
    --trigger-http \
    --allow-unauthenticated \
    --timeout=600s

