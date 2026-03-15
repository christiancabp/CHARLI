import {
  Controller,
  Get,
  Post,
  Patch,
  Body,
  Param,
  UseGuards,
} from '@nestjs/common';
import { DeviceService } from './device.service';
import { AuthGuard } from '../auth/auth.guard';

@Controller('api/devices')
@UseGuards(AuthGuard)
export class DeviceController {
  constructor(private deviceService: DeviceService) {}

  @Get()
  findAll() {
    return this.deviceService.findAll();
  }

  @Post()
  create(
    @Body() body: { name: string; type: string; systemPrompt?: string; maxTokens?: number },
  ) {
    return this.deviceService.create(body);
  }

  @Patch(':id')
  update(
    @Param('id') id: string,
    @Body() body: { systemPrompt?: string; maxTokens?: number },
  ) {
    return this.deviceService.update(id, body);
  }
}
