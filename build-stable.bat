@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 Alpha Pile 稳定构建脚本
echo ========================================
echo.

echo 📋 检查环境...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker 未安装或未启动！
    echo 请确保 Docker Desktop 正在运行
    pause
    exit /b 1
)
echo ✅ Docker 已就绪
echo.

echo 🧹 步骤 1/5: 停止旧容器...
docker-compose down
echo.

echo 🗑️ 步骤 2/5: 清理构建缓存...
docker builder prune -af
echo.

echo 📦 步骤 3/5: 仅构建后端 (通常比较稳定)...
docker-compose build backend
if errorlevel 1 (
    echo ❌ 后端构建失败！
    pause
    exit /b 1
)
echo ✅ 后端构建成功
echo.

echo 📦 步骤 4/5: 构建前端 (使用淘宝 npm 镜像)...
docker-compose build --no-cache frontend
if errorlevel 1 (
    echo ❌ 前端构建失败！
    echo.
    echo 💡 建议：
    echo 1. 检查网络连接
    echo 2. 尝试重新运行此脚本
    echo 3. 如果多次失败，尝试本地构建方案 (见下方说明)
    pause
    exit /b 1
)
echo ✅ 前端构建成功
echo.

echo 🚀 步骤 5/5: 启动服务...
docker-compose up -d

echo.
echo ========================================
echo ✅ 构建完成！
echo ========================================
echo.
echo 🌐 访问地址: http://localhost
echo 📊 查看日志: docker-compose logs -f
echo 🛑 停止服务: docker-compose down
echo.
echo 按任意键查看实时日志...
pause >nul
docker-compose logs -f
