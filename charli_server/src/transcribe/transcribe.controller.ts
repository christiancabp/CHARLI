import {
  Controller,
  Post,
  UseGuards,
  UseInterceptors,
  UploadedFile,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { ApiTags, ApiOperation, ApiResponse, ApiSecurity, ApiConsumes, ApiBody } from '@nestjs/swagger';
import { TranscribeService } from './transcribe.service';
import { AuthGuard } from '../auth/auth.guard';

@ApiTags('Transcribe')
@ApiSecurity('api-key')
@Controller('api/transcribe')
@UseGuards(AuthGuard)
export class TranscribeController {
  constructor(private transcribeService: TranscribeService) {}

  @Post()
  @ApiOperation({
    summary: 'Transcribe audio to text',
    description:
      'Sends an audio file to the Python sidecar (faster-whisper) for speech-to-text. ' +
      'Accepts WAV, M4A, or WebM audio files. Language is auto-detected. ' +
      'Use this standalone endpoint when you only need transcription without the full pipeline.',
  })
  @ApiConsumes('multipart/form-data')
  @ApiBody({
    description: 'Audio file to transcribe',
    schema: {
      type: 'object',
      properties: {
        audio: { type: 'string', format: 'binary', description: 'Audio file (WAV, M4A, or WebM)' },
      },
      required: ['audio'],
    },
  })
  @ApiResponse({
    status: 200,
    description: 'Transcription result',
    schema: {
      type: 'object',
      properties: {
        text: { type: 'string', example: "What's the weather like today?" },
        language: { type: 'string', example: 'en' },
      },
    },
  })
  @ApiResponse({ status: 401, description: 'Invalid or missing API key' })
  @UseInterceptors(FileInterceptor('audio'))
  async transcribe(@UploadedFile() file: Express.Multer.File) {
    return this.transcribeService.transcribeBuffer(
      file.buffer,
      file.originalname,
    );
  }
}
