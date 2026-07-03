#!/bin/bash

echo "🎴 动漫卡牌对战游戏 - 启动脚本"
echo "=================================="

# 检查后端依赖
echo "📦 检查后端依赖..."
cd backend
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

# 检查并构建前端
echo "📦 检查前端..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi
echo "构建前端..."
npm run build
cd ../backend
cd ..

echo ""
echo "🚀 启动后端服务 (端口 8000)..."

# 启动后端（包含前端静态文件）
cd backend
source venv/bin/activate
python main.py

echo ""
echo "✅ 服务启动完成！"
echo "🌐 访问地址: http://localhost:8000"
