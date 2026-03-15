import {
  CanActivate,
  ExecutionContext,
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';
import { AuthService } from './auth.service';

/**
 * API Key guard — validates X-API-Key header on all /api/* routes.
 * Attaches the authenticated device to the request object.
 */
@Injectable()
export class AuthGuard implements CanActivate {
  constructor(private authService: AuthService) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest();
    const apiKey = request.headers['x-api-key'] as string;

    if (!apiKey) {
      throw new UnauthorizedException('Missing X-API-Key header');
    }

    // Admin key is valid for device management endpoints
    if (this.authService.isAdminKey(apiKey)) {
      request.device = null;
      request.isAdmin = true;
      return true;
    }

    const device = await this.authService.validateApiKey(apiKey);
    if (!device) {
      throw new UnauthorizedException('Invalid API key');
    }

    request.device = device;
    request.isAdmin = false;
    return true;
  }
}
