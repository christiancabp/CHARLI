import { Module } from '@nestjs/common';
import { TranscribeService } from './transcribe.service';
import { TranscribeController } from './transcribe.controller';
import { AuthModule } from '../auth/auth.module';

@Module({
  imports: [AuthModule],
  controllers: [TranscribeController],
  providers: [TranscribeService],
  exports: [TranscribeService],
})
export class TranscribeModule {}
