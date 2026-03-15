/**
 * PrismaService — Database connection for NestJS runtime.
 *
 * Prisma 7 requires a driver adapter instead of the old Rust query engine.
 * We use @prisma/adapter-better-sqlite3 for SQLite.
 *
 * IMPORTANT: The DATABASE_URL env var must match what's in prisma.config.ts.
 * Both this file (runtime) and prisma.config.ts (CLI) read from the same env var
 * to ensure they point to the same database file.
 *
 * To switch to Postgres: replace PrismaBetterSqlite3 with PrismaPg,
 * update the provider in schema.prisma, and change DATABASE_URL.
 */

import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { PrismaClient } from '@prisma/generated';
import { PrismaBetterSqlite3 } from '@prisma/adapter-better-sqlite3';

// Initialize the SQLite driver adapter.
// This replaces the Rust engine that Prisma 5 used automatically.
const adapter = new PrismaBetterSqlite3({
  url: process.env.DATABASE_URL || 'file:./prisma/charli.db',
});

@Injectable()
export class PrismaService
  extends PrismaClient
  implements OnModuleInit, OnModuleDestroy
{
  constructor() {
    // Pass the adapter to PrismaClient — required in Prisma 7 (no Rust engine).
    super({ adapter });
  }

  async onModuleInit() {
    await this.$connect();
  }

  async onModuleDestroy() {
    await this.$disconnect();
  }
}
