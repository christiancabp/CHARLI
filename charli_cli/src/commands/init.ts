/**
 * `charli init` — interactive setup wizard.
 *
 * Steps:
 * 1. Detect Tailscale and suggest server URL
 * 2. Prompt for server URL (or confirm suggestion)
 * 3. Validate server via /health
 * 4. Prompt for API key (paste existing or register new device)
 * 5. Save config to ~/.charli/config.json
 */

import { createInterface } from 'node:readline';
import chalk from 'chalk';
import ora from 'ora';
import { loadConfig, saveConfig, CONFIG_FILE_PATH } from '../lib/config.js';
import { ApiClient } from '../lib/api-client.js';
import { getTailscaleStatus, findServerPeer } from '../lib/tailscale.js';
import * as output from '../lib/output.js';
import type { CharliConfig } from '../types.js';

/** Prompt for user input */
function prompt(question: string, defaultValue?: string): Promise<string> {
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  const suffix = defaultValue ? ` ${chalk.dim(`(${defaultValue})`)}` : '';
  return new Promise((resolve) => {
    rl.question(`${question}${suffix}: `, (answer) => {
      rl.close();
      resolve(answer.trim() || defaultValue || '');
    });
  });
}

export async function initCommand(): Promise<void> {
  console.log(chalk.bold('\nCHARLI Setup\n'));

  const existing = await loadConfig();
  if (existing) {
    output.info(`Existing config found at ${CONFIG_FILE_PATH}`);
    output.info('This will overwrite your current settings.\n');
  }

  // 1. Tailscale detection
  let suggestedUrl = '';
  const spinner = ora('Checking Tailscale...').start();
  const tsStatus = await getTailscaleStatus();

  if (tsStatus.connected) {
    spinner.succeed(`Tailscale: connected as ${chalk.bold(tsStatus.hostname)}`);
    const serverPeer = findServerPeer(tsStatus);
    if (serverPeer) {
      suggestedUrl = `http://${serverPeer.hostname}:3000`;
      output.success(`Found CHARLI server: ${chalk.bold(serverPeer.hostname)} (${serverPeer.tailscaleIp})`);
    } else {
      output.info('No known CHARLI server found among Tailscale peers.');
    }
  } else {
    spinner.warn('Tailscale not connected — you\'ll need to enter the server URL manually.');
  }

  // 2. Server URL
  const defaultUrl = suggestedUrl || existing?.serverUrl || 'http://charli-server:3000';
  const serverUrl = await prompt('Server URL', defaultUrl);

  // 3. Validate server
  const testConfig: CharliConfig = { serverUrl, apiKey: '', deviceName: '' };
  const healthSpinner = ora('Checking server...').start();
  try {
    const client = new ApiClient(testConfig);
    await client.health();
    healthSpinner.succeed('Server is reachable');
  } catch {
    healthSpinner.fail('Could not reach server');
    output.warn('Saving config anyway — you can fix the URL later.\n');
  }

  // 4. API key
  console.log();
  output.info('You need an API key for your CLI device.');
  output.info('Option 1: Paste an existing key (from seed output or admin)');
  output.info('Option 2: Register a new device (requires admin key)\n');

  const choice = await prompt('Paste API key, or type "new" to register', existing?.apiKey || '');

  let apiKey: string;
  let deviceName: string;

  if (choice.toLowerCase() === 'new') {
    // Register new device
    const adminKey = await prompt('Admin API key');
    deviceName = await prompt('Device name', `charli-${tsStatus.hostname || 'cli'}`);

    const regSpinner = ora('Registering device...').start();
    try {
      const client = new ApiClient({ serverUrl, apiKey: '', deviceName: '' });
      const device = await client.registerDevice(deviceName, 'cli', adminKey);
      apiKey = device.apiKey || '';
      regSpinner.succeed(`Registered ${chalk.bold(deviceName)}`);
      if (apiKey) {
        output.info(`API key: ${apiKey}`);
      }
    } catch (err) {
      regSpinner.fail('Registration failed');
      const msg = err instanceof Error ? err.message : String(err);
      output.error(msg);
      process.exit(1);
    }
  } else {
    apiKey = choice;
    deviceName = await prompt('Device name (for display)', existing?.deviceName || 'charli-cli');
  }

  // 5. Save config
  const config: CharliConfig = { serverUrl, apiKey, deviceName };
  await saveConfig(config);

  console.log();
  output.success(`Config saved to ${CONFIG_FILE_PATH}`);
  output.info(`Try: ${chalk.bold('charli status')} or ${chalk.bold('charli ask "Hello!"')}`);
  console.log();
}
