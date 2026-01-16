#!/usr/bin/env python3
"""
函数级训练样本生成器
根据函数文档生成Q&A格式的训练样本
"""

import os
import argparse
import json
import asyncio

# 导入日志模块
from . import logger

# 导入工具函数
from .utils import load_ai_config, call_ai_api, async_call_ai_api_stream, save_ai_response, get_ignore_dirs

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
        # 在prompt_template目录中查找模板文件
        template_path = os.path.join(os.path.dirname(__file__), "..", "prompt_template", "function_train_prompt_template.txt")
        with open(template_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        # 如果找不到，报错退出
        logger.error("错误: 找不到函数训练样本提示词模板文件 'function_train_prompt_template.txt'")
        logger.error("请确保模板文件存在于 prompt_template 目录中")
        raise
    
    # 填充模板
    prompt = prompt_template.format(
        function_doc_content=function_doc_content if function_doc_content else "// 无法获取函数文档内容",
        function_source_code=function_source_code if function_source_code else "// 无法获取函数源代码"
    )
    
    return prompt


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


def should_ignore_path(file_path, ignore_dirs):
    """检查文件路径是否应该被忽略"""
    for ignore_dir in ignore_dirs:
        if ignore_dir in file_path:
            return True
    return False


async def generate_single_function_train_async(
    project_path,
    output_dir,
    project_name,
    file_path,
    function_name,
    file_info,
    ai_config,
    semaphore
):
    """异步生成单个函数的训练样本"""
    
    # 构建输出目录结构
    train_output_dir = os.path.join(output_dir, project_name, "train", "functions", file_path)
    os.makedirs(train_output_dir, exist_ok=True)

    train_file_path = os.path.join(train_output_dir, f"{function_name}_train.md")
    if os.path.exists(train_file_path):
        logger.info(f"函数训练样本已存在，跳过生成：{train_file_path}")
        return None
    
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
    except Exception as e:
        logger.warning(f"读取函数 {function_name} 源代码时出错: {e}")
        function_source_code = "// 无法读取函数源代码"
    
    # 生成提示词
    prompt = generate_function_train_prompt(function_doc_content, function_source_code)
    # 保存提示词到文件
    prompt_file_path = os.path.join(train_output_dir, f"{function_name}_train_prompt.txt")
    with open(prompt_file_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    
    logger.info(f"开始生成函数训练样本: {function_name}")

    # 如果提供了AI配置，则调用AI API生成训练样本
    if ai_config:
        response = await async_call_ai_api_stream(
            prompt,
            ai_config,
            semaphore
        )
        
        if response:
            # 保存AI生成的训练样本
            if save_ai_response(response, train_file_path):
                logger.info(f"完成: {function_name}")
                return train_file_path
            else:
                logger.ai_error("AI API调用成功，但保存函数训练样本时出现问题")
        else:
            logger.ai_error(f"AI API调用失败，将仅保留函数训练样本提示词文件: {function_name}")
    
    return None


async def function_worker(
    queue,
    project_path,
    output_dir,
    project_name,
    file_info,
    ai_config,
    semaphore
):
    """函数工作协程"""
    while True:
        item = await queue.get()
        if item is None:
            break

        try:
            file_path, func_name = item
            await generate_single_function_train_async(
                project_path,
                output_dir,
                project_name,
                file_path,
                func_name,
                file_info,
                ai_config,
                semaphore
            )
        finally:
            queue.task_done()


async def generate_all_functions_train_async(
    project_path,
    output_dir,
    project_name,
    ai_config,
    ignore_dirs,
    max_concurrency=5
):
    """异步并发生成所有函数的训练样本"""
    # 读取函数调用图
    call_graph = read_call_graph(project_name, output_dir)
    if not call_graph:
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

    queue = asyncio.Queue(maxsize=max_concurrency * 2)
    semaphore = asyncio.Semaphore(max_concurrency)
    num_workers = max_concurrency + 2

    # 启动固定数量 worker
    workers = [
        asyncio.create_task(
            function_worker(
                queue,
                project_path,
                output_dir,
                project_name,
                file_info,
                ai_config,
                semaphore
            )
        )
        for _ in range(num_workers)
    ]

    # 逐个投喂函数（几乎不占内存）
    for function_name in call_graph.keys():
        try:
            # 解析函数名称获取文件路径和函数名
            parts = function_name.split(":")
            if len(parts) >= 2:
                file_path = parts[0]
                func_name = parts[1]
                
                # 检查是否应该忽略该函数
                if ignore_dirs and should_ignore_path(file_path, ignore_dirs):
                    logger.info(f"跳过被忽略目录中的函数: {function_name}")
                    continue

                await queue.put((file_path, func_name))
        except Exception as e:
            logger.error(f"处理函数 {function_name} 时出错: {e}")
            continue

    # 等待队列清空
    await queue.join()

    # 关闭 worker
    for _ in workers:
        await queue.put(None)
    await asyncio.gather(*workers)


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
    
    # 获取忽略目录列表
    ignore_dirs = get_ignore_dirs(ai_config) if ai_config else []

    max_concurrency = ai_config.get("max_concurrency", 5)
    
    # 生成函数训练样本
    try:
        if args.function:
            # 解析函数名称获取文件路径和函数名
            parts = args.function.split(":")
            if len(parts) >= 2:
                file_path = parts[0]
                func_name = parts[1]
                
                # 检查是否应该忽略该函数
                if should_ignore_path(file_path, ignore_dirs):
                    logger.info(f"跳过被忽略目录中的函数: {args.function}")
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
                # 生成特定函数的训练样本
                asyncio.run(
                    generate_single_function_train_async(
                        args.project_path,
                        output_dir,
                        project_name,
                        file_path,
                        func_name,
                        file_info,
                        ai_config,
                        asyncio.Semaphore(1)
                    )
                )
            else:
                logger.error("错误: 函数名称格式不正确，应为 '文件路径:函数名'")
        else:
            # 生成所有函数的训练样本
            asyncio.run(
                generate_all_functions_train_async(
                    args.project_path,
                    output_dir,
                    project_name,
                    ai_config,
                    ignore_dirs,
                    max_concurrency=max_concurrency
                )
            )
    except Exception as e:
        logger.error(f"生成函数训练样本时出错: {e}")


if __name__ == "__main__":
    main()
