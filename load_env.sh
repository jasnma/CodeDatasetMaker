#!/bin/bash

# 脚本名称: load_env.sh
# 功能: 加载 .env 文件中的环境变量

echo "=== 环境变量加载脚本 ==="

# 检查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo "错误: 找不到 .env 文件"
    echo "请确保在项目根目录中有一个 .env 文件"
    exit 1
fi

echo "找到 .env 文件，正在加载环境变量..."

# 使用 set -a 使变量自动导出到环境中
set -a
source .env
set +a

echo "环境变量加载完成!"

# 验证关键环境变量是否已设置
if [ -n "$OPENAI_API_KEY" ]; then
    echo "✓ OPENAI_API_KEY 已设置"
    echo "  长度: ${#OPENAI_API_KEY} 字符"
    # 显示前8位和后4位，隐藏中间部分
    if [ ${#OPENAI_API_KEY} -gt 12 ]; then
        prefix=${OPENAI_API_KEY:0:8}
        suffix=${OPENAI_API_KEY: -4}
        echo "  值: ${prefix}...${suffix}"
    fi
else
    echo "⚠ OPENAI_API_KEY 未设置"
fi

echo ""
echo "使用方法:"
echo "1. 直接运行此脚本加载环境变量:"
echo "   ./load_env.sh"
echo ""
echo "2. 在当前shell中加载环境变量:"
echo "   source load_env.sh"
echo ""
echo "3. 加载环境变量后运行项目:"
echo "   source load_env.sh && python3 main.py test_project --mode doc"
