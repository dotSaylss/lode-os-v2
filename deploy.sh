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
BACKEND_SVC="lode-backend"
FRONTEND_SVC="lode-frontend"
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
  if [[ -z "${BACKEND_URL}" ]]; then
    echo "⚠ backend not deployed yet — deploy backend first so the frontend can reach it." >&2
    return 1
  fi
  IMAGE="gcr.io/${PROJECT_ID}/${FRONTEND_SVC}"

  # PUBLIC_API_BASE must be baked into the client bundle at BUILD time, so it's
  # passed as a Docker build-arg via a Cloud Build docker step. The build config
  # is written to a temp file in ./frontend (gcloud's `--config=-` stdin form is
  # unreliable across shells), then cleaned up.
  echo "▶ Building frontend image via Cloud Build (PUBLIC_API_BASE=${BACKEND_URL})…"
  CB_CONFIG="$(mktemp -t cloudbuild.frontend.XXXXXX.yaml)"
  cat > "${CB_CONFIG}" <<YAML
steps:
  - name: gcr.io/cloud-builders/docker
    args:
      - build
      - --build-arg
      - PUBLIC_API_BASE=${BACKEND_URL}
      - -t
      - ${IMAGE}
      - .
images:
  - ${IMAGE}
YAML
  gcloud builds submit ./frontend --config="${CB_CONFIG}"
  rm -f "${CB_CONFIG}"

  echo "▶ Deploying frontend to Cloud Run…"
  # PUBLIC_API_BASE is also set as a RUNTIME env var: the client resolves the
  # backend via $env/dynamic/public (read at run time), so the build-arg alone
  # isn't enough — without this the browser falls back to http://localhost:8000.
  gcloud run deploy "${FRONTEND_SVC}" \
    --image "${IMAGE}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars "PUBLIC_API_BASE=${BACKEND_URL}"

  FRONTEND_URL="$(gcloud run services describe "${FRONTEND_SVC}" --region "${REGION}" --format 'value(status.url)')"
  echo "✓ Frontend: ${FRONTEND_URL}"

  # Allow the deployed frontend origin through the backend's CORS.
  echo "▶ Wiring backend CORS to allow ${FRONTEND_URL}…"
  gcloud run services update "${BACKEND_SVC}" \
    --region "${REGION}" \
    --update-env-vars "FRONTEND_ORIGINS=${FRONTEND_URL}" >/dev/null
  echo "✓ Backend CORS updated."
}

case "${TARGET}" in
  backend)  deploy_backend ;;
  frontend) deploy_frontend ;;
  all)      deploy_backend; deploy_frontend ;;
  *) echo "Unknown target: ${TARGET} (use: backend | frontend | all)" >&2; exit 1 ;;
esac

echo "✓ Done."
