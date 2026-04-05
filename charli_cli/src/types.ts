/**
 * Shared types for the CHARLI CLI.
 *
 * These interfaces match the CHARLI Server API responses
 * and the local config file format.
 */

/** ~/.charli/config.json */
export interface CharliConfig {
  serverUrl: string;
  apiKey: string;
  deviceName: string;
}

/** Response from POST /api/ask */
export interface AskResponse {
  question: string;
  answer: string;
  conversationId: string;
}

/** Response from GET /health */
export interface HealthResponse {
  status: string;
  timestamp?: string;
  [key: string]: unknown;
}

/** Response from POST /api/devices */
export interface DeviceResponse {
  id: string;
  name: string;
  type: string;
  apiKey?: string;
}

/** Tailscale status info */
export interface TailscaleStatus {
  connected: boolean;
  hostname?: string;
  tailscaleIp?: string;
  peers?: TailscalePeer[];
}

export interface TailscalePeer {
  hostname: string;
  tailscaleIp: string;
  online: boolean;
}
