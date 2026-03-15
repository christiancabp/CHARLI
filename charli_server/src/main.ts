/**
 * CHARLI Server — Bootstrap
 *
 * Central backend for all CHARLI devices (desk hub, glasses, future devices).
 * Runs on the Mac Mini alongside OpenClaw and the Python ML sidecar.
 */

import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
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

  const port = process.env.CHARLI_SERVER_PORT || 3000;
  await app.listen(port);
  console.log(`\n🤖 CHARLI Server running on http://localhost:${port}`);
  console.log(`   Health: http://localhost:${port}/health`);
  console.log(`   API:    http://localhost:${port}/api/*\n`);
}

bootstrap();
