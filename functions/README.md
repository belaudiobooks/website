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
curl localhost:8080
```

### Deploying

To deploy functions run `deploy.sh`.
