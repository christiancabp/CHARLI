/**
 * `charli status` — show connection and config status.
 *
 * Checks:
 * 1. Config file loaded?
 * 2. Tailscale connected?
 * 3. Server reachable? (GET /health)
 * 4. API key valid? (POST /api/ask with a no-op isn't ideal, so we just show config)
 */

import chalk from 'chalk';
import ora from 'ora';
import { loadConfig, CONFIG_FILE_PATH } from '../lib/config.js';
import { ApiClient } from '../lib/api-client.js';
import { getTailscaleStatus } from '../lib/tailscale.js';
import * as output from '../lib/output.js';

export async function statusCommand(): Promise<void> {
  // 1. Config
  console.log(chalk.bold('\nCHARLI Status\n'));

  const config = await loadConfig();
  if (!config) {
    output.warn(`No config found. Run ${chalk.bold('charli init')} to set up.`);
    output.info(`Config path: ${CONFIG_FILE_PATH}`);
    return;
  }

  output.field('Config', CONFIG_FILE_PATH);
  output.field('Server', config.serverUrl);
  output.field('Device', config.deviceName || '(not set)');
  output.field('API Key', config.apiKey ? config.apiKey.slice(0, 8) + '...' : '(not set)');

  // 2. Tailscale
  console.log();
  const spinner = ora('Checking Tailscale...').start();
  const tsStatus = await getTailscaleStatus();

  if (tsStatus.connected) {
    spinner.succeed(`Tailscale: connected as ${chalk.bold(tsStatus.hostname)}`);
    if (tsStatus.tailscaleIp) {
      output.field('  Tailscale IP', tsStatus.tailscaleIp);
    }
  } else {
    spinner.warn('Tailscale: not connected');
  }

  // 3. Server health
  const healthSpinner = ora('Checking server...').start();
  const client = new ApiClient(config);

  try {
    const health = await client.health();
    healthSpinner.succeed(`Server: ${chalk.green(health.status)}`);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    healthSpinner.fail(`Server: ${chalk.red('unreachable')} — ${msg}`);
  }

  console.log();
}
