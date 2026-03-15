/**
 * WebSocket event types for real-time communication.
 *
 * Server → Client:
 *   snapshot       — Full state sent on connect
 *   device:state   — Device state change (idle/listening/thinking/speaking)
 *   device:message — New conversation message from any device
 *   command:speak  — Tell a device to speak
 *
 * Client → Server:
 *   state          — Device reporting its state
 *   heartbeat      — Keep-alive
 *   metrics        — System metrics (CPU, RAM)
 */

export type DeviceState = 'idle' | 'listening' | 'thinking' | 'speaking';

export interface SnapshotEvent {
  deviceId: string;
  state: DeviceState;
  conversation: Array<{ role: string; content: string; createdAt: string }>;
}

export interface DeviceStateEvent {
  deviceId: string;
  state: DeviceState;
}

export interface DeviceMessageEvent {
  deviceId: string;
  role: string;
  content: string;
}

export interface CommandSpeakEvent {
  text: string;
  language?: string;
  audioUrl?: string;
}
