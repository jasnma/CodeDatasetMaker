#!/usr/bin/env python3
"""
模块级训练样本生成器
根据模块文档生成Q&A格式的训练样本
"""

import os
import argparse
import json

# 导入日志模块
from . import logger

# 导入工具函数
from .utils import load_ai_config, call_ai_api, save_ai_response


def read_module_doc(project_name, output_dir, module_name):
    """读取模块文档文件"""
    # 首先检查output_dir是否直接包含modules目录
    modules_dir = os.path.join(output_dir, "modules")
    if not os.path.exists(modules_dir):
        # output_dir是根输出目录，modules目录在子目录中
        modules_dir = os.path.join(output_dir, project_name, "modules")
    
    module_doc_path = os.path.join(modules_dir, f"{module_name}_doc.md")
    
    try:
        with open(module_doc_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"错误: 找不到模块文档文件 {module_doc_path}")
        return None
    except Exception as e:
        logger.error(f"错误: 读取模块文档文件失败 {module_doc_path}: {e}")
        return None


def generate_module_train_prompt(module_doc_content):
    """生成模块训练样本提示词"""
    # 读取提示词模板
    try:
        # 首先尝试在当前目录查找模板文件
        with open("module_train_prompt_template.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        # 如果在当前目录找不到，尝试在codedatasetmaker目录中查找
        try:
            template_path = os.path.join(os.path.dirname(__file__), "module_train_prompt_template.txt")
            with open(template_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            # 如果都找不到，报错退出
            logger.error("错误: 找不到模块训练样本提示词模板文件 'module_train_prompt_template.txt'")
            logger.error("请确保模板文件存在于当前目录或 codedatasetmaker 目录中")
            raise
    
    # 填充模板
    prompt = prompt_template.format(
        module_doc_content=module_doc_content if module_doc_content else "// 无法获取模块文档内容"
    )
    
    return prompt


def generate_single_module_train(project_path, output_dir, project_name, module_name, ai_config=None):
    """生成单个模块的训练样本"""
    
    # 构建输出目录结构
    train_output_dir = os.path.join(output_dir, project_name, "train", "modules")
    os.makedirs(train_output_dir, exist_ok=True)

    train_file_path = os.path.join(train_output_dir, f"{module_name}_train.md")
    if os.path.exists(train_file_path):
        logger.info(f"模块训练样本已存在，跳过生成：{train_file_path}")
        return
    
    # 读取现有的模块文档文件
    module_doc_content = read_module_doc(project_name, output_dir, module_name)
    if module_doc_content is None:
        return None
    
    # 生成提示词
    prompt = generate_module_train_prompt(module_doc_content)
    # 保存提示词到文件
    prompt_file_path = os.path.join(train_output_dir, f"{module_name}_train_prompt.txt")
    with open(prompt_file_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    
    logger.info(f"已生成模块训练样本提示词文件: {prompt_file_path}")
    
    # 如果提供了AI配置，则调用AI API生成训练样本
    if ai_config:
        logger.info(f"正在调用AI API生成模块训练样本: {module_name}")
        if ai_config.get("train_model", None):
            ai_config["model"] = ai_config.get("train_model")
            
        response = call_ai_api(prompt, ai_config)
        if response:
            # 保存AI生成的训练样本
            if save_ai_response(response, train_file_path):
                logger.info(f"已生成模块训练样本: {train_file_path}")
                return train_file_path
            else:
                logger.ai_error("AI API调用成功，但保存模块训练样本时出现问题")
        else:
            logger.ai_error(f"AI API调用失败，将仅保留模块训练样本提示词文件: {module_name}")
    
    return prompt_file_path


def read_module_structure(project_name, output_dir):
    """读取模块结构文件"""
    # 首先检查output_dir是否直接包含module_structure.json
    module_structure_path = os.path.join(output_dir, "module_structure.json")
    if not os.path.exists(module_structure_path):
        # output_dir是根输出目录，module_structure.json在子目录中
        module_structure_path = os.path.join(output_dir, project_name, "module_structure.json")
    
    try:
        with open(module_structure_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"错误: 找不到模块结构文件 {module_structure_path}")
        return None
    except Exception as e:
        logger.error(f"错误: 读取模块结构文件失败 {module_structure_path}: {e}")
        return None


def generate_all_modules_train(project_path, output_dir, project_name, ai_config=None):
    """生成所有模块的训练样本"""
    # 读取模块结构
    module_structure = read_module_structure(project_name, output_dir)
    if module_structure is None:
        return
    
    # 获取所有模块名称
    module_names = list(module_structure.keys())
    
    logger.info(f"开始生成 {len(module_names)} 个模块的训练样本")
    
    generated_files = []
    for module_name in module_names:
        try:
            result = generate_single_module_train(project_path, output_dir, project_name, module_name, ai_config)
            if result:
                generated_files.append(result)
        except Exception as e:
            logger.error(f"生成模块 {module_name} 的训练样本时出错: {e}")
            continue
    
    logger.info(f"完成生成 {len(generated_files)} 个模块的训练样本")
    return generated_files


def main():
    parser = argparse.ArgumentParser(description="模块级训练样本生成器")
    parser.add_argument("project_path", help="项目路径")
    parser.add_argument("--output", "-o", help="输出目录路径")
    parser.add_argument("--ai-config", "-c", default="ai_config.json", help="AI配置文件路径")
    parser.add_argument("--module", "-m", help="指定生成特定模块的训练样本（可选）")
    
    args = parser.parse_args()
    
    # 计算项目名称和相关路径
    project_name = os.path.basename(os.path.abspath(args.project_path))
    if args.output:
        output_dir = args.output
    else:
        output_dir = "output"
    
    # 加载AI配置
    ai_config = load_ai_config(args.ai_config)
    
    # 生成模块训练样本
    try:
        if args.module:
            # 生成特定模块的训练样本
            generate_single_module_train(args.project_path, output_dir, project_name, args.module, ai_config)
        else:
            # 生成所有模块的训练样本
            generate_all_modules_train(args.project_path, output_dir, project_name, ai_config)
    except Exception as e:
        logger.error(f"生成模块训练样本时出错: {e}")


if __name__ == "__main__":
    main()
