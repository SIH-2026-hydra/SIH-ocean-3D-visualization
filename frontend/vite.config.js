import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '127.0.0.1',
    open: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
  // Cesium asset handling for Vite
  // Cesium Workers, Assets, and Widgets are bundled by the Cesium npm package
  // and will be resolved from node_modules/cesium during build
});
