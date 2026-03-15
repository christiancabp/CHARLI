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
import { PipelineService } from './pipeline.service';
import { AuthGuard } from '../auth/auth.guard';
import { CurrentDevice } from '../common/decorators/current-device.decorator';
import { Device } from '@prisma/client';

@Controller('api/pipeline')
@UseGuards(AuthGuard)
export class PipelineController {
  constructor(private pipelineService: PipelineService) {}

  /**
   * POST /api/pipeline/voice
   * Full voice pipeline: audio file in → WAV audio response out.
   * Accepts optional image file for vision queries.
   */
  @Post('voice')
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

    // Extract image if provided (convert to base64)
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

  /**
   * POST /api/pipeline/voice-text
   * Same as voice, but returns JSON instead of audio.
   */
  @Post('voice-text')
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
