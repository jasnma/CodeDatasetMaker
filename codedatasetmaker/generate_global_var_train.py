#!/usr/bin/env python3
"""
全局变量级训练样本生成器
根据全局变量文档生成Q&A格式的训练样本
"""

import os
import argparse
import json
import asyncio

# 导入日志模块
from . import logger

# 导入工具函数
from .utils import load_ai_config, async_call_ai_api_stream, save_ai_response, get_ignore_dirs

def read_global_var_doc(project_name, output_dir, var_name):
    """读取全局变量文档文件"""
    # 构建文档文件路径
    global_var_doc_path = os.path.join(output_dir, project_name, "global_vars", f"{var_name}_doc.md")
    
    try:
        with open(global_var_doc_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"错误: 找不到全局变量文档文件 {global_var_doc_path}")
        return None
    except Exception as e:
        logger.error(f"错误: 读取全局变量文档文件失败 {global_var_doc_path}: {e}")
        return None


def generate_global_var_train_prompt(global_var_doc_content):
    """生成全局变量训练样本提示词"""
    # 读取提示词模板
    try:
        # 首先尝试在当前目录查找模板文件
        with open("global_var_train_prompt_template.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        # 如果在当前目录找不到，尝试在codedatasetmaker目录中查找
        try:
            template_path = os.path.join(os.path.dirname(__file__), "global_var_train_prompt_template.txt")
            with open(template_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            # 如果都找不到，报错退出
            logger.error("错误: 找不到全局变量训练样本提示词模板文件 'global_var_train_prompt_template.txt'")
            logger.error("请确保模板文件存在于当前目录或 codedatasetmaker 目录中")
            raise
    
    # 填充模板
    prompt = prompt_template.format(
        global_var_doc_content=global_var_doc_content if global_var_doc_content else "// 无法获取全局变量文档内容"
    )
    
    return prompt


def read_global_var_info(project_name, output_dir):
    """读取全局变量信息文件"""
    global_var_info_path = os.path.join(output_dir, project_name, "global_var_info.json")
    
    try:
        with open(global_var_info_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"错误: 找不到全局变量信息文件 {global_var_info_path}")
        return None
    except Exception as e:
        logger.error(f"错误: 读取全局变量信息文件失败 {global_var_info_path}: {e}")
        return None


def should_ignore_path(file_path, ignore_dirs):
    """检查文件路径是否应该被忽略"""
    for ignore_dir in ignore_dirs:
        if ignore_dir in file_path:
            return True
    return False


async def generate_single_global_var_train_async(
    project_path,
    output_dir,
    project_name,
    var_name,
    ai_config,
    semaphore
):
    """异步生成单个全局变量的训练样本"""
    
    # 构建输出目录结构
    train_output_dir = os.path.join(output_dir, project_name, "train", "global_vars")
    os.makedirs(train_output_dir, exist_ok=True)

    train_file_path = os.path.join(train_output_dir, f"{var_name}_train.md")
    if os.path.exists(train_file_path):
        logger.info(f"全局变量训练样本已存在，跳过生成：{train_file_path}")
        return None
    
    # 读取现有的全局变量文档文件
    global_var_doc_content = read_global_var_doc(project_name, output_dir, var_name)
    if global_var_doc_content is None:
        return None
    
    # 生成提示词
    prompt = generate_global_var_train_prompt(global_var_doc_content)
    # 保存提示词到文件
    prompt_file_path = os.path.join(train_output_dir, f"{var_name}_train_prompt.txt")
    with open(prompt_file_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    
    logger.info(f"开始生成全局变量训练样本: {var_name}")

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
                logger.info(f"完成: {var_name}")
                return train_file_path
            else:
                logger.ai_error("AI API调用成功，但保存全局变量训练样本时出现问题")
        else:
            logger.ai_error(f"AI API调用失败，将仅保留全局变量训练样本提示词文件: {var_name}")
    
    return None


async def global_var_worker(
    queue,
    project_path,
    output_dir,
    project_name,
    ai_config,
    semaphore
):
    """全局变量工作协程"""
    while True:
        var_name = await queue.get()
        if var_name is None:
            break

        try:
            await generate_single_global_var_train_async(
                project_path,
                output_dir,
                project_name,
                var_name,
                ai_config,
                semaphore
            )
        finally:
            queue.task_done()


async def generate_all_global_vars_train_async(
    project_path,
    output_dir,
    project_name,
    ai_config,
    ignore_dirs,
    max_concurrency=5
):
    """异步并发生成所有全局变量的训练样本"""
    # 读取全局变量信息
    global_var_info = read_global_var_info(project_name, output_dir)
    if not global_var_info:
        return

    queue = asyncio.Queue(maxsize=max_concurrency * 2)
    semaphore = asyncio.Semaphore(max_concurrency)
    num_workers = max_concurrency + 2

    # 启动固定数量 worker
    workers = [
        asyncio.create_task(
            global_var_worker(
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

    # 逐个投喂全局变量（几乎不占内存）
    for item in global_var_info:
        # 检查是否应该忽略该全局变量
        defined_in = item.get("defined_in", "")
        if ignore_dirs and should_ignore_path(defined_in, ignore_dirs):
            var_name = item.get("var", "未知")
            logger.info(f"跳过被忽略目录中的全局变量: {var_name}")
            continue
            
        # 获取全局变量名称
        var_name = item.get("var", "")
        if not var_name:
            continue
            
        await queue.put(var_name)

    # 等待队列清空
    await queue.join()

    # 关闭 worker
    for _ in workers:
        await queue.put(None)
    await asyncio.gather(*workers)


def main():
    parser = argparse.ArgumentParser(description="全局变量级训练样本生成器")
    parser.add_argument("project_path", help="项目路径")
    parser.add_argument("--output", "-o", help="输出目录路径")
    parser.add_argument("--ai-config", "-c", default="ai_config.json", help="AI配置文件路径")
    parser.add_argument("--var", "-v", help="指定生成特定全局变量的训练样本")
    
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
    
    # 生成全局变量训练样本
    try:
        if args.var:
            # 生成特定全局变量的训练样本
            asyncio.run(
                generate_single_global_var_train_async(
                    args.project_path,
                    output_dir,
                    project_name,
                    args.var,
                    ai_config,
                    asyncio.Semaphore(1)
                )
            )
        else:
            # 生成所有全局变量的训练样本
            asyncio.run(
                generate_all_global_vars_train_async(
                    args.project_path,
                    output_dir,
                    project_name,
                    ai_config,
                    ignore_dirs,
                    max_concurrency=max_concurrency
                )
            )
    except Exception as e:
        logger.error(f"生成全局变量训练样本时出错: {e}")


if __name__ == "__main__":
    main()
