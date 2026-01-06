#!/usr/bin/env python3
"""
函数级训练样本生成器
根据函数文档生成Q&A格式的训练样本
"""

import os
import argparse
import json

# 导入日志模块
from . import logger

# 导入工具函数
from .utils import load_ai_config, call_ai_api, save_ai_response

from .generate_function_docs import read_function_content, find_function_info

def read_function_doc(project_name, output_dir, file_path, function_name):
    """读取函数文档文件"""
    # 构建文档文件路径
    function_doc_path = os.path.join(output_dir, project_name, "functions", file_path, f"{function_name}_doc.md")
    
    try:
        with open(function_doc_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"错误: 找不到函数文档文件 {function_doc_path}")
        return None
    except Exception as e:
        logger.error(f"错误: 读取函数文档文件失败 {function_doc_path}: {e}")
        return None


def generate_function_train_prompt(function_doc_content, function_source_code=None):
    """生成函数训练样本提示词"""
    # 读取提示词模板
    try:
        # 首先尝试在当前目录查找模板文件
        with open("function_train_prompt_template.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        # 如果在当前目录找不到，尝试在codedatasetmaker目录中查找
        try:
            template_path = os.path.join(os.path.dirname(__file__), "function_train_prompt_template.txt")
            with open(template_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            # 如果都找不到，报错退出
            logger.error("错误: 找不到函数训练样本提示词模板文件 'function_train_prompt_template.txt'")
            logger.error("请确保模板文件存在于当前目录或 codedatasetmaker 目录中")
            raise
    
    # 填充模板
    prompt = prompt_template.format(
        function_doc_content=function_doc_content if function_doc_content else "// 无法获取函数文档内容",
        function_source_code=function_source_code if function_source_code else "// 无法获取函数源代码"
    )
    
    return prompt


def generate_single_function_train(project_path, output_dir, project_name, file_path, function_name, file_info=None, ai_config=None):
    """生成单个函数的训练样本"""
    
    # 构建输出目录结构
    train_output_dir = os.path.join(output_dir, project_name, "train", "functions", file_path)
    os.makedirs(train_output_dir, exist_ok=True)

    train_file_path = os.path.join(train_output_dir, f"{function_name}_train.md")
    if os.path.exists(train_file_path):
        logger.info(f"函数训练样本已存在，跳过生成：{train_file_path}")
        return
    
    # 读取现有的函数文档文件
    function_doc_content = read_function_doc(project_name, output_dir, file_path, function_name)
    if function_doc_content is None:
        return None
    
    # 读取函数源代码
    function_source_code = None
    try:
        # 如果提供了file_info，则使用它来查找函数信息
        if file_info:
            # 查找函数信息
            file_data, func_info = find_function_info(f"{file_path}:{function_name}", file_info)
            if func_info:
                # 读取函数源代码
                function_source_code = read_function_content(file_path, func_info["start_line"], func_info["end_line"], project_path)
        else:
            # 否则读取file_info.json以获取函数的行号信息
            file_info_path = os.path.join(output_dir, project_name, "file_info.json")
            if os.path.exists(file_info_path):
                with open(file_info_path, 'r', encoding='utf-8') as f:
                    file_info = json.load(f)
                
                # 查找函数信息
                file_data, func_info = find_function_info(f"{file_path}:{function_name}", file_info)
                if func_info:
                    # 读取函数源代码
                    function_source_code = read_function_content(file_path, func_info["start_line"], func_info["end_line"], project_path)
    except Exception as e:
        logger.warning(f"读取函数 {function_name} 源代码时出错: {e}")
    
    # 生成提示词
    prompt = generate_function_train_prompt(function_doc_content, function_source_code)
    # 保存提示词到文件
    prompt_file_path = os.path.join(train_output_dir, f"{function_name}_train_prompt.txt")
    with open(prompt_file_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    
    logger.info(f"已生成函数训练样本提示词文件: {prompt_file_path}")
    
    # 如果提供了AI配置，则调用AI API生成训练样本
    if ai_config:
        logger.info(f"正在调用AI API生成函数训练样本: {function_name}")
        if ai_config.get("train_model", None):
            ai_config["model"] = ai_config.get("train_model")
            
        response = call_ai_api(prompt, ai_config)
        if response:
            # 保存AI生成的训练样本
            if save_ai_response(response, train_file_path):
                logger.info(f"已生成函数训练样本: {train_file_path}")
                return train_file_path
            else:
                logger.ai_error("AI API调用成功，但保存函数训练样本时出现问题")
        else:
            logger.ai_error(f"AI API调用失败，将仅保留函数训练样本提示词文件: {function_name}")
    
    return prompt_file_path


def read_call_graph(project_name, output_dir):
    """读取函数调用图文件"""
    call_graph_path = os.path.join(output_dir, project_name, "call_graph.json")
    
    try:
        with open(call_graph_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"错误: 找不到函数调用图文件 {call_graph_path}")
        return None
    except Exception as e:
        logger.error(f"错误: 读取函数调用图文件失败 {call_graph_path}: {e}")
        return None


def generate_all_functions_train(project_path, output_dir, project_name, ai_config=None):
    """生成所有函数的训练样本"""
    # 读取函数调用图
    call_graph = read_call_graph(project_name, output_dir)
    if call_graph is None:
        return
    
    # 读取file_info.json
    file_info = None
    try:
        file_info_path = os.path.join(output_dir, project_name, "file_info.json")
        if os.path.exists(file_info_path):
            with open(file_info_path, 'r', encoding='utf-8') as f:
                file_info = json.load(f)
    except Exception as e:
        logger.warning(f"读取file_info.json时出错: {e}")
    
    # 获取所有函数名称
    function_names = list(call_graph.keys())
    
    logger.info(f"开始生成 {len(function_names)} 个函数的训练样本")
    
    generated_files = []
    for function_name in function_names:
        try:
            # 解析函数名称获取文件路径和函数名
            parts = function_name.split(":")
            if len(parts) >= 2:
                file_path = parts[0]
                func_name = parts[1]
                result = generate_single_function_train(project_path, output_dir, project_name, file_path, func_name, file_info, ai_config)
                if result:
                    generated_files.append(result)
        except Exception as e:
            logger.error(f"生成函数 {function_name} 的训练样本时出错: {e}")
            continue
    
    logger.info(f"完成生成 {len(generated_files)} 个函数的训练样本")
    return generated_files


def main():
    parser = argparse.ArgumentParser(description="函数级训练样本生成器")
    parser.add_argument("project_path", help="项目路径")
    parser.add_argument("--output", "-o", help="输出目录路径")
    parser.add_argument("--ai-config", "-c", default="ai_config.json", help="AI配置文件路径")
    parser.add_argument("--function", "-f", help="指定生成特定函数的训练样本（格式：文件路径:函数名）")
    
    args = parser.parse_args()
    
    # 计算项目名称和相关路径
    project_name = os.path.basename(os.path.abspath(args.project_path))
    if args.output:
        output_dir = args.output
    else:
        output_dir = "output"
    
    # 加载AI配置
    ai_config = load_ai_config(args.ai_config)
    
    # 生成函数训练样本
    try:
        if args.function:
            # 解析函数名称获取文件路径和函数名
            parts = args.function.split(":")
            if len(parts) >= 2:
                file_path = parts[0]
                func_name = parts[1]
                # 读取file_info.json
                file_info = None
                try:
                    file_info_path = os.path.join(output_dir, project_name, "file_info.json")
                    if os.path.exists(file_info_path):
                        with open(file_info_path, 'r', encoding='utf-8') as f:
                            file_info = json.load(f)
                except Exception as e:
                    logger.warning(f"读取file_info.json时出错: {e}")
                # 生成特定函数的训练样本
                generate_single_function_train(args.project_path, output_dir, project_name, file_path, func_name, file_info, ai_config)
            else:
                logger.error("错误: 函数名称格式不正确，应为 '文件路径:函数名'")
        else:
            # 生成所有函数的训练样本
            generate_all_functions_train(args.project_path, output_dir, project_name, ai_config)
    except Exception as e:
        logger.error(f"生成函数训练样本时出错: {e}")


if __name__ == "__main__":
    main()
