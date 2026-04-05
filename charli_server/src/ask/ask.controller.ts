import { Controller, Post, Body, UseGuards, UnauthorizedException } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiSecurity } from '@nestjs/swagger';
import { AskService } from './ask.service';
import { AskDto, AskVisionDto } from './dto/ask.dto';
import { AuthGuard } from '../auth/auth.guard';
import { CurrentDevice } from '../common/decorators/current-device.decorator';
import { ConversationService } from '../conversation/conversation.service';
import { Device } from '@prisma/generated';

@ApiTags('Ask')
@ApiSecurity('api-key')
@Controller('api/ask')
@UseGuards(AuthGuard)
export class AskController {
  constructor(
    private askService: AskService,
    private conversationService: ConversationService,
  ) {}

  @Post()
  @ApiOperation({
    summary: 'Ask CHARLI a text question',
    description:
      'Sends a text question to the LLM (OpenClaw) and returns the answer. ' +
      'Conversation history is tracked per device for context-aware follow-ups. ' +
      'Use this when you already have text (e.g., typed input or pre-transcribed audio).',
  })
  @ApiResponse({ status: 200, description: 'Question answered successfully' })
  @ApiResponse({ status: 401, description: 'Invalid or missing API key' })
  async ask(@Body() dto: AskDto, @CurrentDevice() device: Device) {
    if (!device) {
      throw new UnauthorizedException(
        'Admin key cannot be used with /api/ask — use a device API key',
      );
    }
    // CLI devices get more conversation context (10 turns vs 3 for voice)
    const maxTurns = device.type === 'cli' ? 10 : 3;
    const history = await this.conversationService.getHistory(device.id, maxTurns);

    const conversation = await this.conversationService.addMessage(
      device.id,
      'user',
      dto.question,
    );

    const answer = await this.askService.ask({
      question: dto.question,
      language: dto.language || 'en',
      history,
      device,
    });

    await this.conversationService.addMessage(device.id, 'assistant', answer);

    return {
      question: dto.question,
      answer,
      conversationId: conversation.conversationId,
    };
  }

  @Post('vision')
  @ApiOperation({
    summary: 'Ask CHARLI about an image',
    description:
      'Sends a text question with a base64-encoded image to the LLM. ' +
      'CHARLI can identify objects, read text, describe scenes, and more. ' +
      'If the question contains vision keywords ("what am I looking at", "read this", etc.), ' +
      'a specialized vision prompt is used for better results.',
  })
  @ApiResponse({ status: 200, description: 'Vision query answered successfully' })
  @ApiResponse({ status: 401, description: 'Invalid or missing API key' })
  async askVision(@Body() dto: AskVisionDto, @CurrentDevice() device: Device) {
    if (!device) {
      throw new UnauthorizedException(
        'Admin key cannot be used with /api/ask — use a device API key',
      );
    }
    const answer = await this.askService.ask({
      question: dto.question,
      language: dto.language || 'en',
      device,
      imageBase64: dto.imageBase64,
      imageMime: dto.imageMime,
    });

    await this.conversationService.addMessage(device.id, 'user', dto.question);
    await this.conversationService.addMessage(device.id, 'assistant', answer);

    return {
      question: dto.question,
      answer,
      vision: true,
    };
  }
}
