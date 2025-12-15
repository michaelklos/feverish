#!/bin/bash
set -e

# Variables
SHARED_RG="personal-rg"
APP_RG="feverish-rg"
LOCATION="eastus"
ACA_ENV="klos-apps-env"
STORAGE_NAME="feverishstoreklos" # Fixed name for consistency
SHARE_NAME="feverishdata"

echo "--- Setting up Azure Infrastructure ---"

# 1. Create App Resource Group
echo "Creating Resource Group: $APP_RG..."
az group create --name $APP_RG --location $LOCATION

# 2. Create Container Apps Environment (in Shared RG)
echo "Creating Container Apps Environment: $ACA_ENV in $SHARED_RG..."
az containerapp env create \
  --name $ACA_ENV \
  --resource-group $SHARED_RG \
  --location $LOCATION \
  --query "properties.provisioningState"

# 3. Create Storage Account (in App RG)
echo "Creating Storage Account: $STORAGE_NAME..."
az storage account create \
  --name $STORAGE_NAME \
  --resource-group $APP_RG \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2

# 4. Create File Share
echo "Creating File Share: $SHARE_NAME..."
CONNECTION_STRING=$(az storage account show-connection-string --name $STORAGE_NAME --resource-group $APP_RG --output tsv)
az storage share create --name $SHARE_NAME --connection-string $CONNECTION_STRING

# 5. Get Storage Key
STORAGE_KEY=$(az storage account keys list --resource-group $APP_RG --account-name $STORAGE_NAME --query "[0].value" --output tsv)

# 6. Link Storage to Container Apps Environment
echo "Linking Storage to Container Apps Environment..."
az containerapp env storage set \
  --name $ACA_ENV \
  --resource-group $SHARED_RG \
  --storage-name $SHARE_NAME \
  --azure-file-account-name $STORAGE_NAME \
  --azure-file-account-key $STORAGE_KEY \
  --azure-file-share-name $SHARE_NAME \
  --access-mode ReadWrite

echo "--- Done! ---"
echo "Storage Account Name: $STORAGE_NAME"
echo "File Share Name: $SHARE_NAME"
echo "Environment Name: $ACA_ENV"
