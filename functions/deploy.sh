gcloud functions deploy resize-images \
    --gen2 \
    --runtime=python311 \
    --region=europe-west1 \
    --source=. \
    --entry-point=resize_images \
    --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
    --trigger-event-filters="bucket=books_media" \
    --trigger-location=eu

