import { Module } from '@nestjs/common';
import { PrismaModule } from './prisma/prisma.module';
import { AuthModule } from './auth/auth.module';
import { HealthModule } from './health/health.module';
import { DeviceModule } from './device/device.module';
import { AskModule } from './ask/ask.module';
import { TranscribeModule } from './transcribe/transcribe.module';
import { TtsModule } from './tts/tts.module';
import { ConversationModule } from './conversation/conversation.module';
import { PipelineModule } from './pipeline/pipeline.module';
import { EventsModule } from './events/events.module';

@Module({
  imports: [
    // Infrastructure
    PrismaModule,
    AuthModule,
    EventsModule,

    // Features
    HealthModule,
    DeviceModule,
    ConversationModule,
    AskModule,
    TranscribeModule,
    TtsModule,
    PipelineModule,
  ],
})
export class AppModule {}
