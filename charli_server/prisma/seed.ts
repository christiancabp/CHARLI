/**
 * CHARLI Server — Database Seed Script
 *
 * Creates the default devices (desk hub + smart glasses) with API keys.
 * Run with: npx ts-node prisma/seed.ts
 *
 * This uses upsert, so it's safe to run multiple times — existing devices
 * won't be duplicated (matched by unique `name` field).
 *
 * IMPORTANT: Save the API keys printed to the console! They're needed
 * to configure each device's CHARLI_API_KEY env var. The keys are only
 * visible here and on POST /api/devices — GET /api/devices hides them.
 */

import 'dotenv/config';
import { PrismaClient } from './generated/prisma/client/client';
import { PrismaBetterSqlite3 } from '@prisma/adapter-better-sqlite3';
import { v4 as uuid } from 'uuid';

// Same adapter setup as prisma.service.ts — must point to the same DB.
const adapter = new PrismaBetterSqlite3({
  url: process.env.DATABASE_URL || 'file:./prisma/charli.db',
});
const prisma = new PrismaClient({ adapter });

// Default system prompts per device type.
// These match the prompts in src/ask/prompts/system-prompts.ts.
// {lang_name} is replaced at runtime with "English", "Spanish", etc.
const DESK_HUB_PROMPT = `You are CHARLI, a helpful voice assistant on a desk hub with a touchscreen.
Keep answers SHORT: 1 to 3 sentences maximum.
No bullet points, no numbered lists, no markdown symbols like * or #.
Speak naturally, like a friendly assistant sitting on someone's desk.
Respond in {lang_name}.`;

const GLASSES_PROMPT = `You are CHARLI, responding through smart glasses worn by your user.
Keep answers SHORT: 1 to 3 sentences maximum.
No bullet points, no numbered lists, no markdown symbols like * or #.
Speak naturally, like a personal assistant talking in someone's ear.
Be concise — the user is on the move and needs quick, clear answers.
Respond in {lang_name}.`;

const CLI_PROMPT = `You are CHARLI, a helpful personal assistant responding in a terminal/CLI.
You may use markdown formatting: headers, bold, code blocks, bullet points, numbered lists.
Give thorough, detailed answers — the user is reading on a screen, not listening.
For code, always use fenced code blocks with language tags.
Respond in {lang_name}.`;

async function main() {
  console.log('Seeding CHARLI database...');

  // Device name: "charli-home" (kebab-case, matches naming convention)
  // Device type: "desk-hub" (kebab-case, matches system-prompts.ts keys)
  const deskHub = await prisma.device.upsert({
    where: { name: 'charli-home' },
    update: {},
    create: {
      name: 'charli-home',
      type: 'desk-hub',
      apiKey: `chk_${uuid().replace(/-/g, '')}`,
      systemPrompt: DESK_HUB_PROMPT,
      maxTokens: 150,
    },
  });
  console.log(`  Desk hub: ${deskHub.name} (key: ${deskHub.apiKey})`);

  // Device name: "charli-glasses" (kebab-case)
  // Device type: "smart-glasses" (kebab-case, NOT "glasses")
  const glasses = await prisma.device.upsert({
    where: { name: 'charli-glasses' },
    update: {},
    create: {
      name: 'charli-glasses',
      type: 'smart-glasses',
      apiKey: `chk_${uuid().replace(/-/g, '')}`,
      systemPrompt: GLASSES_PROMPT,
      maxTokens: 150,
    },
  });
  console.log(`  Glasses:  ${glasses.name} (key: ${glasses.apiKey})`);

  // Device name: "charli-cli" (kebab-case)
  // Device type: "cli" — terminal client, allows markdown + longer responses
  const cli = await prisma.device.upsert({
    where: { name: 'charli-cli' },
    update: {},
    create: {
      name: 'charli-cli',
      type: 'cli',
      apiKey: `chk_${uuid().replace(/-/g, '')}`,
      systemPrompt: CLI_PROMPT,
      maxTokens: 1024,
    },
  });
  console.log(`  CLI:      ${cli.name} (key: ${cli.apiKey})`);

  console.log('Done! Save the API keys above — you will need them for device config.');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
