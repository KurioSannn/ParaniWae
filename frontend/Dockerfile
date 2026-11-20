# syntax=docker/dockerfile:1.7
# Digest = index multi-arsitektur (amd64+arm64) dari registry; perbarui lewat Dependabot/PR, jangan menebak.
ARG NODE_IMAGE=node:22-bookworm-slim@sha256:e9f565d32859f0cbfb52125eafe8be39390f24dac302dc3cdf566e8ba3ab21ee

# ---- deps: instal berdasarkan lockfile ----
FROM ${NODE_IMAGE} AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---- dev: hot reload; node_modules di named volume (bukan dari host) ----
FROM ${NODE_IMAGE} AS dev
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app
COPY --from=deps --chown=node:node /app/node_modules ./node_modules
COPY --chown=node:node docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && mkdir -p /app/.next && chown node:node /app /app/.next \
    && apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
USER node
EXPOSE 3000
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["npm", "run", "dev"]

# ---- build ----
FROM ${NODE_IMAGE} AS build
ENV NEXT_TELEMETRY_DISABLED=1
# Kosong = API same-origin lewat proxy Next (cookie first-party). Jangan default ke localhost.
ARG NEXT_PUBLIC_API_URL=
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN mkdir -p public/mediapipe/wasm && cp node_modules/@mediapipe/tasks-vision/wasm/* public/mediapipe/wasm/
RUN npm run build:worker && npm run build

# ---- prod: output standalone, non-root ----
FROM ${NODE_IMAGE} AS prod
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
WORKDIR /app
COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static
COPY --from=build --chown=node:node /app/public ./public
# Runtime prod tidak butuh package manager: hapus npm/yarn bawaan image (permukaan serangan + CVE npm bundel).
RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx /opt/yarn-* /usr/local/bin/yarn /usr/local/bin/yarnpkg
USER node
EXPOSE 3000
CMD ["node", "server.js"]
