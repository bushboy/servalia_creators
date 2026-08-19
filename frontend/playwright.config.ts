import { defineConfig, devices } from '@playwright/test';

const e2eApi = process.env.E2E_API === '1';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: !e2eApi,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI || e2eApi ? 1 : undefined,
  reporter: 'list',
  timeout: 60_000,
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 5173',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
      ...process.env,
      // Prefer Vite proxy to the local API (see vite.config.ts).
      VITE_API_BASE_URL: process.env.VITE_API_BASE_URL || '/api',
      // CI and host uvicorn listen on 8000; Compose maps the API to 8100.
      ...(e2eApi
        ? {
            VITE_API_PROXY_TARGET:
              process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000',
          }
        : {}),
    },
  },
});
