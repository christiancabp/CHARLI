import { Injectable, Logger } from '@nestjs/common';

/**
 * TtsService — proxies text to the Python sidecar for speech synthesis.
 *
 * The sidecar runs espeak-ng (or Piper TTS) and returns a WAV buffer.
 */
@Injectable()
export class TtsService {
  private readonly logger = new Logger(TtsService.name);
  private readonly sidecarUrl: string;

  constructor() {
    this.sidecarUrl = process.env.SIDECAR_URL || 'http://localhost:3001';
  }

  /**
   * Synthesize text to speech, returning a WAV audio buffer.
   */
  async synthesize(text: string, language: string = 'en'): Promise<Buffer> {
    this.logger.log(`TTS: "${text.substring(0, 60)}..." (${language})`);

    try {
      const response = await fetch(`${this.sidecarUrl}/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, language }),
      });

      if (!response.ok) {
        throw new Error(`Sidecar ${response.status}: ${await response.text()}`);
      }

      const arrayBuffer = await response.arrayBuffer();
      this.logger.log(`TTS complete: ${arrayBuffer.byteLength} bytes`);
      return Buffer.from(arrayBuffer);
    } catch (error) {
      this.logger.error(`TTS error: ${error.message}`);
      return Buffer.alloc(0);
    }
  }
}
