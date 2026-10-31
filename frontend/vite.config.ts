import { createLogger, defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const logger = createLogger();
const logError = logger.error.bind(logger);
logger.error = (message, options) => logError(message.replace(/(\/(?:out\/\d+|api\/properties(?:\/\d+)?)\/)\?[^\s\u001b]+/g, "$1?[redacted]"), options);

export default defineConfig({
  customLogger: logger,
  plugins: [react()],
  server: {
    allowedHosts: ["louise-refurbished-warner-that.trycloudflare.com"],
    watch: { usePolling: true },
    proxy: {
      "/api": { target: "http://backend:8000", changeOrigin: false },
      "/out": { target: "http://backend:8000", changeOrigin: false },
    },
  },
});
