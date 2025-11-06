@echo off
echo ========================================
echo Docker 构建修复脚本
echo ========================================
echo.

echo [1/4] 停止所有容器...
docker-compose down

echo.
echo [2/4] 清理 Docker 缓存...
docker builder prune -af

echo.
echo [3/4] 删除旧的镜像...
docker-compose rm -f

echo.
echo [4/4] 重新构建 (不使用缓存)...
docker-compose build --no-cache --pull

echo.
echo ========================================
echo 清理完成！现在可以运行:
echo docker-compose up
echo ========================================
pause
