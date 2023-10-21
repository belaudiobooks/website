# Google Cloud Functions

This directory contains functions that we run on [Google Cloud Functions](https://cloud.google.com/functions/docs/concepts/overview).

Functions defined in `main.py`.

### Testing locally

To test locally ensure that you `gcloud` installed and that you logged in properly by running:

```shell
gcloud auth application-default login
```

Then you can start local server that runs functions:

```shell
functions-framework-python --target $FUNCTION_NAME --debug
```

Where $FUNCTION_NAME should match name of a method in `main.py`. And then trigger function by running:

```shell
curl localhost:8080 \
  -X POST \
  -H "Content-Type: application/json" \
  -H "ce-id: 123451234512345" \
  -H "ce-specversion: 1.0" \
  -H "ce-time: 2020-01-02T12:34:56.789Z" \
  -H "ce-type: google.cloud.pubsub.topic.v1.messagePublished" \
  -H "ce-source: //pubsub.googleapis.com/projects/MY-PROJECT/topics/MY-TOPIC" \
  -d '{}'
```

### Deploying

To deploy functions run `deploy.sh`.