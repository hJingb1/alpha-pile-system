# 🚀 桩基施工调度优化系统 - 云端部署指南

## 📋 目录
1. [部署前准备](#部署前准备)
2. [本地测试](#本地测试)
3. [快速部署平台选择](#快速部署平台选择)
4. [Render 平台部署 (推荐)](#render-平台部署)
5. [Railway 平台部署](#railway-平台部署)
6. [常见问题解决](#常见问题解决)

---

## 🛠️ 部署前准备

### 1. 安装必要工具

#### Windows 用户:
1. **安装 Docker Desktop**
   - 下载: https://www.docker.com/products/docker-desktop/
   - 安装后重启电脑
   - 启动 Docker Desktop,确保右下角显示 "Docker is running"

2. **安装 Git**
   - 下载: https://git-scm.com/download/win
   - 安装时选择 "Git from the command line and also from 3rd-party software"

3. **注册 GitHub 账号**
   - 访问: https://github.com
   - 点击 "Sign up" 注册账号

### 2. 验证安装

打开 PowerShell 或命令提示符,运行:

```bash
docker --version
git --version
```

如果都显示版本号,说明安装成功!

---

## 🧪 本地测试

在部署到云端前,先在本地测试确保一切正常。

### 步骤 1: 进入项目目录

```bash
cd d:\1_AAA_HJB\MCTS\alpha-pile\cp_sat_pile
```

### 步骤 2: 创建数据目录

```bash
mkdir data
mkdir data\generated_videos
```

### 步骤 3: 启动 Docker 容器

```bash
docker-compose up --build
```

**第一次运行会比较慢** (10-15分钟),因为需要下载依赖。

### 步骤 4: 测试访问

- 打开浏览器访问: http://localhost
- 应该能看到桩基施工调度优化系统的界面
- 测试上传文件、运行优化等功能

### 步骤 5: 停止服务

按 `Ctrl + C` 停止,或运行:

```bash
docker-compose down
```

**✅ 如果本地测试成功,说明 Docker 配置没问题,可以继续云端部署!**

---

## 🌐 快速部署平台选择

| 平台 | 免费额度 | 优点 | 缺点 | 推荐度 |
|------|---------|------|------|--------|
| **Render** | ✅ 750小时/月 | 简单、稳定、自动HTTPS | 冷启动慢 | ⭐⭐⭐⭐⭐ |
| **Railway** | ✅ $5 免费额度 | 快速、界面好看 | 额度用完需充值 | ⭐⭐⭐⭐ |
| **Fly.io** | ✅ 有限免费 | 全球CDN | 配置复杂 | ⭐⭐⭐ |

**推荐使用 Render**,下面是详细步骤。

---

## 🎯 Render 平台部署 (推荐)

### 第一步: 准备 GitHub 仓库

#### 1.1 初始化 Git 仓库

```bash
cd d:\1_AAA_HJB\MCTS\alpha-pile\cp_sat_pile
git init
```

#### 1.2 创建 .gitignore 文件

在项目根目录创建 `.gitignore`:

```
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg-info/
venv/
env/

# Node
node_modules/
dist/
.npm/

# IDE
.vscode/
.idea/

# 环境变量
.env
.env.local

# 数据文件
data/
generated_videos/
*.mp4
*.gif

# 日志
*.log
```

#### 1.3 提交代码

```bash
git add .
git commit -m "Initial commit: Alpha Pile Construction Scheduling System"
```

#### 1.4 推送到 GitHub

1. 访问 https://github.com/new 创建新仓库
2. 仓库名称: `alpha-pile-system` (或任意名称)
3. 选择 **Private** (私有) 或 **Public** (公开)
4. **不要** 勾选 "Add a README file"
5. 点击 "Create repository"

然后运行 (替换 `YOUR_USERNAME` 为你的 GitHub 用户名):

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/alpha-pile-system.git
git push -u origin main
```

**输入 GitHub 用户名和密码** (密码需要使用 Personal Access Token)。

> **如何获取 Personal Access Token:**
> 1. 访问: https://github.com/settings/tokens
> 2. 点击 "Generate new token (classic)"
> 3. 勾选 `repo` 权限
> 4. 复制生成的 token (只显示一次!)

---

### 第二步: 在 Render 上部署

#### 2.1 注册 Render 账号

1. 访问: https://render.com
2. 点击 "Get Started"
3. 使用 GitHub 账号登录 (推荐)

#### 2.2 创建 Web Service (后端)

1. 点击 "New +" → "Web Service"
2. 连接你的 GitHub 仓库 `alpha-pile-system`
3. 配置如下:

```
Name: alpha-pile-backend
Region: Singapore (或选择离你最近的)
Branch: main
Root Directory: alpha-pile-backend
Runtime: Docker
Instance Type: Free
```

4. 点击 "Create Web Service"

**等待 5-10 分钟**,后端服务会自动构建和部署。

部署成功后,你会得到一个 URL,类似:
```
https://alpha-pile-backend.onrender.com
```

#### 2.3 创建 Static Site (前端)

1. 点击 "New +" → "Static Site"
2. 选择同一个 GitHub 仓库
3. 配置如下:

```
Name: alpha-pile-frontend
Branch: main
Root Directory: alpha-pile-fronted
Build Command: npm install && npm run build
Publish Directory: dist
```

4. **重要**: 添加环境变量
   - 点击 "Advanced"
   - 添加环境变量:
     ```
     VITE_API_URL=https://alpha-pile-backend.onrender.com
     ```

5. 点击 "Create Static Site"

#### 2.4 配置前端 API 代理

**问题**: 前端需要访问后端 API,但现在是不同的域名。

**解决方案**: 修改前端代码以使用环境变量。

在 `alpha-pile-fronted/src/services/api.ts` 中,将 API base URL 改为:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

然后重新提交代码:

```bash
git add .
git commit -m "Update API URL to use environment variable"
git push
```

Render 会自动检测到更新并重新部署!

---

### 第三步: 测试部署

1. 访问前端 URL (类似 `https://alpha-pile-frontend.onrender.com`)
2. 测试上传文件
3. 测试运行优化
4. 检查是否能正常生成结果

**如果遇到 CORS 错误**,需要在后端添加前端域名到 CORS 允许列表。

---

## 🚂 Railway 平台部署

Railway 配置更简单,但免费额度有限。

### 步骤 1: 注册 Railway

1. 访问: https://railway.app
2. 使用 GitHub 登录

### 步骤 2: 创建新项目

1. 点击 "New Project"
2. 选择 "Deploy from GitHub repo"
3. 选择你的仓库 `alpha-pile-system`

### 步骤 3: 添加服务

Railway 会自动检测 `docker-compose.yml` 并创建两个服务!

**非常简单**: 点击 "Deploy Now" 即可!

### 步骤 4: 配置域名

1. 点击后端服务
2. 在 "Settings" 中点击 "Generate Domain"
3. 复制生成的域名
4. 在前端服务的环境变量中添加:
   ```
   VITE_API_URL=https://你的后端域名
   ```

---

## ⚠️ 常见问题解决

### 问题 1: Docker 构建失败

**错误**: `ERROR [internal] load metadata for docker.io/library/python:3.10-slim`

**解决**:
```bash
# 检查 Docker 是否运行
docker ps

# 如果报错,重启 Docker Desktop
```

---

### 问题 2: 前端无法访问后端 API

**错误**: `Failed to fetch` 或 `CORS error`

**解决**: 在后端 `api.py` 中检查 CORS 配置:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境改为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 问题 3: 部署后优化计算超时

**原因**: 免费服务器性能有限

**解决方案**:
1. 减少桩数量进行测试
2. 升级到付费计划 (Render: $7/月起)
3. 增加后端超时时间

---

### 问题 4: 冷启动时间长

**原因**: 免费服务在无流量时会休眠

**解决方案**:
1. 使用 UptimeRobot 定期 ping 你的服务
2. 升级到付费计划 (不会休眠)

---

## 🎓 部署后的优化建议

### 1. 添加自定义域名

在 Render 或 Railway 的设置中可以绑定自己的域名。

### 2. 启用 HTTPS

Render 和 Railway 都自动提供免费 SSL 证书!

### 3. 监控服务状态

- Render: 内置监控面板
- Railway: 内置日志和指标

### 4. 设置环境变量

将敏感信息 (如果有) 存储在环境变量中,不要硬编码。

---

## 📞 需要帮助?

如果遇到问题:

1. **检查日志**: 在 Render/Railway 的控制台查看部署日志
2. **本地测试**: 先确保 `docker-compose up` 在本地能正常运行
3. **查看文档**:
   - Render: https://render.com/docs
   - Railway: https://docs.railway.app

---

## 🎉 部署完成!

恭喜! 你的桩基施工调度优化系统已经成功部署到云端!

现在你可以:
- ✅ 通过 URL 分享给别人使用
- ✅ 在任何地方访问系统
- ✅ 自动 HTTPS 加密
- ✅ 代码更新后自动重新部署

**下一步**:
- 测试所有功能是否正常
- 分享 URL 给团队成员
- 根据使用情况考虑升级到付费计划

---

## 📝 快速命令参考

```bash
# 本地测试
docker-compose up --build          # 启动服务
docker-compose down                # 停止服务
docker-compose logs -f backend     # 查看后端日志

# Git 操作
git add .                          # 添加所有更改
git commit -m "描述"               # 提交更改
git push                           # 推送到 GitHub

# 重新构建
docker-compose up --build --force-recreate
```

---

**祝部署顺利!** 🚀

如有问题,随时告诉我!
