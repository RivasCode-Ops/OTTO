import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    // DECISÃO (2026-11-06): bind IPv4 explícito — no Windows, host default
    // "localhost" pode escutar só em ::1 e quebrar http://127.0.0.1:5194 dos docs.
    host: '127.0.0.1',
    port: 5194,
    strictPort: true,
    proxy: {
      '/api': 'http://127.0.0.1:8791',
      '/health': 'http://127.0.0.1:8791',
    },
  },
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
});
