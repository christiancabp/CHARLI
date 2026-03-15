import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { Device } from '@prisma/generated';

/**
 * AuthService — validates API keys against the database.
 *
 * Two types of keys:
 *   1. Device key (chk_...) — linked to a specific device record in the DB.
 *      The guard attaches the device to the request for downstream use.
 *   2. Admin key (ADMIN_API_KEY env var) — used for bootstrapping (creating
 *      first devices). No device is attached; request.device will be null.
 */
@Injectable()
export class AuthService {
  constructor(private prisma: PrismaService) {}

  /**
   * Validate an API key and return the associated device.
   * Returns null if the key is the admin key (valid but no device).
   * Returns null if the key doesn't match anything (invalid).
   */
  async validateApiKey(apiKey: string): Promise<Device | null> {
    if (!apiKey) return null;

    // Admin key grants access but has no associated device
    if (apiKey === process.env.ADMIN_API_KEY) {
      return null; // Valid auth but no device — handled by guard
    }

    const device = await this.prisma.device.findUnique({
      where: { apiKey },
    });

    if (device) {
      // Update lastSeen timestamp (fire and forget — don't block the request)
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
