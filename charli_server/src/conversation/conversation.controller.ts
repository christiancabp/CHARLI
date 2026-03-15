import { Controller, Get, Delete, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiSecurity } from '@nestjs/swagger';
import { ConversationService } from './conversation.service';
import { AuthGuard } from '../auth/auth.guard';
import { CurrentDevice } from '../common/decorators/current-device.decorator';
import { Device } from '@prisma/generated';

@ApiTags('Conversation')
@ApiSecurity('api-key')
@Controller('api/conversation')
@UseGuards(AuthGuard)
export class ConversationController {
  constructor(private conversationService: ConversationService) {}

  @Get()
  @ApiOperation({
    summary: 'Get active conversation',
    description:
      'Returns the active conversation for the calling device, including all messages. ' +
      'Each device has one active conversation that accumulates context for follow-up questions.',
  })
  @ApiResponse({ status: 200, description: 'Active conversation with messages' })
  @ApiResponse({ status: 401, description: 'Invalid or missing API key' })
  async getConversation(@CurrentDevice() device: Device) {
    return this.conversationService.getActiveConversation(device.id);
  }

  @Delete()
  @ApiOperation({
    summary: 'Clear active conversation',
    description:
      'Deletes all messages in the active conversation for the calling device. ' +
      'Use this to reset context (e.g., "start over" or "new topic"). ' +
      'A new conversation will be created automatically on the next question.',
  })
  @ApiResponse({ status: 200, description: 'Conversation cleared' })
  @ApiResponse({ status: 401, description: 'Invalid or missing API key' })
  async clearConversation(@CurrentDevice() device: Device) {
    return this.conversationService.clearConversation(device.id);
  }
}
