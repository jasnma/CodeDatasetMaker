#!/usr/bin/env python3
"""
实际可用的AI调用脚本，支持私有化部署的OpenAI兼容模型
"""

import json
import os
import argparse
import requests


def load_ai_config(config_path="ai_config.json"):
    """加载AI配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: 找不到配置文件 {config_path}")
        return None
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
    """调用AI API"""
    # 获取配置参数
    api_key = config.get("api_key")
    base_url = config.get("base_url", "https://api.openai.com/v1")
    model = config.get("model", "gpt-3.5-turbo")
    temperature = config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens", 2000)
    top_p = config.get("top_p", 1.0)
    frequency_penalty = config.get("frequency_penalty", 0.0)
    presence_penalty = config.get("presence_penalty", 0.0)
    
    # 检查必要参数
    if not api_key:
        print("错误: 配置文件中缺少api_key")
        return None
    
    # 构造请求
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty
    }
    
    # 发送请求
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=300  # 5分钟超时
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"错误: API请求失败: {e}")
        return None


def save_response(response, output_path):
    """保存API响应到文件"""
    if response is None:
        return False
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"错误: 保存响应失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="调用AI API生成模块文档")
    parser.add_argument("prompt_file", help="提示词文件路径")
    parser.add_argument("-c", "--config", default="ai_config.json", help="AI配置文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径（可选，默认为stdout）")
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_ai_config(args.config)
    if config is None:
        return 1
    
    # 加载提示词
    prompt = load_prompt_file(args.prompt_file)
    if prompt is None:
        return 1
    
    # 调用AI API
    print("正在调用AI API...")
    response = call_ai_api(prompt, config)
    
    if response is None:
        return 1
    
    # 输出结果
    if args.output:
        # 保存到文件
        if save_response(response, args.output):
            print(f"响应已保存到: {args.output}")
        else:
            return 1
    else:
        # 输出到控制台
        if "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0]["message"]["content"]
            print(content)
        else:
            print("API返回了意外的响应格式:")
            print(json.dumps(response, indent=2, ensure_ascii=False))
    
    return 0


if __name__ == "__main__":
    exit(main())
