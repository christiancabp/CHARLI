import { Controller, Get, Delete, UseGuards } from '@nestjs/common';
import { ConversationService } from './conversation.service';
import { AuthGuard } from '../auth/auth.guard';
import { CurrentDevice } from '../common/decorators/current-device.decorator';
import { Device } from '@prisma/client';

@Controller('api/conversation')
@UseGuards(AuthGuard)
export class ConversationController {
  constructor(private conversationService: ConversationService) {}

  @Get()
  async getConversation(@CurrentDevice() device: Device) {
    return this.conversationService.getActiveConversation(device.id);
  }

  @Delete()
  async clearConversation(@CurrentDevice() device: Device) {
    return this.conversationService.clearConversation(device.id);
  }
}
