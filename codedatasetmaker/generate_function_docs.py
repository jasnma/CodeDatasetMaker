#!/usr/bin/env python3
"""
函数文档生成器
根据call_graph.json和file_info.json生成函数级文档
"""

import json
import os
import argparse
import asyncio
from collections import defaultdict, deque

# 导入日志模块
from . import logger

# 导入工具函数
from .utils import load_json_file, load_ai_config, async_call_ai_api_stream, save_ai_response, get_ignore_dirs

# 定义一个变量记住已经处理过的函数，有些定义在头文件中的函数
# 重复被处理，增加这个变量可以避免重复处理
procedured_functions = set()


def build_call_graph_reverse(call_graph):
    """构建反向调用图"""
    reverse_call_graph = defaultdict(list)
    for caller, callees in call_graph.items():
        for callee in callees:
            reverse_call_graph[callee].append(caller)
    return reverse_call_graph


def get_function_dependencies(call_graph):
    """获取函数依赖关系"""
    dependencies = defaultdict(list)
    reverse_dependencies = defaultdict(list)
    
    for caller, callees in call_graph.items():
        dependencies[caller] = callees
        for callee in callees:
            reverse_dependencies[callee].append(caller)
    
    return dependencies, reverse_dependencies


def find_function_info(function_name, file_info):
    """根据函数名查找函数信息"""
    parts = function_name.split(":")
    file_path = parts[0]
    function_name = parts[1]

    for file_data in file_info:
        if file_path != file_data["file"]:
            continue
        
        for func in file_data["functions"]:
            if func['name'] == function_name:
                return file_data, func
    return None, None


