#!/usr/bin/env node

import { spawn } from 'child_process';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = resolve(__dirname, '..');

const isDevelopment = process.env.NODE_ENV !== 'production';

if (isDevelopment) {
  console.log('🚀 Starting Genie Local CLI in development mode...');
  
  // In development, run with ts-node for hot reloading
  const tsNodeProcess = spawn('npx', ['tsx', 'src/index.ts'], {
    cwd: rootDir,
    stdio: 'inherit',
    shell: true,
    env: {
      ...process.env,
      NODE_ENV: 'development',
    },
  });

  tsNodeProcess.on('close', (code) => {
    process.exit(code || 0);
  });

  tsNodeProcess.on('error', (error) => {
    console.error('❌ Development server error:', error);
    process.exit(1);
  });
} else {
  console.log('🚀 Starting Genie Local CLI in production mode...');
  
  // In production, run the built bundle
  const bundlePath = resolve(rootDir, 'bundle/genie-cli.js');
  
  if (!existsSync(bundlePath)) {
    console.error('❌ Bundle not found. Please run "npm run build" first.');
    process.exit(1);
  }

  const bundleProcess = spawn('node', [bundlePath], {
    cwd: rootDir,
    stdio: 'inherit',
    shell: true,
    env: {
      ...process.env,
      NODE_ENV: 'production',
    },
  });

  bundleProcess.on('close', (code) => {
    process.exit(code || 0);
  });

  bundleProcess.on('error', (error) => {
    console.error('❌ Bundle execution error:', error);
    process.exit(1);
  });
}