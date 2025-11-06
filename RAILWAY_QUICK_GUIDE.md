# 🚂 Railway 部署快速指南

## ⚠️ 重要提示

Railway **不支持 `docker-compose.yml`**，需要分别部署前端和后端作为两个独立的服务。

---

## 📋 部署前准备

### 1. 推送代码到 GitHub

```powershell
cd d:\1_AAA_HJB\MCTS\alpha-pile\cp_sat_pile

# 添加所有文件
git add .

# 提交更改
git commit -m "Add Railway deployment configuration"

# 推送到 GitHub
git push origin main
```

---

## 🎯 Railway 部署步骤

### 第一步：部署后端

#### 1. 登录 Railway
- 访问: https://railway.app
- 使用 GitHub 账号登录

#### 2. 创建新项目
- 点击 "New Project"
- 选择 "Deploy from GitHub repo"
- 选择你的仓库（例如：`alpha-pile-system`）
- 点击 "Deploy Now"

#### 3. 配置后端服务

Railway 会自动检测到多个目录，你需要手动配置：

**方法 A：使用 Railway 界面配置**

1. 项目创建后，点击进入项目
2. 点击你的服务
3. 进入 "Settings" 标签
4. 配置以下选项：

```
Service Name: alpha-pile-backend
Root Directory: alpha-pile-backend
```

5. 在 "Variables" 标签添加环境变量：
```
PORT=8000
PYTHONUNBUFFERED=1
```

6. 点击 "Redeploy"

**方法 B：删除服务重新创建**

如果上面的方法不行：

1. 删除当前服务（点击服务 → Settings → Danger Zone → Remove Service）
2. 点击 "+ New Service"
3. 选择 "GitHub Repo"
4. 选择你的仓库
5. **重要**：在服务创建时配置：
   - Root Directory: `alpha-pile-backend`
   - 确保检测到 `Dockerfile`

#### 4. 等待部署完成

- 查看 "Deployments" 标签的实时日志
- 第一次部署需要 5-10 分钟（下载 Python、安装依赖等）
- 成功后会显示绿色 ✓

#### 5. 获取后端 URL

- 进入 "Settings" 标签
- 找到 "Domains" 部分
- 点击 "Generate Domain"
- 复制生成的 URL，类似：`https://alpha-pile-backend-production.up.railway.app`

---

### 第二步：部署前端

#### 1. 在同一项目中添加前端服务

- 在项目主页，点击 "+ New Service"
- 选择 "GitHub Repo"
- 再次选择同一个仓库

#### 2. 配置前端服务

在服务创建时或创建后配置：

```
Service Name: alpha-pile-frontend
Root Directory: alpha-pile-fronted
```

#### 3. 添加环境变量（重要！）

在 "Variables" 标签添加：

```
VITE_API_URL=https://你的后端域名.railway.app
```

**示例**：
```
VITE_API_URL=https://alpha-pile-backend-production.up.railway.app
```

⚠️ **注意**：
- 使用你在步骤 5 中获取的后端 URL
- 不要在 URL 末尾加 `/`

#### 4. 重新部署

添加环境变量后，点击 "Redeploy" 让配置生效。

#### 5. 生成前端域名

- 进入前端服务的 "Settings"
- 在 "Domains" 部分点击 "Generate Domain"
- 复制前端 URL，类似：`https://alpha-pile-frontend-production.up.railway.app`

---

### 第三步：测试部署

#### 1. 测试后端

访问：`https://你的后端URL/docs`

应该看到 FastAPI 的 Swagger 文档页面。

#### 2. 测试前端

访问：`https://你的前端URL`

应该看到桩基施工调度优化系统的界面。

#### 3. 测试完整功能

1. 在前端上传测试数据
2. 配置参数
3. 点击"开始优化"
4. 检查是否能成功调用后端 API

---

## 🔍 常见问题排查

### 问题 1: "Build failed" - 构建失败

**查看日志**：
- 点击 "Deployments" → 查看失败的部署
- 点击 "View Logs" 查看详细错误

**常见原因**：

#### A. npm 依赖下载失败

**症状**：
```
short read: expected 40013340 bytes but got 393216
```

**解决**：
- 确认 `alpha-pile-fronted/.npmrc` 文件存在
- 检查 Dockerfile 是否正确复制了 `.npmrc`

#### B. Dockerfile 路径问题

**症状**：
```
Dockerfile not found
```

**解决**：
- 确认 Root Directory 设置正确
- Dockerfile 应该在 Root Directory 下

