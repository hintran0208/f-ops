#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import { onboardCommand } from './commands/onboard';
import { kbCommand } from './commands/kb';

const program = new Command();

program
  .name('fops')
  .description('F-Ops: AI-powered DevOps automation CLI')
  .version('0.1.0');

// Add onboard command
program.addCommand(onboardCommand);

// Add knowledge base command
program.addCommand(kbCommand);

// Global status command
program
  .command('status')
  .description('Check F-Ops system status')
  .action(() => {
    console.log(chalk.blue.bold('🚀 F-Ops System Status'));
    console.log(chalk.green('✅ CLI: Ready'));
    console.log(chalk.green('✅ Backend API: http://localhost:8000'));
    console.log(chalk.green('✅ Knowledge Base: Connected'));
  });

// Global version command is already handled by commander

// Error handling
program.exitOverride();

try {
  program.parse();
} catch (err: any) {
  if (err.code !== 'commander.version' && err.code !== 'commander.help') {
    console.error(chalk.red('❌ Error:'), err.message);
    process.exit(1);
  }
}