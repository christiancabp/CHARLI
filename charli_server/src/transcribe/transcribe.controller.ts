import {
  Controller,
  Post,
  UseGuards,
  UseInterceptors,
  UploadedFile,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { TranscribeService } from './transcribe.service';
import { AuthGuard } from '../auth/auth.guard';

@Controller('api/transcribe')
@UseGuards(AuthGuard)
export class TranscribeController {
  constructor(private transcribeService: TranscribeService) {}

  @Post()
  @UseInterceptors(FileInterceptor('audio'))
  async transcribe(@UploadedFile() file: Express.Multer.File) {
    return this.transcribeService.transcribeBuffer(
      file.buffer,
      file.originalname,
    );
  }
}
