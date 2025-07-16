import { request as gaxiosRequest } from 'gaxios';

export interface ServerStatus {
  isRunning: boolean;
  url: string;
  health?: any;
  error?: string;
}

export async function detectAPIServer(baseUrl: string): Promise<ServerStatus> {
  try {
    const response = await gaxiosRequest({
      url: `${baseUrl}/api/v1/health`,
      method: 'GET',
      timeout: 3000,
    });

    return {
      isRunning: true,
      url: baseUrl,
      health: response.data,
    };
  } catch (error) {
    return {
      isRunning: false,
      url: baseUrl,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

export function generateStartupGuide(serverStatus: ServerStatus): string {
  if (serverStatus.isRunning) {
    return `✅ **Server is running at:** ${serverStatus.url}`;
  }

  const guide = `
🚀 **Starting Genie API Server**

📂 **Step 1:** Navigate to genie-agents directory
\`\`\`bash
cd /path/to/genie-agents
\`\`\`

⚡ **Step 2:** Start the server
\`\`\`bash
make dev
\`\`\`

⏳ **Step 3:** Wait for startup message
Look for: "Sistema operacional" message

🔄 **Step 4:** Restart this CLI
\`\`\`bash
./bundle/genie-cli.js
\`\`\`

🔧 **Alternative methods:**
• Quick health check: \`curl ${serverStatus.url}/api/v1/health\`
• Check if port is in use: \`lsof -i :9888\`
• Update server URL in .env: \`API_BASE_URL=http://localhost:9888\`

❌ **Error details:** ${serverStatus.error}`;

  return guide;
}

export async function waitForServerStartup(
  baseUrl: string,
  maxAttempts: number = 30,
  intervalMs: number = 1000,
  onProgress?: (attempt: number, maxAttempts: number) => void
): Promise<ServerStatus> {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    onProgress?.(attempt, maxAttempts);
    
    const status = await detectAPIServer(baseUrl);
    if (status.isRunning) {
      return status;
    }

    if (attempt < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, intervalMs));
    }
  }

  return {
    isRunning: false,
    url: baseUrl,
    error: `Server did not start within ${maxAttempts} seconds`,
  };
}