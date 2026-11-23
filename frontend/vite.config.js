import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  // Read the root .env (one folder up). Inside Docker the value arrives as a normal environment variable.
  const env = loadEnv(mode, "..", "");

  return {
    plugins: [react()],
    // Make API_KEY available in the React code as import.meta.env.VITE_API_KEY
    define: { "import.meta.env.VITE_API_KEY": JSON.stringify(env.API_KEY) },
    server: {
      port: 5173,
      // While developing, every /api call is forwarded to the Python backend.
      // This keeps frontend and backend on the "same site", so cookies just work.
      proxy: { "/api": "http://localhost:8000" },
    },
  };
});
