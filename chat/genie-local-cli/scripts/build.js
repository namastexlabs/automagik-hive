#!/usr/bin/env node

import { spawn } from 'child_process';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { existsSync, mkdirSync, chmodSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = resolve(__dirname, '..');

console.log('🔨 Building Genie Local CLI...');

// Ensure bundle directory exists
const bundleDir = resolve(rootDir, 'bundle');
if (!existsSync(bundleDir)) {
  mkdirSync(bundleDir, { recursive: true });
}

// Run TypeScript compilation
console.log('📝 Compiling TypeScript...');
const tscProcess = spawn('npx', ['tsc'], {
  cwd: rootDir,
  stdio: 'inherit',
  shell: true,
});

tscProcess.on('close', (code) => {
  if (code !== 0) {
    console.error('❌ TypeScript compilation failed');
    process.exit(1);
  }

  console.log('✅ TypeScript compilation completed');

  // Run esbuild bundling
  console.log('📦 Creating bundle...');
  const esbuildProcess = spawn('node', ['esbuild.config.js'], {
    cwd: rootDir,
    stdio: 'inherit',
    shell: true,
  });

  esbuildProcess.on('close', (bundleCode) => {
    if (bundleCode !== 0) {
      console.error('❌ Bundle creation failed');
      process.exit(1);
    }

    // Make bundle executable
    const bundlePath = resolve(bundleDir, 'genie-cli.js');
    if (existsSync(bundlePath)) {
      chmodSync(bundlePath, '755');
      console.log('✅ Bundle created and made executable');
      console.log(`📁 Bundle location: ${bundlePath}`);
      console.log('🎉 Build completed successfully!');
    } else {
      console.error('❌ Bundle file not found after build');
      process.exit(1);
    }
  });

  esbuildProcess.on('error', (error) => {
    console.error('❌ Bundle process error:', error);
    process.exit(1);
  });
});

tscProcess.on('error', (error) => {
  console.error('❌ TypeScript process error:', error);
  process.exit(1);
});