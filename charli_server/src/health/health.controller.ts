import { Controller, Get } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';

@ApiTags('Health')
@Controller('health')
export class HealthController {
  private readonly startTime = Date.now();

  @Get()
  @ApiOperation({
    summary: 'Health check',
    description:
      'Returns server status, uptime, and version. No authentication required. ' +
      'Use this for monitoring, load balancers, or device connectivity checks.',
  })
  @ApiResponse({
    status: 200,
    description: 'Server is healthy',
    schema: {
      type: 'object',
      properties: {
        status: { type: 'string', example: 'ok' },
        uptime: { type: 'number', example: 3600, description: 'Uptime in seconds' },
        version: { type: 'string', example: '0.1.0' },
        timestamp: { type: 'string', example: '2026-03-15T12:00:00.000Z' },
      },
    },
  })
  check() {
    return {
      status: 'ok',
      uptime: Math.floor((Date.now() - this.startTime) / 1000),
      version: '0.1.0',
      timestamp: new Date().toISOString(),
    };
  }
}
