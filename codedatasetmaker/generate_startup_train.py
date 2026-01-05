#!/usr/bin/env python3
"""
启动流程训练样本生成器
根据startup_doc.md生成Q&A格式的训练样本
"""

import os
import argparse
import json

# 导入日志模块
from . import logger

# 导入工具函数
from .utils import load_ai_config, call_ai_api, save_ai_response


def read_startup_doc(project_name, output_dir):
    """读取startup_doc.md文件"""
    startup_doc_path = os.path.join(output_dir, project_name, "startup_doc.md")
    
    try:
        with open(startup_doc_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"错误: 找不到启动流程文档文件 {startup_doc_path}")
        return None
    except Exception as e:
        logger.error(f"错误: 读取启动流程文档文件失败 {startup_doc_path}: {e}")
        return None


def generate_startup_train_prompt(startup_doc_content):
    """生成训练样本提示词"""
    # 读取提示词模板
    try:
        # 首先尝试在当前目录查找模板文件
        with open("startup_train_prompt_template.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        # 如果在当前目录找不到，尝试在codedatasetmaker目录中查找
        try:
            template_path = os.path.join(os.path.dirname(__file__), "startup_train_prompt_template.txt")
            with open(template_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            # 如果都找不到，报错退出
            logger.error("错误: 找不到启动流程训练样本提示词模板文件 'startup_train_prompt_template.txt'")
            logger.error("请确保模板文件存在于当前目录或 codedatasetmaker 目录中")
            raise
    
    # 填充模板
    prompt = prompt_template.format(
        startup_doc_content=startup_doc_content if startup_doc_content else "// 无法获取启动流程文档内容"
    )
    
    return prompt


def generate_startup_train(project_path, output_dir, project_name, ai_config=None):
    """生成启动流程训练样本"""
    # 读取现有的startup_doc.md文件
    startup_doc_content = read_startup_doc(project_name, output_dir)
    if startup_doc_content is None:
        return
    
    # 生成提示词
    prompt = generate_startup_train_prompt(startup_doc_content)
    
    # 构建输出目录结构
    train_output_dir = os.path.join(output_dir, project_name, "train")
    os.makedirs(train_output_dir, exist_ok=True)
    
    # 保存提示词到文件
    prompt_file_path = os.path.join(train_output_dir, "startup_train_prompt.txt")
    with open(prompt_file_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    
    logger.info(f"已生成启动流程训练样本提示词文件: {prompt_file_path}")
    
    # 如果提供了AI配置，则调用AI API生成训练样本
    if ai_config:
        logger.info("正在调用AI API生成启动流程训练样本...")
        if ai_config.get("train_model", None):
            ai_config["model"] = ai_config.get("train_model")
            
        response = call_ai_api(prompt, ai_config)
        if response:
            # 保存AI生成的训练样本
            train_file_path = os.path.join(train_output_dir, "startup_train.md")
            if save_ai_response(response, train_file_path):
                logger.info(f"已生成启动流程训练样本: {train_file_path}")
            else:
                logger.ai_error("AI API调用成功，但保存启动流程训练样本时出现问题")
        else:
            logger.ai_error("AI API调用失败，将仅保留启动流程训练样本提示词文件")
    
    return prompt_file_path


def main():
    parser = argparse.ArgumentParser(description="启动流程训练样本生成器")
    parser.add_argument("project_path", help="项目路径")
    parser.add_argument("--output", "-o", help="输出目录路径")
    parser.add_argument("--ai-config", "-c", default="ai_config.json", help="AI配置文件路径")
    
    args = parser.parse_args()
    
    # 计算项目名称和相关路径
    project_name = os.path.basename(os.path.abspath(args.project_path))
    if args.output:
        output_dir = args.output
    else:
        output_dir = "output"
    
    # 加载AI配置
    ai_config = load_ai_config(args.ai_config)
    
    # 生成启动流程训练样本
    try:
        generate_startup_train(args.project_path, output_dir, project_name, ai_config)
    except Exception as e:
        logger.error(f"生成启动流程训练样本时出错: {e}")


if __name__ == "__main__":
    main()
