#!/usr/bin/env python3
"""
模块文档生成器
根据module_structure.json和global_var_info.json生成模块级文档
"""

import json
import os
import argparse
from collections import defaultdict, deque
from openai import OpenAI
from openai import APIError, APIConnectionError, RateLimitError

# 导入日志模块
from . import debug, info, warning, error, critical
from . import ai_debug, ai_info, ai_warning, ai_error, ai_critical
# 导入工具函数
from .utils import load_json_file, load_ai_config, call_ai_api, save_ai_response


def get_module_dependencies(module_structure):
    """获取模块依赖关系"""
    # 构建依赖图
    dependencies = {}
    reverse_dependencies = defaultdict(list)
    
    for module_name, module_info in module_structure.items():
        dependencies[module_name] = module_info.get("dependencies", [])
        for dep in module_info.get("dependencies", []):
            reverse_dependencies[dep].append(module_name)
    
    return dependencies, reverse_dependencies


def topological_sort(module_structure):
    """使用深度优先搜索进行拓扑排序"""
    dependencies, _ = get_module_dependencies(module_structure)
    
    # 初始化状态
    visited = set()
    temp_visited = set()
    sorted_modules = []
    
    def dfs_visit(node):
        """DFS访问节点"""
        # 检测循环依赖
        if node in temp_visited:
            raise Exception(f"检测到循环依赖，涉及模块: {node}")
        
        if node not in visited:
            temp_visited.add(node)
            
            # 访问所有依赖
            for dependency in dependencies.get(node, []):
                if dependency in module_structure:  # 确保依赖的模块存在
                    dfs_visit(dependency)
            
            temp_visited.remove(node)
            visited.add(node)
            sorted_modules.append(node)
    
    # 对所有模块进行DFS
    for module_name in module_structure:
        if module_name not in visited:
            dfs_visit(module_name)
    
    return sorted_modules


def get_global_vars_for_module(module_name, module_structure, global_var_info):
    """获取模块使用的全局变量"""
    module_files = module_structure[module_name]["files"]
    module_global_vars = []
    
    for var_info in global_var_info:
        # 检查全局变量是否在模块文件中定义或使用
        defined_in_module = any(file_path in var_info["defined_in"] for file_path in module_files)
        used_in_module = any(any(file_path in usage for file_path in module_files) 
                            for usage in var_info["used_in"])
        
        if defined_in_module or used_in_module:
            module_global_vars.append(var_info)
    
    return module_global_vars