---

### 问题 2: "Application failed to respond" - 应用无响应

**原因**：端口配置错误

**解决**：

1. 检查后端 Dockerfile 的 CMD 命令：
```dockerfile
CMD uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}
```

2. 确认环境变量中有 `PORT` 或使用 Railway 自动注入的 `$PORT`

---

### 问题 3: 前端无法访问后端 API

**症状**：
```
Failed to fetch
CORS error
```

**解决**：

#### A. 检查前端环境变量

在前端服务的 "Variables" 中确认：
```
VITE_API_URL=https://你的后端完整URL
```

#### B. 检查后端 CORS 配置

确认 `api.py` 中有：
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或指定前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### C. 重新部署前端

修改环境变量后需要重新部署：
- 进入前端服务
- 点击 "Deployments"
- 点击最新的部署
- 点击 "Redeploy"

---

### 问题 4: 构建超时

**症状**：
```
Build exceeded maximum time limit
```

**原因**：免费版构建时间限制

**解决方案**：

#### 方案 A: 优化 Dockerfile（已完成）
- 使用淘宝 npm 镜像
- 已在你的配置中实现

#### 方案 B: 本地构建前端
1. 在本地运行 `npm run build`
2. 修改前端 Dockerfile 直接使用 dist 目录
3. 跳过构建步骤

#### 方案 C: 升级 Railway 计划
- Railway Pro: $20/月
- 更长的构建时间
- 更多资源

---

## 📊 部署后检查清单

- [ ] 后端服务显示 "Active"（绿色）
- [ ] 前端服务显示 "Active"（绿色）
- [ ] 后端 `/docs` 可以访问
- [ ] 前端页面可以正常加载
- [ ] 前端环境变量 `VITE_API_URL` 已正确设置
- [ ] 可以上传数据文件
- [ ] 可以运行优化任务
- [ ] 可以查看结果

---

## 🎯 部署架构图

```
GitHub Repository
       ↓
Railway Project
       ├─→ Backend Service (alpha-pile-backend/)
       │   ├─ Dockerfile
       │   ├─ railway.toml
       │   └─ Domain: https://xxx-backend.railway.app
       │
       └─→ Frontend Service (alpha-pile-fronted/)
           ├─ Dockerfile
           ├─ railway.toml
           ├─ ENV: VITE_API_URL=backend-domain
           └─ Domain: https://xxx-frontend.railway.app
```

---

## 💰 Railway 费用说明

### Free Plan（免费）:
- ✅ $5 免费额度/月
- ✅ 512 MB RAM
- ✅ 1 GB Disk
- ✅ 自动 HTTPS
- ⚠️ 冷启动（无流量时休眠）

### Hobby Plan（$5/月）:
- ✅ $5 + 使用量计费
- ✅ 8 GB RAM
- ✅ 100 GB Disk
- ✅ 无休眠

### 预估成本：
- 小规模使用：免费额度足够
- 中等使用：$5-10/月
- 频繁使用：$10-20/月

---

## 🔄 更新部署

### 自动部署（推荐）

Railway 默认启用自动部署：

1. 在本地修改代码
2. 提交并推送到 GitHub:
   ```bash
   git add .
   git commit -m "Update feature"
   git push
   ```
3. Railway 自动检测更新并重新部署

### 手动部署

1. 进入 Railway 项目
2. 选择服务
3. 点击 "Deployments"
4. 点击 "Redeploy"

---

## 📞 需要帮助？

### 查看日志

```bash
# 安装 Railway CLI
npm i -g @railway/cli

# 登录
railway login

# 链接项目
railway link

# 查看日志
railway logs
```

### 或在 Web 界面：
- 进入服务
- 点击 "Deployments"
- 点击部署记录
- 点击 "View Logs"

---

## 🎉 成功部署后

你的应用已经在云端运行！

- ✅ 分享 URL 给团队成员使用
- ✅ 代码更新自动部署
- ✅ 自动 HTTPS 安全连接
- ✅ 全球 CDN 加速

---

## 📝 下一步建议

1. **设置自定义域名**（可选）
   - 在 Railway Settings → Domains
   - 添加自己的域名

2. **配置监控**
   - Railway 内置监控
   - 查看 CPU、内存、网络使用情况

3. **备份数据**
   - 导出重要的调度结果
   - 定期备份上传的文件

---

**祝部署顺利！** 🚀

如有问题，请查看 Railway 的实时日志或联系我！
