# ── LodeOS frontend — SvelteKit (adapter-node) on Cloud Run ──────────────────
# Multi-stage: build with full deps, ship a lean runtime image.

# --- build stage ---
FROM node:20-slim AS build
WORKDIR /app

COPY package.json package-lock.json ./
# npm install (not ci) so optional platform-specific native deps resolve for the
# linux container even when the lockfile was generated on a different OS.
RUN npm install --no-audit --no-fund

COPY . .
# PUBLIC_API_BASE is inlined at build time for client code; pass --build-arg
# PUBLIC_API_BASE=https://<backend-cloud-run-url> at deploy.
ARG PUBLIC_API_BASE
ENV PUBLIC_API_BASE=${PUBLIC_API_BASE}
RUN npm run build

# --- runtime stage ---
FROM node:20-slim AS run
WORKDIR /app
ENV NODE_ENV=production

# Only what the adapter-node server needs to run.
COPY --from=build /app/build ./build
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/node_modules ./node_modules

# adapter-node honours PORT and HOST. Cloud Run injects $PORT (default 8080).
# PUBLIC_API_BASE was inlined into the client bundle in the build stage.
ENV PORT=8080
ENV HOST=0.0.0.0
EXPOSE 8080

CMD ["node", "build"]
