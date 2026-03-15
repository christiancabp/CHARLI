import {
  Controller,
  Get,
  Post,
  Patch,
  Body,
  Param,
  UseGuards,
} from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiSecurity, ApiBody, ApiParam } from '@nestjs/swagger';
import { DeviceService } from './device.service';
import { AuthGuard } from '../auth/auth.guard';

@ApiTags('Devices')
@ApiSecurity('api-key')
@Controller('api/devices')
@UseGuards(AuthGuard)
export class DeviceController {
  constructor(private deviceService: DeviceService) {}

  @Get()
  @ApiOperation({
    summary: 'List all registered devices',
    description: 'Returns all devices in the registry with their config (API keys are included).',
  })
  @ApiResponse({ status: 200, description: 'List of devices' })
  findAll() {
    return this.deviceService.findAll();
  }

  @Post()
  @ApiOperation({
    summary: 'Register a new device',
    description:
      'Creates a new device and generates an API key for it. ' +
      'Requires the admin API key (`ADMIN_API_KEY` env var). ' +
      'The returned API key should be saved — it\'s the device\'s auth credential.',
  })
  @ApiBody({
    description: 'Device registration data',
    schema: {
      type: 'object',
      properties: {
        name: { type: 'string', example: 'charli-phone', description: 'Unique device name' },
        type: { type: 'string', example: 'phone', description: 'Device type (desk-hub, glasses, phone)' },
        systemPrompt: { type: 'string', description: 'Custom system prompt (optional — uses default for device type if omitted)' },
        maxTokens: { type: 'number', example: 150, description: 'Max response tokens (default: 150)' },
      },
      required: ['name', 'type'],
    },
  })
  @ApiResponse({ status: 201, description: 'Device created with API key' })
  @ApiResponse({ status: 409, description: 'Device name already exists' })
  create(
    @Body() body: { name: string; type: string; systemPrompt?: string; maxTokens?: number },
  ) {
    return this.deviceService.create(body);
  }

  @Patch(':id')
  @ApiOperation({
    summary: 'Update device configuration',
    description:
      'Update a device\'s system prompt or max tokens. ' +
      'Useful for tuning CHARLI\'s behavior per device without code changes.',
  })
  @ApiParam({ name: 'id', description: 'Device UUID' })
  @ApiBody({
    description: 'Fields to update',
    schema: {
      type: 'object',
      properties: {
        systemPrompt: { type: 'string', description: 'New system prompt' },
        maxTokens: { type: 'number', example: 200, description: 'New max response tokens' },
      },
    },
  })
  @ApiResponse({ status: 200, description: 'Device updated' })
  update(
    @Param('id') id: string,
    @Body() body: { systemPrompt?: string; maxTokens?: number },
  ) {
    return this.deviceService.update(id, body);
  }
}
