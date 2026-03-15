import {
  Controller,
  Post,
  Res,
  UseGuards,
  UseInterceptors,
  UploadedFiles,
} from '@nestjs/common';
import { FileFieldsInterceptor } from '@nestjs/platform-express';
import { Response } from 'express';
import { ApiTags, ApiOperation, ApiResponse, ApiSecurity, ApiConsumes, ApiBody } from '@nestjs/swagger';
import { PipelineService } from './pipeline.service';
import { AuthGuard } from '../auth/auth.guard';
import { CurrentDevice } from '../common/decorators/current-device.decorator';
import { Device } from '@prisma/client';

@ApiTags('Pipeline')
@ApiSecurity('api-key')
@Controller('api/pipeline')
@UseGuards(AuthGuard)
export class PipelineController {
  constructor(private pipelineService: PipelineService) {}

  @Post('voice')
  @ApiOperation({
    summary: 'Full voice pipeline — audio in, audio out',
    description:
      'THE main endpoint for devices. Send a recorded audio file and get back a WAV audio response. ' +
      'The server handles everything: transcription (STT) → LLM query → speech synthesis (TTS). ' +
      'Optionally include an image for vision queries (e.g., "what am I looking at?").\n\n' +
      '**Response headers** include metadata:\n' +
      '- `X-Transcription` — What the user said (URL-encoded)\n' +
      '- `X-Language` — Detected language code\n' +
      '- `X-Answer` — CHARLI\'s text response (URL-encoded)\n\n' +
      'If no speech is detected in the audio, returns JSON `{ transcription: "", answer: "" }` instead.',
  })
  @ApiConsumes('multipart/form-data')
  @ApiBody({
    description: 'Audio file (required) and optional image for vision queries',
    schema: {
      type: 'object',
      properties: {
        audio: { type: 'string', format: 'binary', description: 'Audio recording (WAV, M4A, WebM)' },
        image: { type: 'string', format: 'binary', description: 'Optional camera image (JPEG, PNG) for vision queries' },
      },
      required: ['audio'],
    },
  })
  @ApiResponse({ status: 200, description: 'WAV audio response (or JSON if no speech detected)' })
  @ApiResponse({ status: 400, description: 'Missing audio file' })
  @ApiResponse({ status: 401, description: 'Invalid or missing API key' })
  @UseInterceptors(
    FileFieldsInterceptor([
      { name: 'audio', maxCount: 1 },
      { name: 'image', maxCount: 1 },
    ]),
  )
  async voiceToAudio(
    @UploadedFiles()
    files: { audio?: Express.Multer.File[]; image?: Express.Multer.File[] },
    @CurrentDevice() device: Device,
    @Res() res: Response,
  ) {
    const audioFile = files.audio?.[0];
    if (!audioFile) {
      res.status(400).json({ error: 'Missing audio file' });
      return;
    }

    let imageBase64: string | undefined;
    let imageMime: string | undefined;
    if (files.image?.[0]) {
      imageBase64 = files.image[0].buffer.toString('base64');
      imageMime = files.image[0].mimetype;
    }

    const result = await this.pipelineService.voiceQuery(
      audioFile.buffer,
      audioFile.originalname,
      device,
      imageBase64,
      imageMime,
    );

    if (result.audio.length === 0) {
      res.status(200).json({ transcription: '', answer: '', language: 'en' });
      return;
    }

    res.set({
      'Content-Type': 'audio/wav',
      'Content-Length': result.audio.length.toString(),
      'X-Transcription': encodeURIComponent(result.transcription),
      'X-Language': result.language,
      'X-Answer': encodeURIComponent(result.answer),
    });
    res.send(result.audio);
  }

  @Post('voice-text')
  @ApiOperation({
    summary: 'Full voice pipeline — audio in, text out',
    description:
      'Same pipeline as `/api/pipeline/voice` but returns JSON instead of audio. ' +
      'Useful for debugging, or when the device handles TTS locally.',
  })
  @ApiConsumes('multipart/form-data')
  @ApiBody({
    description: 'Audio file (required) and optional image for vision queries',
    schema: {
      type: 'object',
      properties: {
        audio: { type: 'string', format: 'binary', description: 'Audio recording (WAV, M4A, WebM)' },
        image: { type: 'string', format: 'binary', description: 'Optional camera image (JPEG, PNG)' },
      },
      required: ['audio'],
    },
  })
  @ApiResponse({
    status: 200,
    description: 'Transcription and answer as JSON',
    schema: {
      type: 'object',
      properties: {
        transcription: { type: 'string', example: "What's the weather?" },
        language: { type: 'string', example: 'en' },
        answer: { type: 'string', example: "It's sunny and 72 degrees today." },
      },
    },
  })
  @ApiResponse({ status: 401, description: 'Invalid or missing API key' })
  @UseInterceptors(
    FileFieldsInterceptor([
      { name: 'audio', maxCount: 1 },
      { name: 'image', maxCount: 1 },
    ]),
  )
  async voiceToText(
    @UploadedFiles()
    files: { audio?: Express.Multer.File[]; image?: Express.Multer.File[] },
    @CurrentDevice() device: Device,
  ) {
    const audioFile = files.audio?.[0];
    if (!audioFile) {
      return { error: 'Missing audio file' };
    }

    let imageBase64: string | undefined;
    let imageMime: string | undefined;
    if (files.image?.[0]) {
      imageBase64 = files.image[0].buffer.toString('base64');
      imageMime = files.image[0].mimetype;
    }

    const result = await this.pipelineService.voiceQuery(
      audioFile.buffer,
      audioFile.originalname,
      device,
      imageBase64,
      imageMime,
    );

    return {
      transcription: result.transcription,
      language: result.language,
      answer: result.answer,
    };
  }
}
