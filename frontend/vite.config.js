import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    server: {
        port: 5173,
        proxy: {
            '/api': {
                // Compose maps the API to host 8100. Override with VITE_API_PROXY_TARGET
                // (e.g. http://localhost:8000) when running uvicorn on the host.
                target: process.env.VITE_API_PROXY_TARGET || 'http://localhost:8100',
                changeOrigin: true,
                rewrite: function (path) { return path.replace(/^\/api/, ''); },
            },
        },
    },
});
