# Docker 镜像源配置指南

## 问题描述
Docker 无法连接到 Docker Hub，错误信息：
```
dial tcp 108.160.169.171:443: connectex: A connection attempt failed...
```

这是因为国内网络访问 Docker Hub 不稳定。

---

## 🚀 快速修复步骤

### 方法 1：使用 Docker Desktop 图形界面配置（推荐）

#### 步骤 1：打开 Docker Desktop 设置

1. 右键点击任务栏的 Docker 图标
2. 点击 "Settings" (设置)
3. 左侧点击 "Docker Engine"

#### 步骤 2：添加镜像源配置

在右侧的 JSON 配置中，找到或添加 `registry-mirrors` 字段：

```json
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false,
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://docker.nju.edu.cn"
  ],
  "dns": ["8.8.8.8", "8.8.4.4"]
}
```

**注意**：不要删除原有的配置，只需添加 `registry-mirrors` 和 `dns` 字段。

#### 步骤 3：应用并重启

1. 点击 "Apply & Restart" 按钮
2. 等待 Docker 重启完成（约 30 秒）
3. 确认右下角显示 "Docker is running"

---

### 方法 2：手动编辑配置文件

#### Windows 位置：
```
C:\Users\你的用户名\.docker\daemon.json
```

如果文件不存在，创建它，并填入以下内容：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://docker.nju.edu.cn"
  ],
  "dns": ["8.8.8.8", "8.8.4.4"]
}
```

保存后，重启 Docker Desktop。

---

## 🧪 验证配置

打开 PowerShell，运行：

```powershell
# 查看 Docker 信息
docker info

# 查找 "Registry Mirrors" 部分，应该显示配置的镜像源
```

输出应该包含：
```
Registry Mirrors:
  https://docker.mirrors.ustc.edu.cn/
  https://hub-mirror.c.163.com/
  ...
```

---

## 🔄 测试拉取镜像

```powershell
# 测试拉取一个小镜像
docker pull hello-world

# 如果成功，测试拉取 Node 镜像
docker pull node:18-alpine
```

如果成功下载，说明配置生效！

---

## 📦 重新构建项目

配置好镜像源后，重新构建：

```powershell
cd d:\1_AAA_HJB\MCTS\alpha-pile\cp_sat_pile

# 清理旧的构建缓存
docker-compose down
docker builder prune -af

# 重新构建
docker-compose build --no-cache

# 启动
docker-compose up
```

---

## 🌐 国内可用的 Docker 镜像源

| 镜像源 | 地址 | 速度 |
|--------|------|------|
| 中国科技大学 | https://docker.mirrors.ustc.edu.cn | ⭐⭐⭐⭐⭐ |
| 网易 | https://hub-mirror.c.163.com | ⭐⭐⭐⭐ |
| 百度云 | https://mirror.baidubce.com | ⭐⭐⭐⭐ |
| 南京大学 | https://docker.nju.edu.cn | ⭐⭐⭐⭐ |
| 阿里云（需注册） | https://你的ID.mirror.aliyuncs.com | ⭐⭐⭐⭐⭐ |

### 如何获取阿里云镜像加速器（最快）：

1. 访问：https://cr.console.aliyun.com/cn-hangzhou/instances/mirrors
2. 登录阿里云账号（免费）
3. 复制你的专属加速地址，如：`https://abcd1234.mirror.aliyuncs.com`
4. 添加到 `registry-mirrors` 列表的第一位

---

## ⚠️ 常见问题

### Q1: 配置后仍然连接失败？

**解决方案**：
1. 确保完全重启了 Docker Desktop
2. 尝试更换其他镜像源
3. 检查防火墙是否拦截

### Q2: 所有镜像源都很慢？

**解决方案**：
1. 使用阿里云个人镜像加速器（最快）
2. 检查本地网络连接
3. 尝试使用 VPN

### Q3: 配置文件被重置？

**解决方案**：
使用 Docker Desktop 图形界面配置，而不是手动编辑文件。

---

## 💡 其他优化建议

### 1. 增加资源限制

在 Docker Desktop Settings → Resources 中：
- **CPUs**: 设置为 2-4 核
- **Memory**: 设置为 4-8 GB
- **Disk**: 确保至少 20 GB 可用空间

### 2. 启用 BuildKit

在 PowerShell 中设置环境变量：
```powershell
$env:DOCKER_BUILDKIT=1
$env:COMPOSE_DOCKER_CLI_BUILD=1
```

### 3. 使用代理（如果有）

如果你有代理服务器，在 Docker Desktop → Settings → Resources → Proxies 中配置。

---

## 🎯 完整操作流程

```powershell
# 1. 配置镜像源（使用 Docker Desktop 图形界面）
# 2. 重启 Docker Desktop
# 3. 验证配置
docker info | Select-String "Registry Mirrors"

# 4. 清理旧缓存
cd d:\1_AAA_HJB\MCTS\alpha-pile\cp_sat_pile
docker-compose down
docker builder prune -af

# 5. 重新构建
docker-compose build --no-cache --pull

# 6. 启动服务
docker-compose up
```

---

**配置完成后，构建速度应该会大幅提升！** 🚀

如果还有问题，请告诉我具体的错误信息。
