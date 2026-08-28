var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
import { defineConfig, devices } from '@playwright/test';
var e2eApi = process.env.E2E_API === '1';
export default defineConfig({
    testDir: './e2e',
    fullyParallel: !e2eApi,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI || e2eApi ? 1 : undefined,
    reporter: 'list',
    timeout: 60000,
    use: {
        baseURL: 'http://localhost:5173',
        trace: 'on-first-retry',
    },
    projects: [
        {
            name: 'chromium',
            use: __assign({}, devices['Desktop Chrome']),
        },
    ],
    webServer: {
        command: 'npm run dev -- --host 127.0.0.1 --port 5173',
        url: 'http://localhost:5173',
        reuseExistingServer: !process.env.CI,
        timeout: 120000,
        env: __assign(__assign(__assign({}, process.env), { 
            // Prefer Vite proxy to the local API (see vite.config.ts).
            VITE_API_BASE_URL: process.env.VITE_API_BASE_URL || '/api' }), (e2eApi
            ? {
                VITE_API_PROXY_TARGET: process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000',
            }
            : {})),
    },
});
