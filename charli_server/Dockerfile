# ── Stage 1: Build ────────────────────────────────────────────────────
# Install deps, generate Prisma client, compile TypeScript.
FROM node:22-alpine AS builder

WORKDIR /app

# 1. Copy package files first — Docker caches this layer if they haven't changed.
COPY package*.json ./

# 2. Copy Prisma schema + config so `prisma generate` can run during install.
COPY prisma/schema.prisma prisma/schema.prisma
COPY prisma.config.ts prisma.config.ts

# 3. Install ALL dependencies (including devDependencies for the build step).
#    --legacy-peer-deps: @nestjs/swagger@11 expects @nestjs/common@^11 but we use v10.
RUN npm ci --legacy-peer-deps

# 4. Generate the Prisma client into prisma/generated/.
RUN npx prisma generate

# 5. Copy source code and build config, then compile.
COPY src/ src/
COPY tsconfig*.json ./
RUN npm run build


# ── Stage 2: Run ─────────────────────────────────────────────────────
# Slim production image — only what's needed to run the server + seed.
FROM node:22-alpine AS runner

WORKDIR /app

# Install curl for the health check.
RUN apk add --no-cache curl

# Copy everything we need from the builder.
COPY --from=builder /app/node_modules/ node_modules/
COPY --from=builder /app/dist/ dist/
COPY --from=builder /app/prisma/ prisma/
COPY --from=builder /app/prisma.config.ts prisma.config.ts
COPY --from=builder /app/package.json package.json
COPY --from=builder /app/tsconfig.json tsconfig.json

# Copy the seed script (needs ts-node at runtime for auto-seeding).
COPY prisma/seed.ts prisma/seed.ts

# Copy the entrypoint script.
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 3000

# Entrypoint pushes the schema + seeds on first run, then starts the server.
CMD ["/app/entrypoint.sh"]
