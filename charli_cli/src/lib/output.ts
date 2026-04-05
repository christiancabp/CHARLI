/**
 * Output helpers — consistent formatting with chalk.
 *
 * Keeps all color/style decisions in one place so the rest
 * of the CLI just calls output.success(), output.error(), etc.
 */

import chalk from 'chalk';

/** Green checkmark + message */
export function success(msg: string): void {
  console.log(chalk.green('✔') + ' ' + msg);
}

/** Red X + message */
export function error(msg: string): void {
  console.error(chalk.red('✖') + ' ' + msg);
}

/** Yellow warning */
export function warn(msg: string): void {
  console.log(chalk.yellow('⚠') + ' ' + msg);
}

/** Dim info line */
export function info(msg: string): void {
  console.log(chalk.dim(msg));
}

/** Bold label: value */
export function field(label: string, value: string): void {
  console.log(`  ${chalk.bold(label)}: ${value}`);
}

/** Print CHARLI's response */
export function charliResponse(text: string): void {
  console.log();
  console.log(chalk.cyan.bold('CHARLI'));
  console.log(text);
  console.log();
}
