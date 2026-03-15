import { Injectable, ConflictException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { v4 as uuid } from 'uuid';

@Injectable()
export class DeviceService {
  constructor(private prisma: PrismaService) {}

  /**
   * List all devices. API keys are STRIPPED from the response to prevent
   * any authenticated device from seeing other devices' secrets.
   */
  async findAll() {
    const devices = await this.prisma.device.findMany({
      orderBy: { createdAt: 'asc' },
    });
    // Security: destructure out apiKey, return everything else
    return devices.map(({ apiKey, ...rest }) => rest);
  }

  async findById(id: string) {
    return this.prisma.device.findUnique({ where: { id } });
  }

  /**
   * Register a new device. Returns the full record INCLUDING the API key.
   * This is the ONLY time the key is visible — save it for device config.
   * Subsequent GET requests will not include the key.
   */
  async create(data: { name: string; type: string; systemPrompt?: string; maxTokens?: number }) {
    // Check for duplicate name
    const existing = await this.prisma.device.findUnique({ where: { name: data.name } });
    if (existing) {
      throw new ConflictException(`Device "${data.name}" already exists`);
    }

    // Generate a unique API key with prefix for easy identification
    const apiKey = `chk_${uuid().replace(/-/g, '')}`;

    return this.prisma.device.create({
      data: {
        name: data.name,
        type: data.type,
        apiKey,
        systemPrompt: data.systemPrompt,
        maxTokens: data.maxTokens ?? 150,
      },
    });
  }

  /**
   * Update device config. API key is stripped from the response.
   */
  async update(id: string, data: { systemPrompt?: string; maxTokens?: number }) {
    const { apiKey, ...rest } = await this.prisma.device.update({
      where: { id },
      data,
    });
    return rest;
  }
}
