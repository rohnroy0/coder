import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Non-default ports so this project doesn't collide with other local apps on 5173/8000
    port: 5180,
    strictPort: true,
    // Bind IPv4 too: Node may otherwise listen on ::1 only, and the Tailscale
    // Funnel proxy targets 127.0.0.1 (it got "connection refused" -> 502).
    // allowedHosts still rejects requests with unexpected Host headers.
    host: true,
    // Allow access through a Tailscale Funnel public URL (https://<pc>.<tailnet>.ts.net)
    allowedHosts: ['.ts.net'],
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
    },
  },
});
