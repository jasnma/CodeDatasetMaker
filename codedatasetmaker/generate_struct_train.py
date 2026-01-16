#!/usr/bin/env python3
"""
结构体级训练样本生成器
根据结构体文档生成Q&A格式的训练样本
"""

import os
import argparse
import json
import asyncio

# 导入日志模块
from . import logger

# 导入工具函数
from .utils import load_ai_config, async_call_ai_api_stream, save_ai_response, get_ignore_dirs


def read_struct_doc(project_name, output_dir, struct_name):
    """读取结构体文档文件"""
    # 首先检查output_dir是否直接包含structs目录
    structs_dir = os.path.join(output_dir, "structs")
    if not os.path.exists(structs_dir):
        # output_dir是根输出目录，structs目录在子目录中
        structs_dir = os.path.join(output_dir, project_name, "structs")
    
    struct_doc_path = os.path.join(structs_dir, f"{struct_name}_doc.md")
    
    try:
        with open(struct_doc_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"错误: 找不到结构体文档文件 {struct_doc_path}")
        return None
    except Exception as e:
        logger.error(f"错误: 读取结构体文档文件失败 {struct_doc_path}: {e}")
        return None


def generate_struct_train_prompt(struct_doc_content):
    """生成结构体训练样本提示词"""
    # 读取提示词模板
    try:
        # 在prompt_template目录中查找模板文件
        template_path = os.path.join(os.path.dirname(__file__), "..", "prompt_template", "struct_train_prompt_template.txt")
        with open(template_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        # 如果找不到，报错退出
        logger.error("错误: 找不到结构体训练样本提示词模板文件 'struct_train_prompt_template.txt'")
        logger.error("请确保模板文件存在于 prompt_template 目录中")
        raise
    
    # 填充模板
    prompt = prompt_template.format(
        struct_doc_content=struct_doc_content if struct_doc_content else "// 无法获取结构体文档内容"
    )
    
    return prompt

def read_struct_info(project_name, output_dir):
    """读取结构体信息文件"""
    # 首先检查output_dir是否直接包含struct_info.json
    struct_info_path = os.path.join(output_dir, "struct_info.json")
    if not os.path.exists(struct_info_path):
        # output_dir是根输出目录，struct_info.json在子目录中
        struct_info_path = os.path.join(output_dir, project_name, "struct_info.json")
    
    try:
        with open(struct_info_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"错误: 找不到结构体信息文件 {struct_info_path}")
        return None
    except Exception as e:
        logger.error(f"错误: 读取结构体信息文件失败 {struct_info_path}: {e}")
        return None


async def generate_single_struct_train_async(
    project_path,
    output_dir,
    project_name,
    struct_name,
    ai_config,
    semaphore
):
    train_output_dir = os.path.join(output_dir, project_name, "train", "structs")
    os.makedirs(train_output_dir, exist_ok=True)

    train_file_path = os.path.join(train_output_dir, f"{struct_name}_train.md")
    if os.path.exists(train_file_path):
        logger.info(f"已存在，跳过：{struct_name}")
        return None

    struct_doc_content = read_struct_doc(project_name, output_dir, struct_name)
    if not struct_doc_content:
        return None

    prompt = generate_struct_train_prompt(struct_doc_content)

    prompt_file_path = os.path.join(train_output_dir, f"{struct_name}_train_prompt.txt")
    with open(prompt_file_path, "w", encoding="utf-8") as f:
        f.write(prompt)

    logger.info(f"开始生成结构体训练样本: {struct_name}")

    response = await async_call_ai_api_stream(
        prompt,
        ai_config,
        semaphore
    )

    if response:
        if save_ai_response(response, train_file_path):
            logger.info(f"完成: {struct_name}")
            return train_file_path

    return None


async def struct_worker(
    queue,
    project_path,
    output_dir,
    project_name,
    ai_config,
    semaphore
):
    while True:
        struct_name = await queue.get()
        if struct_name is None:
            break

        try:
            await generate_single_struct_train_async(
                project_path,
                output_dir,
                project_name,
                struct_name,
                ai_config,
                semaphore
            )
        finally:
            queue.task_done()


async def generate_all_structs_train_async(
    project_path,
    output_dir,
    project_name,
    ai_config,
    ignore_dirs,
    max_concurrency=5
):
    struct_info = read_struct_info(project_name, output_dir)
    if not struct_info:
        return

    queue = asyncio.Queue(maxsize=max_concurrency * 2)
    semaphore = asyncio.Semaphore(max_concurrency)
    num_workers = max_concurrency + 2

    # 启动固定数量 worker
    workers = [
        asyncio.create_task(
            struct_worker(
                queue,
                project_path,
                output_dir,
                project_name,
                ai_config,
                semaphore
            )
        )
        for _ in range(num_workers)
    ]

    # 逐个投喂 struct（几乎不占内存）
    for item in struct_info:
        struct_name = item.get("struct") or item.get("union") or item.get("enum")
        if not struct_name:
            continue

        # 检查是否应该忽略该结构体
        defined_in = item.get("defined_in", "")
        if ignore_dirs and should_ignore_path(defined_in, ignore_dirs):
            struct_name = item.get('struct', item.get('union', item.get('enum', '未知')))
            logger.info(f"跳过被忽略目录中的结构体: {struct_name}")
            continue

        await queue.put(struct_name)

    # 等待队列清空
    await queue.join()

    # 关闭 worker
    for _ in workers:
        await queue.put(None)
    await asyncio.gather(*workers)


def should_ignore_path(file_path, ignore_dirs):
    """检查文件路径是否应该被忽略"""
    for ignore_dir in ignore_dirs:
        if ignore_dir in file_path:
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description="结构体级训练样本生成器")
    parser.add_argument("project_path", help="项目路径")
    parser.add_argument("--output", "-o", help="输出目录路径")
    parser.add_argument("--ai-config", "-c", default="ai_config.json", help="AI配置文件路径")
    parser.add_argument("--struct", "-s", help="指定生成特定结构体的训练样本")
    
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
    
    # 生成结构体训练样本
    try:
        if args.struct:
            asyncio.run(
                generate_single_struct_train_async(
                    args.project_path,
                    output_dir,
                    project_name,
                    args.struct,
                    ai_config,
                    asyncio.Semaphore(1)
                )
            )
        else:
            asyncio.run(
                generate_all_structs_train_async(
                    args.project_path,
                    output_dir,
                    project_name,
                    ai_config,
                    ignore_dirs,
                    max_concurrency=max_concurrency
                )
            )
    except Exception as e:
        logger.error(f"生成结构体训练样本时出错: {e}")


if __name__ == "__main__":
    main()
