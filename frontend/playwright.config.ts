import { defineConfig } from '@playwright/test'
import { fileURLToPath } from 'node:url'

const backend = fileURLToPath(new URL('../backend/', import.meta.url))

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 30000,
  use: {
    baseURL: 'http://127.0.0.1:15173',
    viewport: { width: 1440, height: 900 },
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    reducedMotion: 'reduce',
  },
  webServer: [
    {
      name: 'API de pruebas',
      command:
        '.venv/bin/python -m uvicorn schedule_compiler.main:app --host 127.0.0.1 --port 18765',
      cwd: backend,
      url: 'http://127.0.0.1:18765/api/v1/health',
      reuseExistingServer: false,
      gracefulShutdown: { signal: 'SIGTERM', timeout: 1000 },
    },
    {
      name: 'Vite de pruebas',
      command: 'npm run dev -- --port 15173',
      url: 'http://127.0.0.1:15173',
      env: { API_TARGET: 'http://127.0.0.1:18765' },
      reuseExistingServer: false,
      gracefulShutdown: { signal: 'SIGTERM', timeout: 1000 },
    },
  ],
})
