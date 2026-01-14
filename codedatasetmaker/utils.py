#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工具函数模块
包含项目中通用的工具函数
"""

import json
import os
from openai import OpenAI, AsyncOpenAI
from openai import APIError, APIConnectionError, RateLimitError

# 导入日志模块
from . import logger


def load_json_file(file_path):
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"错误: 找不到文件 {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"错误: JSON解析失败 {file_path}: {e}")
        return None


def load_ai_config(config_path="ai_config.json"):
    """加载AI配置文件"""
    
    # 首先尝试从环境变量获取API密钥
    api_key = os.environ.get("OPENAI_API_KEY")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 如果环境变量中有API密钥，则使用环境变量中的值
        if api_key:
            config["api_key"] = api_key
            
        return config
    except FileNotFoundError:
        logger.warning(f"警告: 找不到配置文件 {config_path}，将仅生成提示词文件")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"错误: JSON解析失败 {config_path}: {e}")
        return None


def get_ignore_dirs(config):
    """获取忽略目录列表"""
    if config is None:
        return []
    
    ignore_dirs = config.get("ignore_dirs", [])
    
    return ignore_dirs


async def async_call_ai_api_stream(
    prompt,
    config,
    semaphore,
    stream_printer=None,   # 可选：实时输出函数
):
    """
    异步 + 流式 AI 调用
    - 防止网关超时
    - 支持实时输出
    - 支持并发
    """

    api_key = config.get("api_key")
    base_url = config.get("base_url", "https://api.openai.com/v1")
    model = config.get("model")
    temperature = config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens", 2000)

    if not api_key or api_key == "your_api_key_here":
        logger.warning("缺少 api_key，跳过 AI 调用")
        return None

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    messages = [{"role": "user", "content": prompt}]

    full_response = ""

    async with semaphore:
        try:
            stream = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                if not delta or not delta.content:
                    continue

                token = delta.content
                full_response += token

                # 🔥 实时输出
                if stream_printer:
                    stream_printer(token)

            return {
                "choices": [
                    {"message": {"content": full_response}}
                ]
            }

        except RateLimitError as e:
            logger.ai_error(f"限流错误: {e}")
        except APIConnectionError as e:
            logger.ai_error(f"连接失败: {e}")
        except APIError as e:
            logger.ai_error(f"API错误: {e}")
        except Exception as e:
            logger.ai_error(f"未知错误: {e}")

    return None


def call_ai_api(prompt, config):
    """使用OpenAI SDK调用AI API并流式输出响应"""
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
    if not api_key or api_key == "your_api_key_here":
        logger.warning("警告: 配置文件中缺少有效的api_key，将仅生成提示词文件")
        return None
    
    # 创建OpenAI客户端
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    # 构造消息
    messages = [{"role": "user", "content": prompt}]
    
    # 发送请求并流式输出响应
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stream=True  # 启用流式响应
        )
        
        # 流式输出响应
        full_response = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)  # 实时输出到控制台
                full_response += content
        
        print()  # 添加换行
        return {"choices": [{"message": {"content": full_response}}]}
        
    except RateLimitError as e:
        logger.ai_error(f"请求频率过高: {e}")
        return None
    except APIConnectionError as e:
        logger.ai_error(f"API连接失败: {e}")
        return None
    except APIError as e:
        logger.ai_error(f"API返回错误: {e}")
        return None
    except Exception as e:
        logger.ai_error(f"API请求失败: {e}")
        return None


def save_ai_response(response, output_path):
    """保存AI响应到文件"""
    if response is None:
        return False
    
    try:
        # 保存AI生成的文档
        if "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0]["message"]["content"]
            # 去除头部的不可见字符，包括BOM和其他Unicode空白字符
            content = content.strip("\u200B\u200C\u200D\u2060\uFEFF")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        else:
            # 保存原始响应
            with open(output_path + ".raw.json", 'w', encoding='utf-8') as f:
                json.dump(response, f, ensure_ascii=False, indent=2)
            return False
    except Exception as e:
        logger.error(f"错误: 保存AI响应失败: {e}")
        return False
