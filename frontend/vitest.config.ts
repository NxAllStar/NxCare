import path from 'node:path'
import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config.ts'

// Vitest config, layered on top of the app's Vite config (same @ alias,
// same plugins) so component tests see exactly what the app sees.
export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
      css: false,
      globals: false,
      restoreMocks: true,
      // node_modules.orig-rootowned/ is a local leftover from a permission
      // workaround during `npm install` on this machine (see TASK-021
      // session log) - not part of the app, must never be scanned for tests.
      exclude: ['e2e/**', 'node_modules/**', 'node_modules.orig-rootowned/**'],
      server: {
        deps: {
          inline: ['html-encoding-sniffer', '@exodus/bytes'],
        },
      },
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
  }),
)
