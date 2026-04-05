/**
 * API Client — HTTP wrapper for the CHARLI Server.
 *
 * Uses Node 18+ native fetch (no axios needed).
 * Mirrors the pattern from charli_home/src/charli_server_client.py
 * and charli_glasses/ios/CHARLIAPIClient.swift.
 *
 * All requests include the X-API-Key header for device auth.
 */

import type { CharliConfig, AskResponse, HealthResponse, DeviceResponse } from '../types.js';

export class ApiClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(config: CharliConfig) {
    // Strip trailing slash
    this.baseUrl = config.serverUrl.replace(/\/+$/, '');
    this.apiKey = config.apiKey;
  }

  /**
   * GET /health — no auth required.
   */
  async health(): Promise<HealthResponse> {
    const res = await fetch(`${this.baseUrl}/health`);
    if (!res.ok) throw new Error(`Server returned ${res.status}`);
    return res.json() as Promise<HealthResponse>;
  }

  /**
   * POST /api/ask — send a text question, get an answer.
   */
  async ask(question: string, language = 'en'): Promise<AskResponse> {
    const res = await fetch(`${this.baseUrl}/api/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey,
      },
      body: JSON.stringify({ question, language }),
    });

    if (res.status === 401) {
      throw new Error('Invalid API key — run `charli init` to reconfigure');
    }
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Server error ${res.status}: ${text}`);
    }

    return res.json() as Promise<AskResponse>;
  }

  /**
   * POST /api/devices — register a new device (requires admin key).
   */
  async registerDevice(
    name: string,
    type: string,
    adminKey: string,
  ): Promise<DeviceResponse> {
    const res = await fetch(`${this.baseUrl}/api/devices`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': adminKey,
      },
      body: JSON.stringify({ name, type }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Registration failed ${res.status}: ${text}`);
    }

    return res.json() as Promise<DeviceResponse>;
  }
}
