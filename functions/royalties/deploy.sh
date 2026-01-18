# Store the current directory and switch to parent if needed
cd "$(dirname "$0")/.."

gcloud functions deploy push-royalties \
    --gen2 \
    --runtime=python311 \
    --region=europe-west1 \
    --source=. \
    --entry-point=push_royalties \
    --trigger-http \
    --allow-unauthenticated \
    --timeout=600s \
    --env-vars-file=royalties/.env.yaml \
    --service-account=royalties-importer@audiobooksbysite.iam.gserviceaccount.com
