/**
 * CHARLI Server — Bootstrap
 *
 * Central backend for all CHARLI devices (desk hub, glasses, future devices).
 * Runs on the Mac Mini alongside OpenClaw and the Python ML sidecar.
 */

import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Global validation pipe for DTOs
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      transform: true,
    }),
  );

  // CORS — allow all origins (private Tailscale network)
  app.enableCors();

  // ── Swagger API Docs ────────────────────────────────────────────
  // Available at http://localhost:3000/docs
  const config = new DocumentBuilder()
    .setTitle('CHARLI Server')
    .setDescription(
      `Central API gateway for all CHARLI devices (desk hub, glasses, future devices).

**Architecture:** Devices send audio/text → this server orchestrates STT, LLM, TTS → returns audio/text.

**Auth:** All \`/api/*\` endpoints require an \`X-API-Key\` header. Get a key by registering a device via \`POST /api/devices\` (requires admin key).

**Python Sidecar:** STT (faster-whisper) and TTS (espeak-ng/Piper) run in a separate Python process on localhost:3001. This server proxies to it.`,
    )
    .setVersion('0.1.0')
    .addApiKey(
      {
        type: 'apiKey',
        name: 'X-API-Key',
        in: 'header',
        description: 'Device API key (from device registration) or admin key',
      },
      'api-key',
    )
    .addTag('Pipeline', 'Full voice pipeline — the main endpoints devices call. Audio in → audio out.')
    .addTag('Ask', 'Text and vision queries to the LLM (OpenClaw). No audio processing.')
    .addTag('Transcribe', 'Speech-to-text via Python sidecar (faster-whisper).')
    .addTag('TTS', 'Text-to-speech via Python sidecar (espeak-ng / Piper TTS).')
    .addTag('Conversation', 'Conversation history per device. Server tracks context for follow-ups.')
    .addTag('Devices', 'Device registry. Register new devices, update prompts, list all devices.')
    .addTag('Health', 'Health check — no auth required.')
    .build();

  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('docs', app, document, {
    customSiteTitle: '🤖 CHARLI Server — API Docs',
    customfavIcon: undefined,
    swaggerOptions: {
      persistAuthorization: true,
      docExpansion: 'list',
      filter: true,
      tagsSorter: 'alpha',
    },
  });

  const port = process.env.CHARLI_SERVER_PORT || 3000;
  await app.listen(port);
  console.log(`\n🤖 CHARLI Server running on http://localhost:${port}`);
  console.log(`   Health:  http://localhost:${port}/health`);
  console.log(`   API:     http://localhost:${port}/api/*`);
  console.log(`   Swagger: http://localhost:${port}/docs\n`);
}

bootstrap();
