import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  // Vue SFC(.vue 파일)를 Vite가 해석할 수 있도록 공식 Vue 플러그인을 사용한다.
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        // 프론트 코드에서는 /api/...로만 호출하고,
        // 개발 서버 proxy가 Django 백엔드(8000번)로 전달해 CORS/host 차이를 줄인다.
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
