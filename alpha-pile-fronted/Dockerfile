# 前端 Dockerfile - React + Vite 应用
# 阶段 1: 构建阶段
FROM node:18-alpine AS builder

WORKDIR /app

# 复制 npm 配置文件（使用国内镜像源）
COPY .npmrc ./

# 复制 package 文件
COPY package.json package-lock.json* ./

# 配置 npm 使用淘宝镜像源并安装依赖
RUN npm config set registry https://registry.npmmirror.com && \
    npm install --legacy-peer-deps --fetch-timeout=300000 --fetch-retries=5

# 复制源代码
COPY . .

# 声明构建参数（从 Railway 环境变量传入）
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# 构建生产版本
RUN npm run build

# 阶段 2: 生产阶段 - 使用 Nginx 托管静态文件
FROM nginx:alpine

# 复制构建产物到 Nginx 目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
