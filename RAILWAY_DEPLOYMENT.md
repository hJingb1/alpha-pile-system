# Railway 部署配置指南

## 🚂 Railway 部署步骤

### 问题诊断

根据你的截图，Railway 显示区域为 `asia-southeast1`，这说明服务正在部署。如果失败，通常是以下原因：

1. **构建超时** - npm 下载依赖太慢
2. **内存不足** - 构建前端需要较多内存
3. **端口配置问题** - Railway 使用动态端口

---

## ✅ 解决方案

### 方案 1: 分别部署前后端（推荐）

Railway 不支持 `docker-compose.yml`，需要分别部署。

#### 步骤 1: 部署后端

1. **在 Railway 中创建新项目**
2. **选择 "Deploy from GitHub repo"**
3. **选择你的仓库**
4. **配置服务**:
   - Name: `alpha-pile-backend`
   - Root Directory: `alpha-pile-backend`
   - Build Method: `Dockerfile`

5. **添加环境变量**:
   ```
   PORT=8000
   PYTHONUNBUFFERED=1
   ```

6. **点击 "Deploy"**

#### 步骤 2: 部署前端

1. **在同一个项目中添加新服务**
2. **点击 "+ New Service"**
3. **选择同一个 GitHub 仓库**
4. **配置服务**:
   - Name: `alpha-pile-frontend`
   - Root Directory: `alpha-pile-fronted`
   - Build Method: `Dockerfile`

5. **添加环境变量**:
   ```
   VITE_API_URL=https://你的后端域名.railway.app
   ```

   > **重要**: 等后端部署成功后，复制后端的域名填入这里

6. **点击 "Deploy"**

---

### 方案 2: 使用简化的部署方式（更快）

如果 Docker 构建太慢，可以改用 Railway 的原生构建。

#### 后端配置文件

创建 `railway.toml`（在项目根目录）:

```toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "uvicorn api:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/docs"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
```

#### 前端配置

对于前端，建议**先本地构建**，然后部署静态文件：

```bash
# 在本地运行
cd alpha-pile-fronted
npm install
npm run build
```

然后修改 Railway 配置为静态站点部署。

---

### 方案 3: 合并为单一服务（最简单）

将前后端合并到一个容器中，使用 Nginx 代理。

#### 创建合并的 Dockerfile

在项目根目录创建 `Dockerfile.unified`:

```dockerfile
# 多阶段构建
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY alpha-pile-fronted/package*.json ./
RUN npm config set registry https://registry.npmmirror.com && \
    npm install --legacy-peer-deps
COPY alpha-pile-fronted/ ./
RUN npm run build

FROM python:3.10-slim
WORKDIR /app

# 安装系统依赖和 Nginx
RUN apt-get update && apt-get install -y \
    nginx \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制后端代码
COPY alpha-pile-backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY alpha-pile-backend/ ./

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx-unified.conf /etc/nginx/sites-available/default

# 启动脚本
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8080
CMD ["/start.sh"]
```

#### 创建启动脚本 `start.sh`:

```bash
#!/bin/bash
# 启动 Nginx
nginx

# 启动 FastAPI
uvicorn api:app --host 0.0.0.0 --port 8080
```

#### 创建 Nginx 配置 `nginx-unified.conf`:

```nginx
server {
    listen 80;

    # 前端
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /schedule {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /generated_videos {
        proxy_pass http://127.0.0.1:8080;
    }
}
```

---

## 🔍 Railway 部署检查清单

### 构建前检查:

- [ ] GitHub 仓库已推送最新代码
- [ ] `.npmrc` 文件已添加（npm 镜像源）
- [ ] Dockerfile 配置正确
- [ ] 环境变量已配置

### 部署后检查:

- [ ] 查看 Railway 日志，确认构建成功
- [ ] 复制生成的域名
- [ ] 测试后端 API: `https://后端域名.railway.app/docs`
- [ ] 将后端域名添加到前端环境变量
- [ ] 重新部署前端
- [ ] 测试前端访问

---

## 🐛 常见 Railway 部署错误

### 错误 1: "Build timed out"

**原因**: npm install 太慢

**解决**:
1. 确认 `.npmrc` 文件存在且配置了淘宝镜像
2. 增加 Railway 的构建超时时间（付费功能）
3. 或使用方案 3（本地构建前端）

### 错误 2: "Port binding failed"

**原因**: 没有使用 Railway 提供的 `$PORT` 环境变量

**解决**:
修改后端 Dockerfile 的启动命令：
```dockerfile
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### 错误 3: "Health check failed"

**原因**: 服务启动太慢或端口不对

**解决**:
1. 增加健康检查超时时间
2. 检查端口配置
3. 查看日志确认服务是否真的启动了

---

## 💡 Railway 优化建议

### 1. 使用 Railway CLI 本地测试

```bash
# 安装 Railway CLI
npm i -g @railway/cli

# 登录
railway login

# 链接项目
railway link

# 本地运行（使用 Railway 环境变量）
railway run npm start
```

### 2. 配置自动部署

在 Railway 设置中启用:
- ✅ Auto Deploy from GitHub
- ✅ Deploy on Push to main branch

### 3. 查看实时日志

```bash
railway logs
```

或在 Railway Web 界面的 "Deployments" → "View Logs"

---

## 🎯 推荐的 Railway 部署流程

```
1. 先部署后端
   ↓
2. 获取后端域名
   ↓
3. 配置前端环境变量 (VITE_API_URL)
   ↓
4. 部署前端
   ↓
5. 测试完整功能
```

---

## 📞 如果还是失败

请提供以下信息：

1. **Railway 部署日志** (在 Deployments → View Logs)
2. **具体错误信息**
3. **是在构建阶段还是运行阶段失败**

我会根据具体情况提供更精确的解决方案！

---

**现在建议使用方案 1，先单独部署后端，成功后再部署前端！** 🚀
