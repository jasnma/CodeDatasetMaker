#!/usr/bin/env python3
"""
宏定义级训练样本生成器
根据宏定义文档生成Q&A格式的训练样本
"""

import os
import argparse
import json
import asyncio

# 导入日志模块
from . import logger

# 导入工具函数
from .utils import load_ai_config, async_call_ai_api_stream, save_ai_response, get_ignore_dirs

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


def should_ignore_path(file_path, ignore_dirs):
    """检查文件路径是否应该被忽略"""
    for ignore_dir in ignore_dirs:
        if ignore_dir in file_path:
            return True
    return False


async def generate_single_macro_train_async(
    project_path,
    output_dir,
    project_name,
    defined_in,
    macro_name,
    macro_info,
    ai_config,
    semaphore
):
    """异步生成单个宏定义的训练样本"""
    
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
        return None
    
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
    
    logger.info(f"开始生成宏定义训练样本: {macro_name}")

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
                logger.info(f"完成: {macro_name}")
                return train_file_path
            else:
                logger.ai_error("AI API调用成功，但保存宏定义训练样本时出现问题")
        else:
            logger.ai_error(f"AI API调用失败，将仅保留宏定义训练样本提示词文件: {macro_name}")
    
    return None


async def macro_worker(
    queue,
    project_path,
    output_dir,
    project_name,
    macro_info,
    ai_config,
    semaphore
):
    """宏定义工作协程"""
    while True:
        item = await queue.get()
        if item is None:
            break

        try:
            defined_in, macro_name = item
            await generate_single_macro_train_async(
                project_path,
                output_dir,
                project_name,
                defined_in,
                macro_name,
                macro_info,
                ai_config,
                semaphore
            )
        finally:
            queue.task_done()


async def generate_all_macros_train_async(
    project_path,
    output_dir,
    project_name,
    ai_config,
    ignore_dirs,
    max_concurrency=5
):
    """异步并发生成所有宏定义的训练样本"""
    # 读取宏定义信息
    macro_info = read_macro_info(project_name, output_dir)
    if not macro_info:
        return

    queue = asyncio.Queue(maxsize=max_concurrency * 2)
    semaphore = asyncio.Semaphore(max_concurrency)
    num_workers = max_concurrency + 2

    # 启动固定数量 worker
    workers = [
        asyncio.create_task(
            macro_worker(
                queue,
                project_path,
                output_dir,
                project_name,
                macro_info,
                ai_config,
                semaphore
            )
        )
        for _ in range(num_workers)
    ]

    # 逐个投喂宏定义（几乎不占内存）
    for item in macro_info:
        macro_name = item.get("macro")
        defined_in = item.get("defined_in")
        
        if not macro_name or not defined_in:
            continue

        # 检查是否应该忽略该宏定义
        if ignore_dirs and should_ignore_path(defined_in, ignore_dirs):
            logger.info(f"跳过被忽略目录中的宏定义: {macro_name}")
            continue

        await queue.put((defined_in, macro_name))

    # 等待队列清空
    await queue.join()

    # 关闭 worker
    for _ in workers:
        await queue.put(None)
    await asyncio.gather(*workers)


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

    max_concurrency = ai_config.get("max_concurrency", 5)
    
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
                asyncio.run(
                    generate_single_macro_train_async(
                        args.project_path,
                        output_dir,
                        project_name,
                        defined_in,
                        macro_name,
                        macro_info,
                        ai_config,
                        asyncio.Semaphore(1)
                    )
                )
            else:
                logger.error("错误: 宏定义格式不正确，应为 '宏名称:定义文件'")
        else:
            # 生成所有宏定义的训练样本
            asyncio.run(
                generate_all_macros_train_async(
                    args.project_path,
                    output_dir,
                    project_name,
                    ai_config,
                    ignore_dirs,
                    max_concurrency=max_concurrency
                )
            )
    except Exception as e:
        logger.error(f"生成宏定义训练样本时出错: {e}")


if __name__ == "__main__":
    main()
