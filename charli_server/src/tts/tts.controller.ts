import { Controller, Post, Body, Res, UseGuards } from '@nestjs/common';
import { Response } from 'express';
import { TtsService } from './tts.service';
import { AuthGuard } from '../auth/auth.guard';

@Controller('api/tts')
@UseGuards(AuthGuard)
export class TtsController {
  constructor(private ttsService: TtsService) {}

  @Post()
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
