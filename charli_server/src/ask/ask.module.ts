import { Module } from '@nestjs/common';
import { AskService } from './ask.service';
import { AskController } from './ask.controller';
import { AuthModule } from '../auth/auth.module';
import { ConversationModule } from '../conversation/conversation.module';

@Module({
  imports: [AuthModule, ConversationModule],
  controllers: [AskController],
  providers: [AskService],
  exports: [AskService],
})
export class AskModule {}
