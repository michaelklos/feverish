# Next Steps & Session Handoff

## Project Status: "Feverish" (Self-Hosted RSS Reader)
**Date:** December 15, 2025
**State:** Deployed & Operational on Azure Container Apps (ACA).

The application has been successfully refactored from "Fever" to "Feverish", containerized, and deployed to Azure using a shared infrastructure model.

## 🚀 Immediate Next Actions

### 1. Create Admin User (Required)
The application is running, but has no users. You must create a superuser to log in and configure feeds.
**Command:**
```bash
az containerapp exec \
  --name feverish-web \
  --resource-group feverish-rg \
  --command "python manage.py createsuperuser"
```

### 2. Configure Custom Domain
**Goal:** Map a custom domain (e.g., `reader.klos.com`) to the Container App.
*   **Current URL:** `https://news.klos.wtf`
*   **Status:** ✅ Complete
    *   Mapped `news.klos.wtf` to Container App.
    *   Configured Managed Certificate.
    *   Updated `DJANGO_ALLOWED_HOSTS`.

### 3. Verify Reeder Integration
**Goal:** Connect the Reeder app (iOS/Mac) to the Fever API.
*   **Endpoint:** `https://<your-domain>/fever/`
*   **Auth:** Uses the custom "Fever API Key" generated in the Django Admin interface (not the Django password).
*   **Task:** Log in to Django Admin -> Create Fever User -> Set Password -> Try connecting Reeder.

---

## 🏗 Infrastructure Details (Non-Obvious Context)

### Architecture
*   **Hosting:** Azure Container Apps (Serverless).
*   **Registry:** `kloshost.azurecr.io` (Shared Registry in `personal-rg`).
*   **Environment:** `klos-apps-env` (Shared Environment in `personal-rg`).
*   **Resource Group:** `feverish-rg` (Contains the Container Apps and Storage).
*   **Database:** PostgreSQL (Neon Serverless).
    *   **Persistence:** Managed by Neon.tech.
    *   **Connection:** Via `DATABASE_URL` secret.
    *   **Reason:** Switched from SQLite on Azure Files due to severe file locking issues with container concurrency.

### Deployment Pipeline
*   **Method:** GitHub Actions (`.github/workflows/deploy.yml`).
*   **Mechanism:**
    1.  Builds Docker images.
    2.  Pushes to `kloshost.azurecr.io`.
    3.  Runs `scripts/deploy_azure.sh`.
    4.  Uses `envsubst` to inject secrets/IDs into `deploy/*.yaml` templates.
    5.  Executes `az containerapp create/job create`.

### Configuration Quirks
*   **Web App (`feverish-web`)**:
    *   **Scale-to-Zero:** Enabled (`minReplicas: 0`). Expect a 10-15s "cold start" delay on first access.
*   **Worker Job (`feverish-worker`)**:
    *   **Schedule:** Hourly (`0 * * * *`).
    *   **Logic:** Checks for feeds before running. Exits early if DB is empty or no feeds exist.
*   **Secrets:**
    *   `SECRET_KEY` and `ACR_PASSWORD` are injected from GitHub Secrets.
    *   `ENV_ID` is fetched dynamically during deployment script execution.

## 🛠 Useful Commands

**View Logs:**
```bash
az containerapp logs show --name feverish-web --resource-group feverish-rg --follow
```

**Connect to Console:**
```bash
az containerapp exec --name feverish-web --resource-group feverish-rg --command bash
```

**Manual Trigger of Feed Refresh:**
```bash
az containerapp job start --name feverish-worker --resource-group feverish-rg
```
