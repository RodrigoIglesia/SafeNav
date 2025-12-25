// vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/routes": {
        target: "http://safenav-core:8000",
        changeOrigin: true,
      },
    },
  },
});
