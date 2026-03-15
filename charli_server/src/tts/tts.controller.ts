import { Controller, Post, Body, Res, UseGuards } from '@nestjs/common';
import { Response } from 'express';
import { ApiTags, ApiOperation, ApiResponse, ApiSecurity, ApiBody } from '@nestjs/swagger';
import { TtsService } from './tts.service';
import { AuthGuard } from '../auth/auth.guard';

@ApiTags('TTS')
@ApiSecurity('api-key')
@Controller('api/tts')
@UseGuards(AuthGuard)
export class TtsController {
  constructor(private ttsService: TtsService) {}

  @Post()
  @ApiOperation({
    summary: 'Convert text to speech audio',
    description:
      'Sends text to the Python sidecar for speech synthesis. Returns a WAV audio file. ' +
      'Uses espeak-ng by default (robotic but instant). Upgradeable to Piper TTS (natural voice). ' +
      'Use this standalone endpoint when you have text and need audio without the full pipeline.',
  })
  @ApiBody({
    description: 'Text to convert to speech',
    schema: {
      type: 'object',
      properties: {
        text: { type: 'string', example: "It's sunny and 72 degrees today.", description: 'Text to speak' },
        language: { type: 'string', example: 'en', description: 'Language code (en, es)', default: 'en' },
      },
      required: ['text'],
    },
  })
  @ApiResponse({ status: 200, description: 'WAV audio file' })
  @ApiResponse({ status: 401, description: 'Invalid or missing API key' })
  @ApiResponse({ status: 500, description: 'TTS synthesis failed' })
  async synthesize(
    @Body() body: { text: string; language?: string },
    @Res() res: Response,
  ) {
    const wavBuffer = await this.ttsService.synthesize(
      body.text,
      body.language || 'en',
    );

    if (wavBuffer.length === 0) {
      res.status(500).json({ error: 'TTS synthesis failed' });
      return;
    }

    res.set({
      'Content-Type': 'audio/wav',
      'Content-Length': wavBuffer.length.toString(),
    });
    res.send(wavBuffer);
  }
}
