import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    watch: { usePolling: true },
    proxy: {
      "/api": "http://backend:8000",
      "/out": "http://backend:8000",
    },
  },
});
