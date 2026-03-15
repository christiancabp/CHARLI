import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { Device } from '@prisma/client';

@Injectable()
export class AuthService {
  constructor(private prisma: PrismaService) {}

  /**
   * Validate an API key and return the associated device.
   * Also accepts the ADMIN_API_KEY for bootstrap operations.
   */
  async validateApiKey(apiKey: string): Promise<Device | null> {
    if (!apiKey) return null;

    // Check admin key (for device registration)
    if (apiKey === process.env.ADMIN_API_KEY) {
      return null; // Valid auth but no device — handled by guard
    }

    const device = await this.prisma.device.findUnique({
      where: { apiKey },
    });

    if (device) {
      // Update lastSeen timestamp (fire and forget)
      this.prisma.device
        .update({
          where: { id: device.id },
          data: { lastSeen: new Date() },
        })
        .catch(() => {});
    }

    return device;
  }

  isAdminKey(apiKey: string): boolean {
    return apiKey === process.env.ADMIN_API_KEY;
  }
}
