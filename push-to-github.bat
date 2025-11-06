@echo off
chcp 65001 >nul
echo ========================================
echo 📤 准备推送到 GitHub 并部署到 Railway
echo ========================================
echo.

echo 📋 步骤 1/4: 检查 Git 状态...
git status
echo.

echo 📝 步骤 2/4: 添加所有更改...
git add .
echo ✅ 文件已添加
echo.

echo 💬 步骤 3/4: 提交更改...
git commit -m "Add Railway deployment configuration and fix TypeScript errors"
if errorlevel 1 (
    echo ⚠️ 没有新的更改需要提交，或提交失败
    echo.
    echo 按任意键继续查看状态...
    pause >nul
)
echo.

echo 🚀 步骤 4/4: 推送到 GitHub...
echo.
echo ⚠️ 请确认：
echo 1. 你已经创建了 GitHub 仓库
echo 2. 你已经设置了 remote origin
echo.
echo 如果还没有设置 remote，请先运行：
echo git remote add origin https://github.com/你的用户名/仓库名.git
echo.
set /p confirm="是否继续推送? (y/n): "

if /i "%confirm%"=="y" (
    git push origin main
    if errorlevel 1 (
        echo.
        echo ❌ 推送失败！
        echo.
        echo 💡 可能的原因：
        echo 1. 还没有设置 remote origin
        echo 2. 需要先运行: git remote add origin https://github.com/用户名/仓库名.git
        echo 3. 分支名可能是 master 而不是 main，尝试: git push origin master
        echo 4. 需要 GitHub 认证（使用 Personal Access Token）
        echo.
        pause
        exit /b 1
    )
    echo.
    echo ========================================
    echo ✅ 推送成功！
    echo ========================================
    echo.
    echo 📋 下一步：在 Railway 上部署
    echo.
    echo 1. 访问: https://railway.app
    echo 2. 使用 GitHub 登录
    echo 3. 创建新项目，选择你的仓库
    echo 4. 分别部署后端和前端（见 RAILWAY_QUICK_GUIDE.md）
    echo.
) else (
    echo.
    echo ❌ 已取消推送
    echo.
)

pause
