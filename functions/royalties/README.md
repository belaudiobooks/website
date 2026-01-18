# Royalties

This is a module that contains functions for parsing and processing royalty reports. We are getting reports from Spotify and INAudio in .xlsx format. Each report is converted into a dataclass object and later they are pushed to bigquery.

## Google Drive Setup

To fetch royalty reports from Google Drive, you need to set up a service account:

### 1. Create a Service Account

```bash
# Create service account
gcloud iam service-accounts create royalties-reader \
    --display-name="Royalties Reader"

# Get the service account email (you'll need this)
gcloud iam service-accounts list --filter="name:royalties-reader"
# Output: royalties-reader@PROJECT_ID.iam.gserviceaccount.com
```

### 2. Share the Google Drive Folder

1. Open the Google Drive folder containing the royalty reports
2. Click "Share"
3. Add the service account email (e.g., `royalties-reader@PROJECT_ID.iam.gserviceaccount.com`)
4. Grant "Viewer" permission
5. Click "Send" (ignore the warning about sending email to a service account)

### 3. Get the Folder ID

The folder ID is in the URL when viewing the folder:
```
https://drive.google.com/drive/folders/FOLDER_ID_HERE
```

### 4. For Local Development

Download a service account key:
```bash
gcloud iam service-accounts keys create ./service-account.json \
    --iam-account=royalties-reader@PROJECT_ID.iam.gserviceaccount.com
```

Then use it from `functions` folder:

```bash
python -m royalties.run_local --credentials service-accounts.json --folder FOLDER_ID --samples 3
```

### 5. For Cloud Functions

Attach the service account to your Cloud Function:
```bash
gcloud functions deploy FUNCTION_NAME \
    --service-account=royalties-reader@PROJECT_ID.iam.gserviceaccount.com \
    ...
```

The function will automatically use the attached service account's credentials:
```python
fetcher = GoogleDriveFetcher(folder_id="your-folder-id")
```

## Deploying the Cloud Function

To deploy the `push_royalties` function run `deploy.sh`.

## Debugging the Cloud Function

You can use the following command to debug:

```bash
GOOGLE_CLOUD_PROJECT=audiobooksbysite GOOGLE_APPLICATION_CREDENTIALS=key.json BIGQUERY_DATASET_ID=DATASET_ID  BIGQUERY_TABLE_ID=TABLE_ID GOOGLE_DRIVE_FOLDER_ID=FOLDER_ID  functions-framework-python --target push_royalties --debug
```

## Running tests

```bash
python3 -m unittest -v
```