def read_source_files(module_files, project_path):
    """读取模块的源代码文件"""
    source_code = ""
    
    for file_path in module_files:
        full_path = os.path.join(project_path, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                file_text = f.read()
                if (file_text):
                    source_code += f"\n// === {file_path} ===\n"
                    source_code += "```"
                    source_code += file_text
                    source_code += "```"
        except FileNotFoundError:
            source_code += f"\n// 错误: 找不到文件 {file_path}\n"
        except Exception as e:
            source_code += f"\n// 错误: 读取文件 {file_path} 失败: {e}\n"
    
    return source_code


def extract_duties_and_boundaries(doc_content):
    """从文档内容中提取'职责与边界'部分"""
    import re
    
    # 查找"职责与边界"部分
    pattern = r"### 职责与边界\s*(.*?)(?=\n### |\Z)"
    match = re.search(pattern, doc_content, re.DOTALL)
    
    if match:
        duties_and_boundaries = match.group(1).strip()
        return duties_and_boundaries
    else:
        return None


def extract_duties_and_boundaries_from_file(file_path):
    """从文件中提取'职责与边界'部分"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            doc_content = f.read()
        return extract_duties_and_boundaries(doc_content)
    except FileNotFoundError:
        error(f"文件未找到: {file_path}")
        return None
    except Exception as e:
        error(f"读取文件时出错: {e}")
        return None


def extract_duties_and_boundaries_for_module(output_dir, module_name):
    module_output_dir = os.path.join(output_dir, "modules")
    module_doc_file = os.path.join(module_output_dir, f"{module_name}_doc.md")

    return extract_duties_and_boundaries_from_file(module_doc_file)


def extract_dependencies_doc(output_dir, dependencies):
    dependencies_doc = ""

    for dependency in dependencies:
        dependency_doc = extract_duties_and_boundaries_for_module(output_dir, dependency)
        if dependency_doc:
            dependencies_doc += f"\n// === {dependency}的功能 ===\n"
            dependencies_doc += dependency_doc
            dependencies_doc += "\n"

    if not dependencies_doc:
        dependencies_doc = "无"

    return dependencies_doc


def generate_module_doc(module_name, module_structure, global_var_info, project_path, output_dir, ai_config=None):
    """生成单个模块的文档"""
    # 获取模块信息
    module_info = module_structure[module_name]
    dependencies = module_info.get("dependencies", [])

    dependencies_doc = extract_dependencies_doc(output_dir, dependencies)
    
    # 获取反向依赖
    _, reverse_dependencies = get_module_dependencies(module_structure)
    reverse_deps = reverse_dependencies.get(module_name, [])
    
    # 获取模块使用的全局变量
    module_global_vars = get_global_vars_for_module(module_name, module_structure, global_var_info)
    
    # 读取源代码
    source_code = read_source_files(module_info["files"], project_path)

    if not source_code:
        warning(f"No source code found for module: {module_name}")
        return None
    
    # 构造元数据
    metadata = {
        "dependencies": dependencies,
        "reverse_dependencies": reverse_deps,
        "global_variables": module_global_vars
    }
    
    # 读取提示词模板
    try:
        # 首先尝试在当前目录查找模板文件
        with open("module_doc_prompt_template.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        # 如果在当前目录找不到，尝试在codedatasetmaker目录中查找
        try:
            template_path = os.path.join(os.path.dirname(__file__), "module_doc_prompt_template.txt")
            with open(template_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            # 如果都找不到，报错退出
            error("错误: 找不到模块文档提示词模板文件 'module_doc_prompt_template.txt'")
            error("请确保模板文件存在于当前目录或 codedatasetmaker 目录中")
            raise
    
    # 填充模板
    prompt = prompt_template.format(
        module_name=module_name,
        source_code=source_code,
        metadata=json.dumps(metadata, indent=2, ensure_ascii=False),
        dependencies_description=dependencies_doc
    )
    
    # 创建输出目录
    module_output_dir = os.path.join(output_dir, "modules")
    os.makedirs(module_output_dir, exist_ok=True)
    
    # 保存提示词到文件
    prompt_file_path = os.path.join(module_output_dir, f"{module_name}_prompt.txt")
    with open(prompt_file_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    
    print(f"已生成模块 '{module_name}' 的文档提示词文件: {prompt_file_path}")
    
    # 如果提供了AI配置，则调用AI API生成文档
    if ai_config:
        info(f"正在调用AI API生成模块 '{module_name}' 的文档...")
        response = call_ai_api(prompt, ai_config)
        if response:
            # 保存AI生成的文档
            doc_file_path = os.path.join(module_output_dir, f"{module_name}_doc.md")
            if save_ai_response(response, doc_file_path):
                info(f"已生成模块 '{module_name}' 的AI文档: {doc_file_path}")
            else:
                ai_error(f"AI API调用成功，但保存{module_name}文档时出现问题")
        else:
            ai_error(f"AI API调用失败，将仅保留{module_name}提示词文件")
    
    return prompt_file_path


def main():
    parser = argparse.ArgumentParser(description="模块文档生成器")
    parser.add_argument("project_path", help="项目路径")
    parser.add_argument("--output", "-o", help="输出目录路径")
    parser.add_argument("--ai-config", "-c", default="ai_config.json", help="AI配置文件路径")
    
    args = parser.parse_args()
    
    # 计算项目名称和相关路径
    project_name = os.path.basename(os.path.abspath(args.project_path))
    if args.output:
        output_dir = args.output
    else:
        output_dir = os.path.join("output", project_name)
    
    module_structure_path = os.path.join(output_dir, "module_structure.json")
    global_var_info_path = os.path.join(output_dir, "global_var_info.json")
    
    # 加载必要的JSON文件
    module_structure = load_json_file(module_structure_path)
    if module_structure is None:
        return
    
    global_var_info = load_json_file(global_var_info_path)
    if global_var_info is None:
        return
    
    # 加载AI配置
    ai_config = load_ai_config(args.ai_config)
    
    # 进行拓扑排序，确保从最底层模块开始处理
    try:
        sorted_modules = topological_sort(module_structure)
        print(f"模块处理顺序: {' -> '.join(sorted_modules)}")
    except Exception as e:
        print(f"错误: {e}")
        return
    
    # 为每个模块生成文档
    for module_name in sorted_modules:
        print(f"正在处理模块: {module_name}")
        try:
            generate_module_doc(module_name, module_structure, global_var_info, args.project_path, output_dir, ai_config)
        except Exception as e:
            print(f"处理模块 '{module_name}' 时出错: {e}")

if __name__ == "__main__":
    main()
