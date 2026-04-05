#!/bin/sh
# CHARLI Server — Docker Entrypoint
#
# 1. Push the Prisma schema to create/sync the SQLite DB (idempotent).
# 2. Seed default devices if the DB is empty (upsert — safe to re-run).
# 3. Start the NestJS server.

echo "Running Prisma db push..."
npx prisma db push

echo "Running seed (upsert — safe to re-run)..."
npx tsx prisma/seed.ts || true

echo "Starting CHARLI Server..."
exec node dist/src/main.js
