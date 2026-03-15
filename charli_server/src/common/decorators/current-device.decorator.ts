import { createParamDecorator, ExecutionContext } from '@nestjs/common';

/**
 * Extract the authenticated device from the request.
 * Usage: @CurrentDevice() device: Device
 */
export const CurrentDevice = createParamDecorator(
  (_data: unknown, ctx: ExecutionContext) => {
    const request = ctx.switchToHttp().getRequest();
    return request.device;
  },
);
