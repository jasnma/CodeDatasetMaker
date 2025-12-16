#!/usr/bin/env python3
"""
示例脚本：演示如何使用AI配置文件和生成的提示词调用AI API
"""

import json
import os
import argparse


def load_ai_config(config_path="ai_config.json"):
    """加载AI配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"警告: 找不到配置文件 {config_path}，使用默认配置")
        return {
            "api_key": "your_api_key_here",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000
        }
    except json.JSONDecodeError as e:
        print(f"错误: JSON解析失败 {config_path}: {e}")
        return None


def load_prompt_file(prompt_path):
    """加载提示词文件"""
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"错误: 找不到提示词文件 {prompt_path}")
        return None
    except Exception as e:
        print(f"错误: 读取提示词文件失败 {prompt_path}: {e}")
        return None


def call_ai_api(prompt, config):
    """调用AI API的示例函数（实际使用时需要替换为真实的API调用）"""
    print("=== AI API 调用示例 ===")
    print(f"基础URL: {config.get('base_url', 'https://api.openai.com/v1')}")
    print(f"模型: {config['model']}")
    print(f"温度: {config['temperature']}")
    print(f"最大令牌数: {config['max_tokens']}")
    print("\n提示词内容预览（前500个字符）:")
    print(prompt[:500] + ("..." if len(prompt) > 500 else ""))
    print("\n=== 实际使用时，请替换此函数为真实的AI API调用 ===")
    
    # 这里应该是实际的API调用代码，例如使用requests库调用OpenAI API
    # 示例伪代码：
    # import requests
    # base_url = config.get("base_url", "https://api.openai.com/v1")
    # headers = {
    #     "Authorization": f"Bearer {config['api_key']}",
    #     "Content-Type": "application/json"
    # }
    # data = {
    #     "model": config["model"],
    #     "messages": [{"role": "user", "content": prompt}],
    #     "temperature": config["temperature"],
    #     "max_tokens": config["max_tokens"]
    # }
    # response = requests.post(f"{base_url}/chat/completions", headers=headers, json=data)
    # return response.json()


def main():
    parser = argparse.ArgumentParser(description="示例脚本：演示如何使用AI配置文件和生成的提示词调用AI API")
    parser.add_argument("prompt_file", help="提示词文件路径")
    parser.add_argument("--config", "-c", default="ai_config.json", help="AI配置文件路径")
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_ai_config(args.config)
    if config is None:
        return
    
    # 加载提示词
    prompt = load_prompt_file(args.prompt_file)
    if prompt is None:
        return
    
    # 调用AI API
    call_ai_api(prompt, config)


if __name__ == "__main__":
    main()
