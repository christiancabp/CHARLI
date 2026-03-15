import { IsString, IsOptional, IsInt, Min, Max } from 'class-validator';

export class AskDto {
  @IsString()
  question: string;

  @IsString()
  @IsOptional()
  language?: string = 'en';
}

export class AskVisionDto extends AskDto {
  @IsString()
  imageBase64: string;

  @IsString()
  @IsOptional()
  imageMime?: string = 'image/jpeg';
}
