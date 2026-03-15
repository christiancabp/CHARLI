/**
 * Prisma 7 CLI Configuration
 *
 * This file configures the Prisma CLI (migrate, db push, studio, seed).
 * It replaces the old `url = env("DATABASE_URL")` that used to live in schema.prisma.
 *
 * IMPORTANT: The DATABASE_URL env var is the single source of truth for the DB path.
 * It's read here (for CLI) and in src/prisma/prisma.service.ts (for runtime).
 * Both must agree — if you change it, update .env and restart both.
 *
 * Path format: "file:./prisma/charli.db" (relative to project root)
 */

import 'dotenv/config';
import { defineConfig } from 'prisma/config';

export default defineConfig({
  earlyAccess: true,
  schema: 'prisma/schema.prisma',
  migrate: {
    async seed(prisma) {
      // Seed is run via: npx ts-node prisma/seed.ts
      // (not through this hook — we need the adapter setup in seed.ts)
    },
  },
  datasource: {
    // IMPORTANT: This path is relative to the project root (where you run npx prisma).
    // The DB file lives at charli_server/prisma/charli.db.
    url: process.env.DATABASE_URL || 'file:./prisma/charli.db',
  },
});
