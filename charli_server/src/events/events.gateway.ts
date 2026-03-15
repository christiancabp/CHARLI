import {
  WebSocketGateway,
  WebSocketServer,
  OnGatewayConnection,
  OnGatewayDisconnect,
  SubscribeMessage,
} from '@nestjs/websockets';
import { Logger } from '@nestjs/common';
import { Server, Socket } from 'socket.io';
import { PrismaService } from '../prisma/prisma.service';
import {
  DeviceState,
  DeviceStateEvent,
  DeviceMessageEvent,
} from './events.types';

/**
 * WebSocket gateway for real-time events.
 *
 * Devices connect with: ws://server:3000/events?apiKey=<key>
 * On connect, they receive a snapshot of their conversation.
 * State changes and messages are broadcast to all connected clients.
 */
@WebSocketGateway({
  namespace: '/events',
  cors: { origin: '*' },
})
export class EventsGateway
  implements OnGatewayConnection, OnGatewayDisconnect
{
  @WebSocketServer()
  server: Server;

  private readonly logger = new Logger(EventsGateway.name);

  // Track connected devices: socketId → deviceId
  private connectedDevices = new Map<string, string>();

  // Track device states in memory
  private deviceStates = new Map<string, DeviceState>();

  constructor(private prisma: PrismaService) {}

  async handleConnection(client: Socket) {
    const apiKey =
      (client.handshake.query.apiKey as string) ||
      (client.handshake.auth?.apiKey as string);

    if (!apiKey) {
      this.logger.warn(`WS rejected: no API key`);
      client.disconnect();
      return;
    }

    // Validate API key
    const device = await this.prisma.device.findUnique({
      where: { apiKey },
    });

    if (!device) {
      this.logger.warn(`WS rejected: invalid API key`);
      client.disconnect();
      return;
    }

    this.connectedDevices.set(client.id, device.id);
    this.logger.log(`WS connected: ${device.name} (${client.id})`);

    // Send snapshot on connect
    const conversation = await this.prisma.conversation.findFirst({
      where: { deviceId: device.id },
      orderBy: { updatedAt: 'desc' },
      include: {
        messages: {
          orderBy: { createdAt: 'asc' },
          select: { role: true, content: true, createdAt: true },
        },
      },
    });

    client.emit('snapshot', {
      deviceId: device.id,
      state: this.deviceStates.get(device.id) || 'idle',
      conversation: conversation?.messages || [],
    });
  }

  handleDisconnect(client: Socket) {
    const deviceId = this.connectedDevices.get(client.id);
    this.connectedDevices.delete(client.id);
    if (deviceId) {
      this.logger.log(`WS disconnected: ${deviceId}`);
    }
  }

  @SubscribeMessage('state')
  handleState(client: Socket, payload: { state: DeviceState }) {
    const deviceId = this.connectedDevices.get(client.id);
    if (deviceId) {
      this.deviceStates.set(deviceId, payload.state);
      this.server.emit('device:state', { deviceId, state: payload.state });
    }
  }

  @SubscribeMessage('heartbeat')
  handleHeartbeat(client: Socket) {
    client.emit('heartbeat', { timestamp: Date.now() });
  }

  @SubscribeMessage('metrics')
  handleMetrics(client: Socket, payload: any) {
    const deviceId = this.connectedDevices.get(client.id);
    if (deviceId) {
      this.logger.debug(`Metrics from ${deviceId}: ${JSON.stringify(payload)}`);
    }
  }

  // ── Broadcast helpers (called by PipelineService) ──────────────────

  broadcastDeviceState(deviceId: string, state: DeviceState) {
    this.deviceStates.set(deviceId, state);
    const event: DeviceStateEvent = { deviceId, state };
    this.server?.emit('device:state', event);
  }

  broadcastMessage(deviceId: string, role: string, content: string) {
    const event: DeviceMessageEvent = { deviceId, role, content };
    this.server?.emit('device:message', event);
  }

  /**
   * Send a speak command to a specific device.
   */
  sendSpeakCommand(
    deviceId: string,
    text: string,
    language?: string,
  ) {
    // Find the socket(s) for this device
    for (const [socketId, dId] of this.connectedDevices) {
      if (dId === deviceId) {
        this.server?.to(socketId).emit('command:speak', { text, language });
      }
    }
  }
}
