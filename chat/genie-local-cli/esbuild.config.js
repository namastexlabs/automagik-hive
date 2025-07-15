import { build } from 'esbuild';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const isProduction = process.env.NODE_ENV === 'production';

async function buildBundle() {
  try {
    await build({
      entryPoints: [resolve(__dirname, 'src/index.ts')],
      bundle: true,
      outfile: resolve(__dirname, 'bundle/genie-cli.js'),
      platform: 'node',
      target: 'node20',
      format: 'esm',
      banner: {
        js: `#!/usr/bin/env node\nimport { createRequire as _gcliCreateRequire } from 'module'; const require = _gcliCreateRequire(import.meta.url); globalThis.__filename = require('url').fileURLToPath(import.meta.url); globalThis.__dirname = require('path').dirname(globalThis.__filename);`,
      },
      minify: isProduction,
      sourcemap: !isProduction,
      metafile: true,
      logLevel: 'info',
      define: {
        'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
      },
    });

    console.log('✅ Bundle created successfully!');
  } catch (error) {
    console.error('❌ Build failed:', error);
    process.exit(1);
  }
}

buildBundle();