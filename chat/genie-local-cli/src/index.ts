import React from 'react';
import { render } from 'ink';
import { AppWrapper } from './ui/App.js';
import { appConfig } from './config/settings.js';
import { runHeadless, formatHeadlessOutput } from './headless.js';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';

// Version from package.json
const version = '0.1.0';

// Parse CLI arguments
const argv = yargs(hideBin(process.argv))
  .option('prompt', {
    alias: 'p',
    type: 'string',
    describe: 'Run in headless mode with this prompt',
  })
  .option('target', {
    alias: 't',
    type: 'string',
    describe: 'Target to use (agent/team/workflow ID or name)',
  })
  .option('session', {
    alias: 's',
    type: 'string',
    describe: 'Session ID to use (optional)',
  })
  .option('output', {
    alias: 'o',
    type: 'string',
    choices: ['json', 'text', 'markdown'],
    default: 'text',
    describe: 'Output format for headless mode',
  })
  .help()
  .argv as any;

const main = async () => {
  // Check if running in headless mode
  if (argv.prompt && argv.target) {
    // Headless mode execution
    const result = await runHeadless({
      prompt: argv.prompt,
      target: argv.target,
      sessionId: argv.session,
      output: argv.output
    });

    const formattedOutput = formatHeadlessOutput(result, argv.output);
    console.log(formattedOutput);
    
    process.exit(result.success ? 0 : 1);
  }

  // Interactive mode
  // Display startup info in debug mode
  if (appConfig.cliDebug) {
    console.log('🎯 Genie Local CLI starting...');
    console.log(`API Base URL: ${appConfig.apiBaseUrl}`);
    console.log(`Session Directory: ${appConfig.sessionDir}`);
    console.log(`Debug Mode: ${appConfig.cliDebug}`);
    console.log('---');
  }

  // Render the application
  const { unmount } = render(React.createElement(AppWrapper, { version }));

  // Handle graceful shutdown
  const cleanup = () => {
    if (appConfig.cliDebug) {
      console.log('\\n🎯 Genie Local CLI shutting down...');
    }
    unmount();
    process.exit(0);
  };

  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);
  process.on('SIGUSR1', cleanup);
  process.on('SIGUSR2', cleanup);
};

// Error handling
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  process.exit(1);
});

// Start the application
main().catch((error) => {
  console.error('Failed to start Genie Local CLI:', error);
  process.exit(1);
});