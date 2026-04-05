/**
 * `charli ask "question"` — send a text question to CHARLI.
 *
 * Loads config, shows a spinner while waiting for the LLM response,
 * then prints CHARLI's answer. Supports follow-up questions
 * because the server tracks conversation history per device.
 */

import chalk from 'chalk';
import ora from 'ora';
import { loadConfig } from '../lib/config.js';
import { ApiClient } from '../lib/api-client.js';
import * as output from '../lib/output.js';

export async function askCommand(question: string): Promise<void> {
  const config = await loadConfig();
  if (!config) {
    output.error(`Not configured. Run ${chalk.bold('charli init')} first.`);
    process.exit(1);
  }

  if (!config.apiKey) {
    output.error(`No API key configured. Run ${chalk.bold('charli init')} to set one.`);
    process.exit(1);
  }

  const client = new ApiClient(config);
  const spinner = ora('Thinking...').start();

  try {
    const response = await client.ask(question);
    spinner.stop();
    output.charliResponse(response.answer);
  } catch (err) {
    spinner.fail('Failed to get a response');
    const msg = err instanceof Error ? err.message : String(err);
    output.error(msg);
    process.exit(1);
  }
}
