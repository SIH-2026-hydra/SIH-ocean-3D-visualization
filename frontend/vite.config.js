import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],

  // Cesium runtime assets are copied to public/cesium.
  // Files inside Vite's public directory are served from "/",
  // so Cesium must resolve Assets/Workers/Widgets from /cesium/.
  define: {
    CESIUM_BASE_URL: JSON.stringify('/cesium/'),
  },

  server: {
    port: 5173,
    host: '127.0.0.1',
    open: true,
  },

  build: {
    outDir: 'dist',
    sourcemap: false,
  },
});