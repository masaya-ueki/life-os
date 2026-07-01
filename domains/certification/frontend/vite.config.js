import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 開発時は Vite(5173) から FastAPI(8000) へプロキシする。
// バックエンド URL は環境変数 VITE_API_TARGET で上書き可能（docker compose 用）。
const apiTarget = process.env.VITE_API_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": { target: apiTarget, changeOrigin: true },
    },
  },
});
