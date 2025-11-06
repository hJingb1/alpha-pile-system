import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react' // 导入 React 插件

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react() // 启用 React 插件，提供 JSX 支持和快速刷新等功能
  ],
  server: {
    // 配置开发服务器 (可选)
    port: 5173, // 开发服务器端口号 (默认是 5173)
    // 如果你的后端API跑在不同端口，需要配置代理来解决跨域问题
    proxy: {
      // 将所有 /api 开头的请求代理到你的 FastAPI 后端
      '/schedule': { 
        target: 'http://localhost:8000', // 你的后端API地址
        changeOrigin: true, // 需要改变源
        // secure: false, // 如果后端是 https 且证书无效，可能需要设置
        // rewrite: (path) => path.replace(/^\/api/, ''), // 如果需要重写路径
      },
      // --- 你需要为视频添加一个新的代理规则 ---
      '/generated_videos': { // 匹配前端请求 /generated_videos/*
        target: 'http://localhost:8000', // 转发到后端
        changeOrigin: true,
        // 可选：如果后端路径与前端不同，可能需要路径重写，但这里应该不需要
        // rewrite: (path) => path.replace(/^\/generated_videos/, '/generated_videos'), 
      }
    }
  }
  // 可以添加其他配置，例如 build, resolve.alias 等
})