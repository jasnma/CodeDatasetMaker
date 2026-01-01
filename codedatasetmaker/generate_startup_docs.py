#!/usr/bin/env python3
"""
启动流程文档生成器
根据call_graph.json和file_info.json生成启动流程文档
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


def find_main_function(call_graph):
    """查找main函数"""
    for func_name in call_graph.keys():
        if func_name.endswith(":main"):
            return func_name
    return None


def build_call_tree(call_graph, start_function):
    """构建函数调用树"""
    tree = defaultdict(list)
    
    # 使用广度优先搜索构建调用树
    queue = deque([start_function])
    visited = set()
    
    while queue:
        current_func = queue.popleft()
        if current_func in visited:
            continue
        visited.add(current_func)
        
        # 获取当前函数调用的函数
        callees = call_graph.get(current_func, [])
        tree[current_func] = callees
        
        # 将被调用的函数加入队列继续探索
        for callee in callees:
            if callee not in visited:
                queue.append(callee)
    
    return tree


def extract_function_source(file_info, function_name):
    """从file_info中提取函数源码位置信息"""
    # 解析函数名，格式为 "文件路径:函数名"
    parts = function_name.split(":")
    if len(parts) != 2:
        return None
        
    file_path, func_name = parts
    
    # 在file_info中查找对应的文件和函数
    for file_data in file_info:
        if file_data["file"] == file_path:
            for func in file_data.get("functions", []):
                if func["name"] == func_name:
                    return {
                        "file": file_path,
                        "function": func_name,
                        "start_line": func["start_line"],
                        "end_line": func["end_line"]
                    }
    return None


def read_function_content(project_path, func_source_info):
    """读取函数内容"""
    if not func_source_info:
        return None
        
    file_path = os.path.join(project_path, func_source_info["file"])
    start_line = func_source_info["start_line"]
    end_line = func_source_info["end_line"]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # 注意：行号通常从1开始，但列表索引从0开始
            function_lines = lines[start_line-1:end_line]
            return "".join(function_lines)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {file_path}")
        # 返回占位符文本而不是None，这样即使找不到源文件也能继续生成提示词
        return f"// 无法找到源文件 {file_path} 中的函数内容"
    except Exception as e:
        print(f"错误: 读取文件 {file_path} 失败: {e}")
        # 返回占位符文本而不是None，这样即使读取失败也能继续生成提示词
        return f"// 读取源文件 {file_path} 失败: {e}"


def find_main_loop_function(call_graph, main_function):
    """查找主循环函数"""
    # 查找main函数直接调用的函数
    main_callees = call_graph.get(main_function, [])
    
    # 寻找可能的主循环函数（通常是一个持续执行的函数）
    # 在嵌入式系统中，主循环通常是一个持续执行的函数
    for callee in main_callees:
        # 检查是否有明显的循环特征
        callee_name = callee.split(":")[-1]  # 获取函数名部分
        if any(keyword in callee_name.lower() for keyword in ["loop", "task", "process", "handle", "run"]):
            return callee
    
    # 如果没有找到明显特征的函数，返回第一个被调用的函数
    if main_callees:
        return main_callees[0]
    
    return None


def generate_startup_prompt(call_tree, main_function_content, called_functions_content, 
                           main_loop_function_content, main_loop_function_file, main_loop_function_name):
    """生成启动流程文档提示词"""
    # 读取提示词模板
    try:
        # 首先尝试在当前目录查找模板文件
        with open("startup_doc_prompt_template.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        # 如果在当前目录找不到，尝试在codedatasetmaker目录中查找
        try:
            template_path = os.path.join(os.path.dirname(__file__), "startup_doc_prompt_template.txt")
            with open(template_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            # 如果都找不到，报错退出
            error("错误: 找不到启动流程文档提示词模板文件 'startup_doc_prompt_template.txt'")
            error("请确保模板文件存在于当前目录或 codedatasetmaker 目录中")
            raise
    
    # 准备填充模板的数据
    call_tree_str = json.dumps(dict(call_tree), indent=2, ensure_ascii=False)
    
    called_functions_content_str = ""
    for func_name, content in called_functions_content.items():
        called_functions_content_str += f"\n// === {func_name} ===\n```c\n{content}\n```\n"
    
    # 填充模板
    prompt = prompt_template.format(
        call_tree_json=call_tree_str,
        main_function_content=main_function_content if main_function_content else "// 无法获取main函数源码",
        called_functions_content=called_functions_content_str if called_functions_content_str else "// 无调用函数源码",
        main_loop_function_content=main_loop_function_content if main_loop_function_content else "// 无法获取主循环函数源码",
        main_loop_function_file=main_loop_function_file if main_loop_function_file else "未知",
        main_loop_function_name=main_loop_function_name if main_loop_function_name else "未知"
    )
    
    return prompt


def generate_startup_doc(project_path, output_dir, project_name, ai_config=None):
    """生成启动流程文档"""
    call_graph_path = os.path.join(output_dir, project_name, "call_graph.json")
    file_info_path = os.path.join(output_dir, project_name, "file_info.json")
    
    # 加载必要的JSON文件
    call_graph = load_json_file(call_graph_path)
    if call_graph is None:
        return
    
    file_info = load_json_file(file_info_path)
    if file_info is None:
        return
    
    # 查找main函数
    main_function = find_main_function(call_graph)
    if not main_function:
        error("错误: 未找到main函数")
        return
    
    info(f"找到main函数: {main_function}")
    
    # 构建main函数调用树
    call_tree = build_call_tree(call_graph, main_function)
    
    # 提取main函数源码
    main_source_info = extract_function_source(file_info, main_function)
    main_function_content = read_function_content(project_path, main_source_info)
    
    # 提取main函数直接调用的函数源码
    called_functions_content = {}
    main_callees = call_tree.get(main_function, [])
    for callee in main_callees:
        func_source_info = extract_function_source(file_info, callee)
        func_content = read_function_content(project_path, func_source_info)
        if func_content:
            called_functions_content[callee] = func_content
    
    # 查找主循环函数
    main_loop_function = find_main_loop_function(call_graph, main_function)
    if not main_loop_function:
        warning("警告: 未找到主循环函数")
        main_loop_function_file = None
        main_loop_function_name = None
    else:
        info(f"找到主循环函数: {main_loop_function}")
        parts = main_loop_function.split(":")
        if len(parts) == 2:
            main_loop_function_file, main_loop_function_name = parts
        else:
            main_loop_function_file = None
            main_loop_function_name = None
    
    # 提取主循环函数源码
    main_loop_source_info = extract_function_source(file_info, main_loop_function) if main_loop_function else None
    main_loop_function_content = read_function_content(project_path, main_loop_source_info) if main_loop_source_info else None
    
    # 生成提示词
    prompt = generate_startup_prompt(call_tree, main_function_content, called_functions_content,
                                   main_loop_function_content, main_loop_function_file, main_loop_function_name)
    
    # 构建输出目录结构
    startup_output_dir = os.path.join(output_dir, project_name)
    os.makedirs(startup_output_dir, exist_ok=True)
    
    # 保存提示词到文件
    prompt_file_path = os.path.join(startup_output_dir, "startup_doc_prompt.txt")
    with open(prompt_file_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    
    info(f"已生成启动流程分析提示词文件: {prompt_file_path}")
    
    # 如果提供了AI配置，则调用AI API生成文档
    if ai_config:
        info("正在调用AI API生成启动流程文档...")
        response = call_ai_api(prompt, ai_config)
        if response:
            # 保存AI生成的文档
            doc_file_path = os.path.join(startup_output_dir, "startup_doc.md")
            if save_ai_response(response, doc_file_path):
                info(f"已生成启动流程AI文档: {doc_file_path}")
            else:
                ai_error("AI API调用成功，但保存启动流程文档时出现问题")
        else:
            ai_error("AI API调用失败，将仅保留启动流程提示词文件")
    
    return prompt_file_path


def main():
    parser = argparse.ArgumentParser(description="启动流程文档生成器")
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
    
    # 生成启动流程文档
    try:
        generate_startup_doc(args.project_path, output_dir, project_name, ai_config)
    except Exception as e:
        error(f"生成启动流程文档时出错: {e}")


if __name__ == "__main__":
    main()
