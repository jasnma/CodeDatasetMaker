#!/usr/bin/env python3
"""
模块文档生成器
根据module_structure.json和global_var_info.json生成模块级文档
"""

import json
import os
import argparse
import asyncio
from collections import defaultdict, deque

# 导入日志模块
from . import logger

# 导入工具函数
from .utils import load_json_file, load_ai_config, async_call_ai_api_stream, save_ai_response


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


def group_modules_by_dependency(module_structure):
    """
    根据模块依赖关系对模块进行分层分组
    
    使用 Kahn 算法进行拓扑排序，将模块分为不同层级。同一层级内的模块
    不会相互依赖，因此可以并发处理。
    
    Args:
        module_structure (dict): 模块结构信息
        
    Returns:
        list: 按层级分组的模块列表，每个元素是一个包含该层级所有模块的列表。
              层级索引越小，依赖越少，应优先处理。
    """
    # 获取模块依赖关系
    dependencies, _ = get_module_dependencies(module_structure)
    
    # 计算每个模块的入度（有多少个模块依赖它）
    # 入度为0表示没有其他模块依赖它，可以优先处理
    in_degree = defaultdict(int)
    
    # 初始化所有模块的入度为0
    for module_name in module_structure:
        in_degree[module_name] = 0
    
    # 计算实际入度
    for module_name, deps in dependencies.items():
        for dep in deps:
            if dep in module_structure:  # 确保依赖的模块存在
                in_degree[dep] += 1
    
    # 初始化层级分组
    levels = []
    
    # 找到所有入度为0的模块（没有其他模块依赖它们）
    # 这些模块可以作为第一批并发处理的模块
    queue = deque([module_name for module_name in in_degree if in_degree[module_name] == 0])
    processed = set()
    
    # 按层级进行分组
    while queue:
        # 当前层级的所有模块
        # 这些模块可以并发处理，因为它们之间没有依赖关系
        current_level = list(queue)
        levels.append(current_level)
        
        # 清空队列，准备下一层级
        next_queue = deque()
        
        # 处理当前层级的所有模块
        while queue:
            module_name = queue.popleft()
            processed.add(module_name)
            
            # 减少所有被当前模块依赖的模块的入度
            # 当一个模块被处理后，它所依赖的模块的入度应该减少
            for dep in dependencies.get(module_name, []):
                if dep in module_structure and dep not in processed:
                    in_degree[dep] -= 1
                    # 如果入度变为0，说明所有依赖它的模块都已处理完，
                    # 可以加入下一层级的候选队列
                    if in_degree[dep] == 0:
                        next_queue.append(dep)
        
        # 更新队列为下一层级
        queue = next_queue
    
    # 检查是否有循环依赖（未处理的模块）
    # 正常情况下，所有模块都应该被处理
    unprocessed = set(in_degree.keys()) - processed
    if unprocessed:
        print(f"警告: 检测到可能存在循环依赖的模块: {unprocessed}")
        # 将未处理的模块作为一个单独的层级
        levels.append(list(unprocessed))
    
    # 颠倒层级顺序，使没有依赖的模块在最前面
    levels.reverse()
    
    return levels


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
        logger.error(f"文件未找到: {file_path}")
        return None
    except Exception as e:
        logger.error(f"读取文件时出错: {e}")
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


async def module_worker(queue, module_structure, global_var_info, project_path, output_dir, ai_config, semaphore):
    """模块工作协程"""
    while True:
        item = await queue.get()
        if item is None:
            break

        try:
            module_name = item
            await generate_module_doc_async(
                module_name,
                module_structure,
                global_var_info,
                project_path,
                output_dir,
                ai_config,
                semaphore
            )
        finally:
            queue.task_done()


async def process_modules_by_levels(levels, module_structure, global_var_info, project_path, output_dir, ai_config):
    """按层级处理模块"""
    print(f"总共 {len(levels)} 个层级需要处理")

    max_concurrency = ai_config.get('max_concurrency', 5)
    queue = asyncio.Queue(maxsize=max_concurrency * 2)
    semaphore = asyncio.Semaphore(max_concurrency)
    num_workers = max_concurrency

    # 启动固定数量 worker
    workers = [
        asyncio.create_task(
            module_worker(
                queue,
                module_structure,
                global_var_info,
                project_path,
                output_dir,
                ai_config,
                semaphore
            )
        )
        for _ in range(num_workers)
    ]

    for i, level in enumerate(levels):
        print(f"正在处理第 {i+1}/{len(levels)} 层级，包含 {len(level)} 个模块")

        # 为当前层级的每个模块生成文档
        for module_name in level:
            await queue.put(module_name)

        # 等待队列清空，必须要待这一层的所有模块处理完成才能处理下一层
        await queue.join()

    # 关闭 worker
    for _ in workers:
        await queue.put(None)
    await asyncio.gather(*workers)


async def generate_module_doc_async(module_name, module_structure, global_var_info, project_path, output_dir, ai_config=None, semaphore=None):
    """异步生成单个模块的文档"""
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
        logger.warning(f"No source code found for module: {module_name}")
        return
    
    # 构造元数据
    metadata = {
        "dependencies": dependencies,
        "reverse_dependencies": reverse_deps,
        "global_variables": module_global_vars
    }
    
    # 读取提示词模板
    try:
        # 在prompt_template目录中查找模板文件
        template_path = os.path.join(os.path.dirname(__file__), "..", "prompt_template", "module_doc_prompt_template.txt")
        with open(template_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        # 如果找不到，报错退出
        logger.error("错误: 找不到模块文档提示词模板文件 'module_doc_prompt_template.txt'")
        logger.error("请确保模板文件存在于 prompt_template 目录中")
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
        logger.info(f"正在调用AI API生成模块 '{module_name}' 的文档...")
        # 使用异步API调用
        response = await async_call_ai_api_stream(prompt, ai_config, semaphore)
        if response:
            # 保存AI生成的文档
            doc_file_path = os.path.join(module_output_dir, f"{module_name}_doc.md")
            if save_ai_response(response, doc_file_path):
                logger.info(f"已生成模块 '{module_name}' 的AI文档: {doc_file_path}")
            else:
                logger.ai_error(f"AI API调用成功，但保存{module_name}文档时出现问题")
        else:
            logger.ai_error(f"AI API调用失败，将仅保留{module_name}提示词文件")


def main():
    parser = argparse.ArgumentParser(description="模块文档生成器")
    parser.add_argument("project_path", help="项目路径")
    parser.add_argument("--output", "-o", help="输出目录路径")
    parser.add_argument("--ai-config", "-c", default="ai_config.json", help="AI配置文件路径")
    
    args = parser.parse_args()
    
    # 计算项目名称和相关路径
    project_name = os.path.basename(os.path.abspath(args.project_path))
    if args.output:
        output_dir = os.path.join(args.output, project_name)
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
    
    # 按依赖关系对模块进行分组
    try:
        module_levels = group_modules_by_dependency(module_structure)
        print(f"模块分组完成，共 {len(module_levels)} 个层级")
        for i, level in enumerate(module_levels):
            print(f"  层级 {i}: {len(level)} 个模块")
            # 显示前几个模块作为示例
            for j, module in enumerate(level[:3]):
                print(f"    - {module}")
            if len(level) > 3:
                print(f"    ... 还有 {len(level) - 3} 个模块")
    except Exception as e:
        print(f"错误: {e}")
        return

    # 按层级处理模块
    asyncio.run(
        process_modules_by_levels(module_levels,
                                 module_structure,
                                 global_var_info,
                                 args.project_path,
                                 output_dir,
                                 ai_config)
    )

if __name__ == "__main__":
    main()
