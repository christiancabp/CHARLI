import { Injectable, Logger } from '@nestjs/common';
import { Device } from '@prisma/generated';
import {
  DEFAULT_PROMPTS,
  VISION_PROMPT,
  VISION_KEYWORDS,
} from './prompts/system-prompts';

interface ChatMessage {
  role: string;
  content: string | Array<{ type: string; text?: string; image_url?: { url: string } }>;
}

/**
 * AskService — sends questions to the OpenClaw LLM gateway.
 *
 * Ported from charli_glasses/api/src/ask_charli_vision.py.
 * Uses the OpenAI-compatible chat completions API.
 */
@Injectable()
export class AskService {
  private readonly logger = new Logger(AskService.name);
  private readonly openclawUrl: string;
  private readonly openclawToken: string;

  constructor() {
    this.openclawUrl = process.env.OPENCLAW_URL || 'http://localhost:18789';
    this.openclawToken = process.env.OPENCLAW_TOKEN || '';
  }

  /**
   * Check if a question is asking about something visual.
   */
  isVisionQuery(question: string): boolean {
    const q = question.toLowerCase();
    return VISION_KEYWORDS.some((kw) => q.includes(kw));
  }

  /**
   * Get the language display name for prompt interpolation.
   */
  private langName(language: string): string {
    const map: Record<string, string> = { en: 'English', es: 'Spanish' };
    return map[language] || 'English';
  }

  /**
   * Build the system prompt for a device + query type.
   */
  private getSystemPrompt(device: Device | null, language: string, isVision: boolean): string {
    let template: string;

    if (isVision) {
      template = VISION_PROMPT;
    } else if (device?.systemPrompt) {
      template = device.systemPrompt;
    } else {
      const type = device?.type || 'default';
      template = DEFAULT_PROMPTS[type] || DEFAULT_PROMPTS.default;
    }

    return template.replace(/{lang_name}/g, this.langName(language));
  }

  /**
   * Send a question (with optional image) to OpenClaw and return the response.
   */
  async ask(params: {
    question: string;
    language: string;
    history?: Array<{ role: string; content: string }>;
    device: Device | null;
    imageBase64?: string;
    imageMime?: string;
  }): Promise<string> {
    const { question, language, history, device, imageBase64, imageMime } = params;

    const hasImage = !!imageBase64;
    const isVision = hasImage && this.isVisionQuery(question);
    const maxTokens = isVision ? 250 : (device?.maxTokens || 150);

    const systemPrompt = this.getSystemPrompt(device, language, isVision);

    // Build messages array
    const messages: ChatMessage[] = [{ role: 'system', content: systemPrompt }];

    // Add conversation history (last N turns)
    if (history?.length) {
      const maxTurns = 3;
      const recent = history.slice(-(maxTurns * 2));
      for (const entry of recent) {
        messages.push({ role: entry.role, content: entry.content });
      }
    }

    // Build user message (with or without image)
    if (hasImage) {
      messages.push({
        role: 'user',
        content: [
          { type: 'text', text: question },
          {
            type: 'image_url',
            image_url: {
              url: `data:${imageMime || 'image/jpeg'};base64,${imageBase64}`,
            },
          },
        ],
      });
    } else {
      messages.push({ role: 'user', content: question });
    }

    // Call OpenClaw via OpenAI-compatible API
    const deviceName = device?.name || 'unknown';
    this.logger.log(`Asking OpenClaw (device: ${deviceName}, vision: ${isVision})`);

    try {
      const response = await fetch(`${this.openclawUrl}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.openclawToken}`,
        },
        body: JSON.stringify({
          model: 'openclaw:main',
          messages,
          max_tokens: maxTokens,
          user: deviceName,
        }),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`OpenClaw ${response.status}: ${text}`);
      }

      const data = await response.json();
      const answer = data.choices?.[0]?.message?.content || '';
      this.logger.log(`Response: "${answer.substring(0, 80)}..."`);
      return answer;
    } catch (error) {
      this.logger.error(`OpenClaw error: ${error.message}`);
      return "I'm sorry, I'm having trouble connecting to my brain right now.";
    }
  }
}
