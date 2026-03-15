import { Injectable, Logger } from '@nestjs/common';
import { Device } from '@prisma/generated';
import { TranscribeService } from '../transcribe/transcribe.service';
import { AskService } from '../ask/ask.service';
import { TtsService } from '../tts/tts.service';
import { ConversationService } from '../conversation/conversation.service';
import { EventsGateway } from '../events/events.gateway';

/**
 * PipelineService — orchestrates the full voice pipeline.
 *
 * Flow: audio → transcribe → ask → tts → audio
 *
 * This replaces the sequential pipeline that used to run locally on each device.
 * Now it runs centrally on the Mac Mini with ~1-3ms overhead between steps.
 */
@Injectable()
export class PipelineService {
  private readonly logger = new Logger(PipelineService.name);

  constructor(
    private transcribeService: TranscribeService,
    private askService: AskService,
    private ttsService: TtsService,
    private conversationService: ConversationService,
    private eventsGateway: EventsGateway,
  ) {}

  /**
   * Full voice pipeline: audio in → audio out.
   * Returns the WAV audio buffer of CHARLI's spoken response.
   */
  async voiceQuery(
    audioBuffer: Buffer,
    filename: string,
    device: Device,
    imageBase64?: string,
    imageMime?: string,
  ): Promise<{ audio: Buffer; transcription: string; language: string; answer: string }> {
    const deviceName = device.name;

    // Step 1: Transcribe audio → text
    this.eventsGateway.broadcastDeviceState(device.id, 'listening');
    const { text, language } = await this.transcribeService.transcribeBuffer(
      audioBuffer,
      filename,
    );

    if (!text) {
      this.logger.warn(`No speech detected from ${deviceName}`);
      this.eventsGateway.broadcastDeviceState(device.id, 'idle');
      return { audio: Buffer.alloc(0), transcription: '', language: 'en', answer: '' };
    }

    this.logger.log(`[${deviceName}] "${text}" (${language})`);

    // Step 2: Save user message + get history
    this.eventsGateway.broadcastDeviceState(device.id, 'thinking');
    await this.conversationService.addMessage(device.id, 'user', text);
    this.eventsGateway.broadcastMessage(device.id, 'user', text);

    const history = await this.conversationService.getHistory(device.id);

    // Step 3: Ask OpenClaw
    const answer = await this.askService.ask({
      question: text,
      language,
      history,
      device,
      imageBase64,
      imageMime,
    });

    // Step 4: Save assistant response
    await this.conversationService.addMessage(device.id, 'assistant', answer);
    this.eventsGateway.broadcastMessage(device.id, 'assistant', answer);

    // Step 5: Generate speech
    this.eventsGateway.broadcastDeviceState(device.id, 'speaking');
    const audio = await this.ttsService.synthesize(answer, language);

    this.eventsGateway.broadcastDeviceState(device.id, 'idle');
    return { audio, transcription: text, language, answer };
  }
}
