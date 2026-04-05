/**
 * Config — loads and saves ~/.charli/config.json.
 *
 * Environment variables override file values:
 *   CHARLI_SERVER_URL → serverUrl
 *   CHARLI_API_KEY    → apiKey
 *
 * This is the same pattern the Pi desk hub uses (~/.bashrc env vars)
 * but with a JSON config file as the primary source.
 */

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { homedir } from 'node:os';
import { join } from 'node:path';
import type { CharliConfig } from '../types.js';

const CONFIG_DIR = join(homedir(), '.charli');
const CONFIG_PATH = join(CONFIG_DIR, 'config.json');

/**
 * Load config from file, then overlay env vars.
 * Returns null if no config file exists and no env vars are set.
 */
export async function loadConfig(): Promise<CharliConfig | null> {
  let fileConfig: Partial<CharliConfig> = {};

  try {
    const raw = await readFile(CONFIG_PATH, 'utf-8');
    fileConfig = JSON.parse(raw);
  } catch {
    // No config file yet — that's fine
  }

  // Env vars override file values (same names as Pi desk hub)
  const config: CharliConfig = {
    serverUrl: process.env.CHARLI_SERVER_URL || fileConfig.serverUrl || '',
    apiKey: process.env.CHARLI_API_KEY || fileConfig.apiKey || '',
    deviceName: fileConfig.deviceName || '',
  };

  // If nothing is configured at all, return null so callers can prompt setup
  if (!config.serverUrl && !config.apiKey) {
    return null;
  }

  return config;
}

/**
 * Save config to ~/.charli/config.json.
 * Creates the directory if it doesn't exist.
 */
export async function saveConfig(config: CharliConfig): Promise<void> {
  await mkdir(CONFIG_DIR, { recursive: true });
  await writeFile(CONFIG_PATH, JSON.stringify(config, null, 2) + '\n', 'utf-8');
}

/** Path to the config file (for display in status/init) */
export const CONFIG_FILE_PATH = CONFIG_PATH;
