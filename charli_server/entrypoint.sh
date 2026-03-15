#!/bin/sh
# CHARLI Server — Docker Entrypoint
#
# 1. Push the Prisma schema to create/sync the SQLite DB (idempotent).
# 2. Seed default devices if the DB is empty (upsert — safe to re-run).
# 3. Start the NestJS server.

echo "Running Prisma db push..."
npx prisma db push --skip-generate

echo "Running seed (upsert — safe to re-run)..."
npx ts-node prisma/seed.ts 2>/dev/null || true

echo "Starting CHARLI Server..."
exec node dist/main.js
