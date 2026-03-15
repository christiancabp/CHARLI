/**
 * CHARLI Server — Database Seed Script
 *
 * Creates the default devices (desk hub + glasses) with API keys.
 * Run with: npm run db:seed
 */

import { PrismaClient } from '@prisma/client';
import { v4 as uuid } from 'uuid';

const prisma = new PrismaClient();

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

async function main() {
  console.log('Seeding CHARLI database...');

  // Create desk hub device
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

  // Create glasses device
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

  console.log('Done! Save the API keys above — you will need them for device config.');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