def read_function_content(file_path, start_line, end_line, project_path):
    """读取函数内容"""
    full_path = os.path.join(project_path, file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # 注意：行号通常从1开始，但列表索引从0开始
            function_lines = lines[start_line-1:end_line]
            return "".join(function_lines)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {full_path}")
        return None
    except Exception as e:
        print(f"错误: 读取文件 {full_path} 失败: {e}")
        return None


def extract_function_doc_from_file(file_path):
    """从文件中提取函数文档的功能描述部分"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 查找"功能描述"部分
        # 查找"### 功能描述"标题
        func_desc_start = content.find("### 功能描述")
        if func_desc_start == -1:
            # 如果没找到"### 功能描述"，尝试查找"功能描述"
            func_desc_start = content.find("功能描述")
            if func_desc_start == -1:
                return content  # 如果都没找到，返回整个内容
        
        # 从"功能描述"开始截取
        func_desc_content = content[func_desc_start:]
        
        # 查找下一个标题，如果有则截取到下一个标题之前
        next_title_pos = func_desc_content.find("\n##", len("### 功能描述"))
        if next_title_pos != -1:
            func_desc_content = func_desc_content[:next_title_pos]
        
        # 去除标题本身，只保留内容
        # 找到第一行换行符
        first_newline = func_desc_content.find("\n")
        if first_newline != -1:
            func_desc_content = func_desc_content[first_newline+1:].strip()
        else:
            # 如果没有找到换行符，就去掉标题部分
            if func_desc_content.startswith("### 功能描述"):
                func_desc_content = func_desc_content[len("### 功能描述"):].strip()
            elif func_desc_content.startswith("功能描述"):
                func_desc_content = func_desc_content[len("功能描述"):].strip()
        
        return func_desc_content
    except FileNotFoundError:
        print(f"文件未找到: {file_path}")
        return None
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None


def extract_callees_docs(output_dir, callees, project_name):
    """提取被调用函数的文档"""
    callees_docs = {}

    for callee in callees:
        # 构建文档文件路径
        doc_file_path = os.path.join(output_dir, project_name, "functions", callee, f"_doc.md")

        # 尝试读取文档
        doc_content = extract_function_doc_from_file(doc_file_path)
        if doc_content:
            callees_docs[callee] = doc_content

    return callees_docs


def generate_function_prompt(function_name, function_content, callees, callees_docs, callers):
    """生成函数文档提示词"""
    # 构建被调用函数文档部分
    callees_docs_str = ""
    if callees_docs:
        for callee, doc in callees_docs.items():
            callees_docs_str += f"\n// === {callee} 的功能说明 ===\n"
            callees_docs_str += doc
            callees_docs_str += "\n"
    else:
        callees_docs_str = "无\n"
    
    # 读取提示词模板
    try:
        # 首先尝试在当前目录查找模板文件
        with open("function_doc_prompt_template.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        # 如果在当前目录找不到，尝试在codedatasetmaker目录中查找
        try:
            template_path = os.path.join(os.path.dirname(__file__), "function_doc_prompt_template.txt")
            with open(template_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            # 如果都找不到，报错退出
            logger.error("错误: 找不到函数文档提示词模板文件 'function_doc_prompt_template.txt'")
            logger.error("请确保模板文件存在于当前目录或 codedatasetmaker 目录中")
            raise
    
    # 填充模板
    prompt = prompt_template.format(
        function_name=function_name,
        function_content=function_content,
        callees_json=json.dumps(callees, indent=2, ensure_ascii=False),
        callees_docs=callees_docs_str,
        callers_json=callers
    )
    
    return prompt


async def generate_function_doc_async(
    function_name,
    call_graph,
    reverse_call_graph,
    file_info,
    project_path,
    output_dir,
    project_name,
    ai_config,
    semaphore
):
    """生成单个函数的文档"""
    # 获取函数信息
    file_data, func_info = find_function_info(function_name, file_info)
    
    if not file_data or not func_info:
        print(f"错误: 找不到函数 {function_name} 的信息")
        return None
    
    file_path = func_info["definded_in"]
    function_base_name = func_info["name"]

    if function_name in procedured_functions:
        print(f"已处理过函数 {function_name}")
        return None
    
    procedured_functions.add(function_name)
    
    # 构建输出目录结构
    function_output_dir = os.path.join(output_dir, project_name, "functions", file_path)
    os.makedirs(function_output_dir, exist_ok=True)
    
    # 生成文件名
    prompt_file_name = f"{function_base_name}_prompt.txt"
    doc_file_name = f"{function_base_name}_doc.md"

    # 如果文档文件已经存在，则跳过
    doc_file_path = os.path.join(function_output_dir, doc_file_name)
    if os.path.exists(doc_file_path):
        logger.info(f"Skipping {function_base_name}")
        return

    # 读取函数内容
    function_content = read_function_content(file_path, func_info["start_line"], func_info["end_line"], project_path)
    
    if not function_content:
        print(f"错误: 无法读取函数 {function_name} 的内容")
        return None
    
    # 获取调用的函数列表
    callees = call_graph.get(function_name, [])

    # 调用这个函数的列表
    callers = reverse_call_graph.get(function_name, [])

    # 提取被调用函数的文档
    callees_docs = extract_callees_docs(output_dir, callees, project_name)
    
    # 生成提示词
    prompt = generate_function_prompt(function_name, function_content, callees, callees_docs, callers)

    # 保存提示词到文件
    prompt_file_path = os.path.join(function_output_dir, prompt_file_name)
    with open(prompt_file_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    
    print(f"已生成函数 '{function_name}' 的文档提示词文件: {prompt_file_path}")
    
    # 如果提供了AI配置，则调用AI API生成文档
    if ai_config:
        logger.info(f"正在调用AI API生成函数 '{function_name}' 的文档...")
        response = await async_call_ai_api_stream(
            prompt,
            ai_config,
            semaphore
        )

        if response:
            # 保存AI生成的文档
            if save_ai_response(response, doc_file_path):
                logger.info(f"已生成函数 '{function_name}' 的AI文档: {doc_file_path}")
            else:
                logger.ai_error(f"AI API调用成功，但保存{function_name}文档时出现问题")
        else:
            logger.ai_error(f"AI API调用失败，将仅保留{function_name}提示词文件")


def should_ignore_path(file_path, ignore_dirs):
    """检查文件路径是否应该被忽略"""
    for ignore_dir in ignore_dirs:
        if ignore_dir in file_path:
            return True
    return False


async def function_worker(
    queue,
    call_graph,
    reverse_call_graph,
    file_info,
    project_path,
    output_dir,
    project_name,
    ai_config,
    semaphore
):
    """函数工作协程"""
    while True:
        item = await queue.get()
        if item is None:
            break

        try:
            function_name = item
            await generate_function_doc_async(
                function_name,
                call_graph,
                reverse_call_graph,
                file_info,
                project_path,
                output_dir,
                project_name,
                ai_config,
                semaphore
            )
        finally:
            queue.task_done()


async def process_functions_by_levels(levels, call_graph, reverse_call_graph, file_info, project_path, output_dir, project_name, ai_config, ignore_dirs):
    """按层级处理函数"""
    print(f"总共 {len(levels)} 个层级需要处理")

    max_concurrency = ai_config.get('max_concurrency', 5)
    queue = asyncio.Queue(maxsize=max_concurrency * 2)
    semaphore = asyncio.Semaphore(max_concurrency)
    num_workers = max_concurrency

    # 启动固定数量 worker
    workers = [
        asyncio.create_task(
            function_worker(
                queue,
                call_graph,
                reverse_call_graph,
                file_info,
                project_path,
                output_dir,
                project_name,
                ai_config,
                semaphore
            )
        )
        for _ in range(num_workers)
    ]

    for i, level in enumerate(levels):
        print(f"正在处理第 {i+1}/{len(levels)} 层级，包含 {len(level)} 个函数")

        # 为当前层级的每个函数生成文档
        for function_name in level:
            await queue.put(function_name)

        # 等待队列清空，必须要待这一层的所有函数处理完成才能处理下一层
        await queue.join()

    # 关闭 worker
    for _ in workers:
        await queue.put(None)
    await asyncio.gather(*workers)


def group_functions_by_dependency(call_graph):
    """
    根据函数依赖关系对函数进行分层分组
    
    使用 Kahn 算法进行拓扑排序，将函数分为不同层级。同一层级内的函数
    不会相互依赖，因此可以并发处理。
    
    Args:
        call_graph (dict): 函数调用图，格式为 {caller: [callee1, callee2, ...]}
            caller: 调用其他函数的函数
            callee: 被调用的函数
        
    Returns:
        list: 按层级分组的函数列表，每个元素是一个包含该层级所有函数的列表。
              层级索引越小，依赖越少，应优先处理。
              
    Example:
        >>> call_graph = {
        ...     "file1.c:main": ["file1.c:init", "file2.c:process_data"],
        ...     "file1.c:init": ["file3.c:setup"],
        ...     "file2.c:process_data": ["file3.c:setup"],
        ...     "file3.c:setup": []
        ... }
        >>> levels = group_functions_by_dependency(call_graph)
        >>> len(levels)
        3
    """
    # 计算每个函数的入度（有多少个函数调用它）
    # 入度为0表示没有其他函数依赖它，可以优先处理
    in_degree = defaultdict(int)
    
    # 初始化所有函数的入度为0
    for func in call_graph:
        in_degree[func] = 0
    
    # 计算实际入度
    for caller, callees in call_graph.items():
        for callee in callees:
            in_degree[callee] += 1
    
    # 初始化层级分组
    levels = []
    
    # 找到所有入度为0的函数（没有其他函数调用它们）
    # 这些函数可以作为第一批并发处理的函数
    queue = deque([func for func in in_degree if in_degree[func] == 0])
    processed = set()
    
    # 按层级进行分组
    while queue:
        # 当前层级的所有函数
        # 这些函数可以并发处理，因为它们之间没有依赖关系
        current_level = list(queue)
        levels.append(current_level)
        
        # 清空队列，准备下一层级
        next_queue = deque()
        
        # 处理当前层级的所有函数
        while queue:
            func = queue.popleft()
            processed.add(func)
            
            # 减少所有被当前函数调用的函数的入度
            # 当一个函数被处理后，它所依赖的函数的入度应该减少
            for callee in call_graph.get(func, []):
                if callee not in processed:
                    in_degree[callee] -= 1
                    # 如果入度变为0，说明所有依赖它的函数都已处理完，
                    # 可以加入下一层级的候选队列
                    if in_degree[callee] == 0:
                        next_queue.append(callee)
        
        # 更新队列为下一层级
        queue = next_queue
    
    # 检查是否有循环依赖（未处理的函数）
    # 正常情况下，所有函数都应该被处理
    unprocessed = set(in_degree.keys()) - processed
    if unprocessed:
        print(f"警告: 检测到可能存在循环依赖的函数: {unprocessed}")
        # 将未处理的函数作为一个单独的层级
        # 在实际应用中，可能需要特殊处理这些函数
        levels.append(list(unprocessed))
    
    # 颠倒层级顺序，使没有依赖的函数在最前面
    levels.reverse()
    
    return levels


def main():
    parser = argparse.ArgumentParser(description="函数文档生成器")
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
    
    call_graph_path = os.path.join(output_dir, project_name, "call_graph.json")
    file_info_path = os.path.join(output_dir, project_name, "file_info.json")
    
    # 加载必要的JSON文件
    call_graph = load_json_file(call_graph_path)
    if call_graph is None:
        return
    
    file_info = load_json_file(file_info_path)
    if file_info is None:
        return
    
    # 加载AI配置
    ai_config = load_ai_config(args.ai_config)
    
    # 获取忽略目录列表
    ignore_dirs = get_ignore_dirs(ai_config) if ai_config else []
    
    # 构建反向调用图
    reverse_call_graph = build_call_graph_reverse(call_graph)
    
    # 按依赖关系对函数进行分组
    try:
        function_levels = group_functions_by_dependency(call_graph)
        print(f"函数分组完成，共 {len(function_levels)} 个层级")
        for i, level in enumerate(function_levels):
            print(f"  层级 {i}: {len(level)} 个函数")
            # 显示前几个函数作为示例
            for j, func in enumerate(level[:3]):
                print(f"    - {func}")
            if len(level) > 3:
                print(f"    ... 还有 {len(level) - 3} 个函数")
    except Exception as e:
        print(f"错误: {e}")
        return

    # 按层级处理函数
    asyncio.run(
        process_functions_by_levels(function_levels,
                                    call_graph,
                                    reverse_call_graph,
                                    file_info,
                                    args.project_path,
                                    output_dir,
                                    project_name,
                                    ai_config,
                                    ignore_dirs)
    )


if __name__ == "__main__":
    main()
