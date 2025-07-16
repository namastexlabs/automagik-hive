import { config } from 'dotenv';

// Load environment variables from .env file
config();

export interface AppConfig {
  // API Configuration
  apiBaseUrl: string;
  apiTimeout: number;
  apiRetryAttempts: number;
  
  
  // CLI Configuration
  cliName: string;
  cliVersion: string;
  cliDebug: boolean;
  
  // Session Configuration
  sessionDir: string;
  sessionMaxHistory: number;
  sessionAutoSave: boolean;
  
  // Display Configuration
  enableColors: boolean;
  enableSpinner: boolean;
  maxDisplayWidth: number;
  
  // Development Configuration
  nodeEnv: string;
  logLevel: string;
  disableUpdateCheck: boolean;
}

function getEnvString(key: string, defaultValue: string): string {
  return process.env[key] || defaultValue;
}

function getEnvNumber(key: string, defaultValue: number): number {
  const value = process.env[key];
  return value ? parseInt(value, 10) : defaultValue;
}

function getEnvBoolean(key: string, defaultValue: boolean): boolean {
  const value = process.env[key];
  return value ? value.toLowerCase() === 'true' : defaultValue;
}

export const appConfig: AppConfig = {
  // API Configuration
  apiBaseUrl: getEnvString('API_BASE_URL', 'http://localhost:9888'),
  apiTimeout: getEnvNumber('API_TIMEOUT', 10000), // Reduced from 30s to 10s
  apiRetryAttempts: getEnvNumber('API_RETRY_ATTEMPTS', 3),
  
  // CLI Configuration
  cliName: getEnvString('CLI_NAME', 'genie-cli'),
  cliVersion: getEnvString('CLI_VERSION', '0.1.0'),
  cliDebug: getEnvBoolean('CLI_DEBUG', false),
  
  // Session Configuration
  sessionDir: getEnvString('SESSION_DIR', '~/.genie-cli/sessions'),
  sessionMaxHistory: getEnvNumber('SESSION_MAX_HISTORY', 100),
  sessionAutoSave: getEnvBoolean('SESSION_AUTO_SAVE', true),
  
  // Display Configuration
  enableColors: getEnvBoolean('ENABLE_COLORS', true),
  enableSpinner: getEnvBoolean('ENABLE_SPINNER', true),
  maxDisplayWidth: getEnvNumber('MAX_DISPLAY_WIDTH', 120),
  
  // Development Configuration
  nodeEnv: getEnvString('NODE_ENV', 'development'),
  logLevel: getEnvString('LOG_LEVEL', 'info'),
  disableUpdateCheck: getEnvBoolean('DISABLE_UPDATE_CHECK', false),
};

export default appConfig;