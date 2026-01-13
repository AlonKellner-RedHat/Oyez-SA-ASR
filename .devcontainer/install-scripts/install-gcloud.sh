#!/usr/bin/env bash
curl https://sdk.cloud.google.com | bash -s -- --disable-prompts --install-dir=$CLOUDSDK_INSTALL_DIR
gcloud components install gke-gcloud-auth-plugin
