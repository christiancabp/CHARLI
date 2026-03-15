import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

/**
 * ConversationService — manages conversation history per device.
 *
 * Each device has one active conversation. Messages are appended to it.
 * Clearing a conversation deletes all its messages.
 */
@Injectable()
export class ConversationService {
  private readonly logger = new Logger(ConversationService.name);

  constructor(private prisma: PrismaService) {}

  /**
   * Get or create the active conversation for a device.
   */
  async getOrCreateConversation(deviceId: string) {
    // Find existing conversation (most recent)
    let conversation = await this.prisma.conversation.findFirst({
      where: { deviceId },
      orderBy: { updatedAt: 'desc' },
    });

    if (!conversation) {
      conversation = await this.prisma.conversation.create({
        data: { deviceId },
      });
      this.logger.log(`Created new conversation for device ${deviceId}`);
    }

    return conversation;
  }

  /**
   * Add a message to the active conversation.
   */
  async addMessage(deviceId: string, role: string, content: string) {
    const conversation = await this.getOrCreateConversation(deviceId);

    const message = await this.prisma.message.create({
      data: {
        conversationId: conversation.id,
        role,
        content,
      },
    });

    return { ...message, conversationId: conversation.id };
  }

  /**
   * Get conversation history for context (last N turns as role/content pairs).
   */
  async getHistory(
    deviceId: string,
    maxTurns: number = 3,
  ): Promise<Array<{ role: string; content: string }>> {
    const conversation = await this.prisma.conversation.findFirst({
      where: { deviceId },
      orderBy: { updatedAt: 'desc' },
    });

    if (!conversation) return [];

    const messages = await this.prisma.message.findMany({
      where: { conversationId: conversation.id },
      orderBy: { createdAt: 'asc' },
      take: maxTurns * 2,
      select: { role: true, content: true },
    });

    return messages;
  }

  /**
   * Get the full active conversation with all messages.
   */
  async getActiveConversation(deviceId: string) {
    const conversation = await this.prisma.conversation.findFirst({
      where: { deviceId },
      orderBy: { updatedAt: 'desc' },
      include: {
        messages: { orderBy: { createdAt: 'asc' } },
      },
    });

    return conversation;
  }

  /**
   * Clear the active conversation (delete all messages, create fresh).
   */
  async clearConversation(deviceId: string) {
    const conversation = await this.prisma.conversation.findFirst({
      where: { deviceId },
      orderBy: { updatedAt: 'desc' },
    });

    if (conversation) {
      await this.prisma.message.deleteMany({
        where: { conversationId: conversation.id },
      });
      await this.prisma.conversation.delete({
        where: { id: conversation.id },
      });
    }

    this.logger.log(`Cleared conversation for device ${deviceId}`);
    return { cleared: true };
  }
}
