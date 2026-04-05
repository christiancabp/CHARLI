/**
 * CHARLI CLI — main program.
 *
 * Wires up Commander.js with all commands.
 * Entry point: bin/charli.js → this file.
 */

import { Command } from 'commander';
import { statusCommand } from './commands/status.js';
import { askCommand } from './commands/ask.js';
import { initCommand } from './commands/init.js';

const program = new Command();

program
  .name('charli')
  .description('Talk to CHARLI from the terminal')
  .version('0.1.0');

program
  .command('init')
  .description('Set up CHARLI CLI (server URL, API key)')
  .action(initCommand);

program
  .command('status')
  .description('Check connection status and config')
  .action(statusCommand);

program
  .command('ask')
  .description('Ask CHARLI a question')
  .argument('<question>', 'Your question (use quotes for multi-word)')
  .action(askCommand);

program.parse();
