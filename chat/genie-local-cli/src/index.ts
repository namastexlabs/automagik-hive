import React from 'react';
import { render } from 'ink';
import { AppWrapper } from './ui/App.js';
import { appConfig } from './config/settings.js';

// Version from package.json
const version = '0.1.0';

const main = async () => {
  // Display startup info in debug mode
  if (appConfig.cliDebug) {
    console.log('🧞 Genie Local CLI starting...');
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
      console.log('\\n🧞 Genie Local CLI shutting down...');
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