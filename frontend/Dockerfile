# syntax=docker/dockerfile:1
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

FROM node:20-alpine AS builder
WORKDIR /app
# NOTE: no NEXT_PUBLIC_* build ARGs here anymore. The backend URL and Google
# IDs are now read at RUNTIME via src/app/api/config/route.ts, so the exact
# same image works across environments - set BACKEND_API_URL,
# GOOGLE_CLIENT_ID, GOOGLE_MAPS_API_KEY as plain environment variables on
# whatever's running the container (Cloud Run, docker-compose, etc.) and
# restart; no rebuild required. See src/lib/runtimeConfig.ts for why.
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
