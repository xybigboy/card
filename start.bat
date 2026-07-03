@echo off
chcp 65001 >nul
echo ========================================
echo    动漫卡牌对战游戏 - 启动脚本
echo ========================================

cd frontend
if not exist "node_modules" (
    echo [1/3] 安装前端依赖...
    npm install
)
echo [2/3] 构建前端...
call npm run build
cd ..

echo [3/3] 启动后端服务 (端口 8000)...
cd backend
call python main.py
pause
