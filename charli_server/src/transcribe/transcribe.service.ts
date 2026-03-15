import { Injectable, Logger } from '@nestjs/common';
import * as fs from 'fs';

/**
 * TranscribeService — proxies audio to the Python sidecar for STT.
 *
 * The sidecar runs faster-whisper and stays hot (model loaded once).
 * We send the audio file over HTTP and get back { text, language }.
 */
@Injectable()
export class TranscribeService {
  private readonly logger = new Logger(TranscribeService.name);
  private readonly sidecarUrl: string;

  constructor() {
    this.sidecarUrl = process.env.SIDECAR_URL || 'http://localhost:3001';
  }

  async transcribe(audioPath: string): Promise<{ text: string; language: string }> {
    this.logger.log(`Transcribing: ${audioPath}`);

    const audioBuffer = fs.readFileSync(audioPath);
    const formData = new FormData();
    formData.append('audio', new Blob([audioBuffer]), 'audio.wav');

    try {
      const response = await fetch(`${this.sidecarUrl}/transcribe`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Sidecar ${response.status}: ${await response.text()}`);
      }

      const result = await response.json();
      this.logger.log(`Transcribed: "${result.text}" (${result.language})`);
      return { text: result.text, language: result.language };
    } catch (error) {
      this.logger.error(`Transcription error: ${error.message}`);
      return { text: '', language: 'en' };
    }
  }

  /**
   * Transcribe from a Buffer directly (for multipart uploads).
   */
  async transcribeBuffer(buffer: Buffer, filename: string): Promise<{ text: string; language: string }> {
    this.logger.log(`Transcribing buffer: ${filename} (${buffer.length} bytes)`);

    const formData = new FormData();
    formData.append('audio', new Blob([new Uint8Array(buffer)]), filename);

    try {
      const response = await fetch(`${this.sidecarUrl}/transcribe`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Sidecar ${response.status}: ${await response.text()}`);
      }

      const result = await response.json();
      this.logger.log(`Transcribed: "${result.text}" (${result.language})`);
      return { text: result.text, language: result.language };
    } catch (error) {
      this.logger.error(`Transcription error: ${error.message}`);
      return { text: '', language: 'en' };
    }
  }
}
