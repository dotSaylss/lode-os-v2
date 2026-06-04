#!/usr/bin/env bash
# ── Deploy LodeOS to Google Cloud Run via Cloud Build ────────────────────────
# Builds and deploys the FastAPI/ADK backend and the SvelteKit frontend to
# Cloud Run in the currently configured GCP project.
#
# Prereqs: gcloud auth'd, billing enabled, and these APIs on:
#   run.googleapis.com cloudbuild.googleapis.com aiplatform.googleapis.com
#
# Usage:  ./deploy.sh            # deploy both services
#         ./deploy.sh backend    # backend only
#         ./deploy.sh frontend   # frontend only
set -euo pipefail

PROJECT_ID="$(gcloud config get-value project 2>/dev/null)"
REGION="${REGION:-us-central1}"
BACKEND_SVC="mogul-backend"
FRONTEND_SVC="mogul-frontend"
TARGET="${1:-all}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "ERROR: no GCP project configured. Run: gcloud config set project <id>" >&2
  exit 1
fi

echo "▶ Project: ${PROJECT_ID}  Region: ${REGION}  Target: ${TARGET}"

deploy_backend() {
  echo "▶ Building backend image via Cloud Build…"
  gcloud builds submit --tag "gcr.io/${PROJECT_ID}/${BACKEND_SVC}" .

  echo "▶ Deploying backend to Cloud Run…"
  gcloud run deploy "${BACKEND_SVC}" \
    --image "gcr.io/${PROJECT_ID}/${BACKEND_SVC}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --timeout 300 \
    --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION}"

  BACKEND_URL="$(gcloud run services describe "${BACKEND_SVC}" --region "${REGION}" --format 'value(status.url)')"
  echo "✓ Backend: ${BACKEND_URL}"
}

deploy_frontend() {
  # NOTE: requires the SvelteKit app to use @sveltejs/adapter-node and a
  # frontend/Dockerfile. The frontend must point its API calls at the deployed
  # backend URL (set PUBLIC_API_BASE at build time).
  if [[ ! -f frontend/Dockerfile ]]; then
    echo "⚠ frontend/Dockerfile not found — skipping frontend (swap to adapter-node first)." >&2
    return 0
  fi
  BACKEND_URL="$(gcloud run services describe "${BACKEND_SVC}" --region "${REGION}" --format 'value(status.url)' 2>/dev/null || true)"

  echo "▶ Building frontend image via Cloud Build…"
  gcloud builds submit --tag "gcr.io/${PROJECT_ID}/${FRONTEND_SVC}" ./frontend

  echo "▶ Deploying frontend to Cloud Run…"
  gcloud run deploy "${FRONTEND_SVC}" \
    --image "gcr.io/${PROJECT_ID}/${FRONTEND_SVC}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars "PUBLIC_API_BASE=${BACKEND_URL}"

  FRONTEND_URL="$(gcloud run services describe "${FRONTEND_SVC}" --region "${REGION}" --format 'value(status.url)')"
  echo "✓ Frontend: ${FRONTEND_URL}"
}

case "${TARGET}" in
  backend)  deploy_backend ;;
  frontend) deploy_frontend ;;
  all)      deploy_backend; deploy_frontend ;;
  *) echo "Unknown target: ${TARGET} (use: backend | frontend | all)" >&2; exit 1 ;;
esac

echo "✓ Done."
