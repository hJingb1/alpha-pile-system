@echo off
chcp 65001 >nul
echo ========================================
echo 🧪 前端本地构建测试
echo ========================================
echo.

cd alpha-pile-fronted

echo 📋 步骤 1/4: 配置 npm 镜像源...
call npm config set registry https://registry.npmmirror.com
echo ✅ 镜像源已配置
echo.

echo 📦 步骤 2/4: 清理旧的依赖...
if exist node_modules (
    echo 发现旧的 node_modules，正在删除...
    rmdir /s /q node_modules
)
if exist dist (
    echo 发现旧的 dist，正在删除...
    rmdir /s /q dist
)
echo ✅ 清理完成
echo.

echo 📥 步骤 3/4: 安装依赖 (可能需要 5-10 分钟)...
call npm install --legacy-peer-deps
if errorlevel 1 (
    echo ❌ 依赖安装失败！
    echo.
    echo 💡 建议：
    echo 1. 检查网络连接
    echo 2. 尝试使用 VPN
    echo 3. 手动运行: npm install --legacy-peer-deps
    pause
    exit /b 1
)
echo ✅ 依赖安装成功
echo.

echo 🔨 步骤 4/4: 构建生产版本...
call npm run build
if errorlevel 1 (
    echo ❌ 构建失败！
    echo.
    echo 查看上方错误信息，可能是：
    echo 1. TypeScript 类型错误
    echo 2. 依赖版本冲突
    echo 3. 内存不足
    pause
    exit /b 1
)
echo ✅ 构建成功！
echo.

echo ========================================
echo ✅ 前端构建完成！
echo ========================================
echo.
echo 📂 构建产物位置: alpha-pile-fronted\dist
echo 📊 产物大小:
dir dist /s | find "File(s)"
echo.
echo 下一步:
echo 1. 可以使用 "npm run preview" 预览构建结果
echo 2. 或者使用 Docker 部署 dist 目录
echo.
pause

cd ..
