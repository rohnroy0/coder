import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Shared by the dev server and the built-site preview server.
  // host:true binds IPv4 too (the Tailscale Funnel proxy targets 127.0.0.1,
  // and Node may otherwise listen on ::1 only -> 502). allowedHosts still
  // rejects requests with unexpected Host headers. The /api proxy forwards
  // backend calls to FastAPI on :8100.
  server: {
    port: 5180,
    strictPort: true,
    host: true,
    allowedHosts: ['.ts.net'],
    proxy: {
      '/api': { target: 'http://127.0.0.1:8100', changeOrigin: true },
    },
  },
  // `vite preview` serves the production build (npm run build) with NO
  // hot-reload websocket, so the page never auto-refreshes - the right way
  // to serve a demo, especially over a tunnel on mobile.
  preview: {
    port: 5180,
    strictPort: true,
    host: true,
    allowedHosts: ['.ts.net'],
    proxy: {
      '/api': { target: 'http://127.0.0.1:8100', changeOrigin: true },
    },
  },
});
