import { Injectable, ConflictException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { v4 as uuid } from 'uuid';

@Injectable()
export class DeviceService {
  constructor(private prisma: PrismaService) {}

  async findAll() {
    const devices = await this.prisma.device.findMany({
      orderBy: { createdAt: 'asc' },
    });
    return devices.map(({ apiKey, ...rest }) => rest);
  }

  async findById(id: string) {
    return this.prisma.device.findUnique({ where: { id } });
  }

  async create(data: { name: string; type: string; systemPrompt?: string; maxTokens?: number }) {
    // Check for duplicate name
    const existing = await this.prisma.device.findUnique({ where: { name: data.name } });
    if (existing) {
      throw new ConflictException(`Device "${data.name}" already exists`);
    }

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

  async update(id: string, data: { systemPrompt?: string; maxTokens?: number }) {
    const { apiKey, ...rest } = await this.prisma.device.update({
      where: { id },
      data,
    });
    return rest;
  }
}
