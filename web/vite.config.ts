/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  base: './',
  server: { fs: { allow: ['..'] } }, // config/ and fixtures/ live one level up
  test: { include: ['src/**/*.test.ts'], environment: 'node' },
});
