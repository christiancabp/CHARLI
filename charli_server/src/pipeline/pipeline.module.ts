import { Module } from '@nestjs/common';
import { PipelineService } from './pipeline.service';
import { PipelineController } from './pipeline.controller';
import { AuthModule } from '../auth/auth.module';
import { TranscribeModule } from '../transcribe/transcribe.module';
import { AskModule } from '../ask/ask.module';
import { TtsModule } from '../tts/tts.module';
import { ConversationModule } from '../conversation/conversation.module';
import { EventsModule } from '../events/events.module';

@Module({
  imports: [
    AuthModule,
    TranscribeModule,
    AskModule,
    TtsModule,
    ConversationModule,
    EventsModule,
  ],
  controllers: [PipelineController],
  providers: [PipelineService],
})
export class PipelineModule {}
