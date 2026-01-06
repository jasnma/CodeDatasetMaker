#!/usr/bin/env python3
"""
宏定义级训练样本生成器
根据宏定义文档生成Q&A格式的训练样本
"""

import os
import argparse
import json

# 导入日志模块
from . import logger

# 导入工具函数
from .utils import load_ai_config, call_ai_api, save_ai_response, get_ignore_dirs

def read_macro_doc(project_name, output_dir, defined_in, macro_name):
    """读取宏定义文档文件"""
    # 清理宏名称中的特殊字符
    clean_macro_name = macro_name.replace("(", "_").replace(")", "_").replace(",", "_").replace(" ", "_")
    
    # 移除文件扩展名，创建目录结构
    defined_in_no_ext = os.path.splitext(defined_in)[0]
    
    # 构建文档文件路径
    macro_doc_path = os.path.join(output_dir, project_name, "macros", defined_in_no_ext, f"{clean_macro_name}_doc.md")
    
    try:
        with open(macro_doc_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"错误: 找不到宏定义文档文件 {macro_doc_path}")
        return None
    except Exception as e:
        logger.error(f"错误: 读取宏定义文档文件失败 {macro_doc_path}: {e}")
        return None


def generate_macro_train_prompt(macro_doc_content, macro_source_code=None):
    """生成宏定义训练样本提示词"""
    # 读取提示词模板
    try:
        # 首先尝试在当前目录查找模板文件
        with open("macro_train_prompt_template.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        # 如果在当前目录找不到，尝试在codedatasetmaker目录中查找
        try:
            template_path = os.path.join(os.path.dirname(__file__), "macro_train_prompt_template.txt")
            with open(template_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            # 如果都找不到，报错退出
            logger.error("错误: 找不到宏定义训练样本提示词模板文件 'macro_train_prompt_template.txt'")
            logger.error("请确保模板文件存在于当前目录或 codedatasetmaker 目录中")
            raise
    
    # 填充模板
    prompt = prompt_template.format(
        macro_doc_content=macro_doc_content if macro_doc_content else "// 无法获取宏定义文档内容",
        macro_source_code=macro_source_code if macro_source_code else "// 无法获取宏定义源代码"
    )
    
    return prompt


def generate_single_macro_train(project_path, output_dir, project_name, defined_in, macro_name, macro_info=None, ai_config=None):
    """生成单个宏定义的训练样本"""
    
    # 移除文件扩展名，创建目录结构
    defined_in_no_ext = os.path.splitext(defined_in)[0]
    
    # 构建输出目录结构
    train_output_dir = os.path.join(output_dir, project_name, "train", "macros", defined_in_no_ext)
    os.makedirs(train_output_dir, exist_ok=True)

    # 清理宏名称中的特殊字符
    clean_macro_name = macro_name.replace("(", "_").replace(")", "_").replace(",", "_").replace(" ", "_")
    
    train_file_path = os.path.join(train_output_dir, f"{clean_macro_name}_train.md")
    if os.path.exists(train_file_path):
        logger.info(f"宏定义训练样本已存在，跳过生成：{train_file_path}")
        return
    
    # 读取现有的宏定义文档文件
    macro_doc_content = read_macro_doc(project_name, output_dir, defined_in, macro_name)
    if macro_doc_content is None:
        return None
    
    # 从macro_info中读取宏定义源代码
    macro_source_code = None
    if macro_info:
        # 查找匹配的宏定义
        for macro_item in macro_info:
            # 检查宏名称和定义文件是否匹配
            # 处理函数式宏名称的不同表示方式
            item_macro_name = macro_item.get("macro", "")
            item_defined_in = macro_item.get("defined_in", "")
            
            # 检查是否完全匹配
            if item_macro_name == macro_name and item_defined_in == defined_in:
                # 构造宏定义源代码
                content = macro_item.get("content", "")
                if content:
                    macro_source_code = f"#define {macro_name} {content}"
                else:
                    macro_source_code = f"#define {macro_name}"
                break
            else:
                logger.debug(f"宏定义不匹配: '{item_macro_name}' != '{macro_name}' or '{item_defined_in}' != '{defined_in}'")
    else:
        logger.warning("无法获取macro_info")
        macro_source_code = "// 无法获取宏定义源代码"
    
    # 生成提示词
    prompt = generate_macro_train_prompt(macro_doc_content, macro_source_code)
    # 保存提示词到文件
    prompt_file_path = os.path.join(train_output_dir, f"{clean_macro_name}_train_prompt.txt")
    with open(prompt_file_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    
    logger.info(f"已生成宏定义训练样本提示词文件: {prompt_file_path}")
    
    # 如果提供了AI配置，则调用AI API生成训练样本
    if ai_config:
        logger.info(f"正在调用AI API生成宏定义训练样本: {macro_name}")
        if ai_config.get("train_model", None):
            ai_config["model"] = ai_config.get("train_model")
            
        response = call_ai_api(prompt, ai_config)
        if response:
            # 保存AI生成的训练样本
            if save_ai_response(response, train_file_path):
                logger.info(f"已生成宏定义训练样本: {train_file_path}")
                return train_file_path
            else:
                logger.ai_error("AI API调用成功，但保存宏定义训练样本时出现问题")
        else:
            logger.ai_error(f"AI API调用失败，将仅保留宏定义训练样本提示词文件: {macro_name}")
    
    return prompt_file_path


def read_macro_definition_from_source(project_path, defined_in, macro_name):
    """从源文件中读取宏定义"""
    try:
        # 构建完整的文件路径
        file_path = os.path.join(project_path, defined_in)

        # 如果文件不存在，返回None
        if not os.path.exists(file_path):
            logger.warning(f"警告: 找不到源文件 {file_path}")
            return None

        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # 查找宏定义的位置
        macro_line_index = -1
        for i, line in enumerate(lines):
            # 查找完全匹配宏定义的行
            if line.strip().startswith(f"#define {macro_name}") or line.strip() == f"#define {macro_name}":
                macro_line_index = i
                break
        
        if macro_line_index != -1:
            # 提取宏定义前20行和后100行
            start_line = max(0, macro_line_index - 20)
            end_line = min(len(lines), macro_line_index + 101)  # +100行，+1因为切片是左闭右开
            macro_context_lines = lines[start_line:end_line]
            macro_context = "".join(macro_context_lines)
            return macro_context
        else:
            # 如果没有找到宏定义，使用默认上下文
            macro_context = "// 无法找到宏定义位置\n" + "".join(lines[:50])  # 使用前50行作为默认上下文
            return macro_context
    except Exception as e:
        logger.error(f"读取宏定义文件 {file_path} 时出错: {e}")
        return "// 无法读取文件内容"


def read_macro_info(project_name, output_dir):
    """读取宏定义信息文件"""
    macro_info_path = os.path.join(output_dir, project_name, "macro_info.json")
    
    try:
        with open(macro_info_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"错误: 找不到宏定义信息文件 {macro_info_path}")
        return None
    except Exception as e:
        logger.error(f"错误: 读取宏定义信息文件失败 {macro_info_path}: {e}")
        return None


def generate_all_macros_train(project_path, output_dir, project_name, ai_config=None, ignore_dirs=None):
    """生成所有宏定义的训练样本"""
    # 读取宏定义信息
    macro_info = read_macro_info(project_name, output_dir)
    if macro_info is None:
        return
    
    # 获取所有宏定义名称和定义位置
    macros = [(item["macro"], item["defined_in"]) for item in macro_info if "macro" in item and "defined_in" in item]
    
    logger.info(f"开始生成宏定义的训练样本")
    
    generated_files = []
    for macro_name, defined_in in macros:
        # 检查是否应该忽略该宏定义
        if ignore_dirs and should_ignore_path(defined_in, ignore_dirs):
            logger.info(f"跳过被忽略目录中的宏定义: {macro_name}")
            continue
            
        try:
            result = generate_single_macro_train(project_path, output_dir, project_name, defined_in, macro_name, macro_info, ai_config)
            if result:
                generated_files.append(result)
        except Exception as e:
            logger.error(f"生成宏定义 {macro_name} 的训练样本时出错: {e}")
            continue
    
    logger.info(f"完成生成 {len(generated_files)} 个宏定义的训练样本")
    return generated_files


def should_ignore_path(file_path, ignore_dirs):
    """检查文件路径是否应该被忽略"""
    for ignore_dir in ignore_dirs:
        if ignore_dir in file_path:
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description="宏定义级训练样本生成器")
    parser.add_argument("project_path", help="项目路径")
    parser.add_argument("--output", "-o", help="输出目录路径")
    parser.add_argument("--ai-config", "-c", default="ai_config.json", help="AI配置文件路径")
    parser.add_argument("--macro", "-m", help="指定生成特定宏定义的训练样本（格式：宏名称:定义文件）")
    
    args = parser.parse_args()
    
    # 计算项目名称和相关路径
    project_name = os.path.basename(os.path.abspath(args.project_path))
    if args.output:
        output_dir = args.output
    else:
        output_dir = "output"
    
    # 加载AI配置
    ai_config = load_ai_config(args.ai_config)
    
    # 获取忽略目录列表
    ignore_dirs = get_ignore_dirs(ai_config) if ai_config else []
    
    # 生成宏定义训练样本
    try:
        if args.macro:
            # 解析宏定义名称和定义文件
            parts = args.macro.split(":")
            if len(parts) >= 2:
                macro_name = parts[0]
                defined_in = parts[1]
                
                # 检查是否应该忽略该宏定义
                if should_ignore_path(defined_in, ignore_dirs):
                    logger.info(f"跳过被忽略目录中的宏定义: {args.macro}")
                    return
                
                # 读取宏定义信息
                macro_info = read_macro_info(project_name, output_dir)
                # 生成特定宏定义的训练样本
                generate_single_macro_train(args.project_path, output_dir, project_name, defined_in, macro_name, macro_info, ai_config)
            else:
                logger.error("错误: 宏定义格式不正确，应为 '宏名称:定义文件'")
        else:
            # 生成所有宏定义的训练样本
            generate_all_macros_train(args.project_path, output_dir, project_name, ai_config, ignore_dirs)
    except Exception as e:
        logger.error(f"生成宏定义训练样本时出错: {e}")


if __name__ == "__main__":
    main()
