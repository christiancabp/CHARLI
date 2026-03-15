import { IsString, IsOptional } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class AskDto {
  @ApiProperty({
    description: 'The question to ask CHARLI',
    example: 'What is the capital of France?',
  })
  @IsString()
  question: string;

  @ApiPropertyOptional({
    description: 'Language code for the response (affects system prompt)',
    example: 'en',
    default: 'en',
  })
  @IsString()
  @IsOptional()
  language?: string = 'en';
}

export class AskVisionDto extends AskDto {
  @ApiProperty({
    description: 'Base64-encoded image (JPEG or PNG) from the device camera',
    example: '/9j/4AAQSkZJRgABAQ...',
  })
  @IsString()
  imageBase64: string;

  @ApiPropertyOptional({
    description: 'MIME type of the image',
    example: 'image/jpeg',
    default: 'image/jpeg',
  })
  @IsString()
  @IsOptional()
  imageMime?: string = 'image/jpeg';
}
