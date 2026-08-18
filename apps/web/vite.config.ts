import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "LOGWATCH_");
  return {
    plugins: [react()],
    server: {
      port: Number(env.LOGWATCH_WEB_PORT ?? 5177),
      allowedHosts: [".manus.computer"],
      proxy: {
        "/api": env.LOGWATCH_API_URL ?? "http://127.0.0.1:4300",
      },
    },
  };
});
