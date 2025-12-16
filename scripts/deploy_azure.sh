#!/bin/bash
set -e

# Variables
RG="feverish-rg"
ENV_RG="personal-rg"
ENV_NAME="klos-apps-env"
IMAGE_WEB="$1"
IMAGE_WORKER="$2"

# Check if images are provided
if [ -z "$IMAGE_WEB" ] || [ -z "$IMAGE_WORKER" ]; then
  echo "Usage: $0 <image-web> <image-worker>"
  exit 1
fi

# Get Environment ID
echo "Fetching Environment ID..."
export ENV_ID=$(az containerapp env show --name $ENV_NAME --resource-group $ENV_RG --query id --output tsv)
echo "Environment ID: $ENV_ID"

# Generate a random secret key if not provided (for initial setup, though in CI it should be a secret)
# In CI, we expect SECRET_KEY to be set in the environment.
if [ -z "$SECRET_KEY" ]; then
  echo "SECRET_KEY not set, generating one..."
  export SECRET_KEY=$(openssl rand -base64 32)
fi

export IMAGE_WEB
export IMAGE_WORKER
export ACR_PASSWORD
export DATABASE_URL

# Deploy Web App
echo "Deploying Web App..."
envsubst < deploy/feverish-web.yaml > deploy/feverish-web.generated.yaml
echo "--- Generated Web YAML ---"
cat deploy/feverish-web.generated.yaml
echo "--------------------------"
az containerapp create \
  --name feverish-web \
  --resource-group $RG \
  --yaml deploy/feverish-web.generated.yaml

# Deploy Worker Job
echo "Deploying Worker Job..."
envsubst < deploy/feverish-worker.yaml > deploy/feverish-worker.generated.yaml
echo "--- Generated Worker YAML ---"
cat deploy/feverish-worker.generated.yaml
echo "-----------------------------"
az containerapp job create \
  --name feverish-worker \
  --resource-group $RG \
  --yaml deploy/feverish-worker.generated.yaml

echo "Deployment Complete!"
