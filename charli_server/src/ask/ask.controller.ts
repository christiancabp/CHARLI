import { Controller, Post, Body, UseGuards } from '@nestjs/common';
import { AskService } from './ask.service';
import { AskDto, AskVisionDto } from './dto/ask.dto';
import { AuthGuard } from '../auth/auth.guard';
import { CurrentDevice } from '../common/decorators/current-device.decorator';
import { ConversationService } from '../conversation/conversation.service';
import { Device } from '@prisma/client';

@Controller('api/ask')
@UseGuards(AuthGuard)
export class AskController {
  constructor(
    private askService: AskService,
    private conversationService: ConversationService,
  ) {}

  @Post()
  async ask(@Body() dto: AskDto, @CurrentDevice() device: Device) {
    // Get conversation history
    const history = await this.conversationService.getHistory(device.id);

    // Save user message
    const conversation = await this.conversationService.addMessage(
      device.id,
      'user',
      dto.question,
    );

    // Ask OpenClaw
    const answer = await this.askService.ask({
      question: dto.question,
      language: dto.language || 'en',
      history,
      device,
    });

    // Save assistant response
    await this.conversationService.addMessage(device.id, 'assistant', answer);

    return {
      question: dto.question,
      answer,
      conversationId: conversation.conversationId,
    };
  }

  @Post('vision')
  async askVision(@Body() dto: AskVisionDto, @CurrentDevice() device: Device) {
    const answer = await this.askService.ask({
      question: dto.question,
      language: dto.language || 'en',
      device,
      imageBase64: dto.imageBase64,
      imageMime: dto.imageMime,
    });

    // Save both messages
    await this.conversationService.addMessage(device.id, 'user', dto.question);
    await this.conversationService.addMessage(device.id, 'assistant', answer);

    return {
      question: dto.question,
      answer,
      vision: true,
    };
  }
}
