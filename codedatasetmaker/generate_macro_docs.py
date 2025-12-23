#!/usr/bin/env python3
"""
宏文档生成器
根据macro_info.json生成宏级文档
"""

import json
import os
import argparse
from collections import defaultdict, deque
from openai import OpenAI
from openai import APIError, APIConnectionError, RateLimitError


# 定义一个变量记住已经处理过的宏，避免重复处理
processed_macros = set()

# 定义一个函数，用于加载JSON文件
def load_json_file(file_path):
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"错误: JSON解析失败 {file_path}: {e}")
        return None


def load_ai_config(config_path="ai_config.json"):
    """加载AI配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"警告: 找不到配置文件 {config_path}，将仅生成提示词文件")
        return None
    except json.JSONDecodeError as e:
        print(f"错误: JSON解析失败 {config_path}: {e}")
        return None


def call_ai_api(prompt, config):
    """使用OpenAI SDK调用AI API并流式输出响应"""
    # 获取配置参数
    api_key = config.get("api_key")
    base_url = config.get("base_url", "https://api.openai.com/v1")
    model = config.get("model", "gpt-3.5-turbo")
    temperature = config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens", 2000)
    top_p = config.get("top_p", 1.0)
    frequency_penalty = config.get("frequency_penalty", 0.0)
    presence_penalty = config.get("presence_penalty", 0.0)
    
    # 检查必要参数
    if not api_key or api_key == "your_api_key_here":
        print("警告: 配置文件中缺少有效的api_key，将仅生成提示词文件")
        return None
    
    # 创建OpenAI客户端
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    # 构造消息
    messages = [{"role": "user", "content": prompt}]
    
    # 发送请求并流式输出响应
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stream=True  # 启用流式响应
        )
        
        # 流式输出响应
        full_response = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)  # 实时输出到控制台
                full_response += content
        
        print()  # 添加换行
        return {"choices": [{"message": {"content": full_response}}]}
        
    except RateLimitError as e:
        print(f"错误: 请求频率过高 {e}")
        return None
    except APIConnectionError as e:
        print(f"错误: API连接失败 {e}")
        return None
    except APIError as e:
        print(f"错误: API返回错误 {e}")
        return None
    except Exception as e:
        print(f"错误: API请求失败: {e}")
        return None


def save_ai_response(response, output_path):
    """保存AI响应到文件"""
    if response is None:
        return False
    
    try:
        # 保存AI生成的文档
        if "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0]["message"]["content"]
            # 去除头部的不可见字符，包括BOM和其他Unicode空白字符
            content = content.strip("\u200B\u200C\u200D\u2060\uFEFF")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        else:
            # 保存原始响应
            with open(output_path + ".raw.json", 'w', encoding='utf-8') as f:
                json.dump(response, f, ensure_ascii=False, indent=2)
            return False
    except Exception as e:
        print(f"错误: 保存AI响应失败: {e}")
        return False


def extract_macro_doc_from_file(file_path):
    """从文件中提取宏文档的功能描述部分"""
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


def extract_macro_usage_snippets(macro_name, used_in, project_path):
    """从源代码中提取宏使用的代码片段"""
    snippets = {}
    
    # 处理宏名称，如果是函数式宏则只取名称部分
    base_macro_name = macro_name.split('(')[0]
    
    # 获取项目中的所有C/C++源文件
    def get_c_files(directory):
        """获取目录下所有C源文件"""
        c_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.c', '.h', '.cpp', '.cc')):
                    c_files.append(os.path.join(root, file))
        return c_files
    
    # 获取所有源文件
    all_files = get_c_files(project_path)
    
    # 在所有文件中查找宏的使用
    for file_path in all_files:
        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"读取文件 {file_path} 时出错: {e}")
            continue
            
        # 查找包含宏的行
        snippet_lines = []
        for i, line in enumerate(lines):
            # 查找包含宏名称的行（包括#if, #elif, #ifdef等预处理指令）
            if (base_macro_name in line and 
                (not line.strip().startswith("#define") or 
                 ("#if" in line or "#elif" in line or "#ifdef" in line))):
                # 收集包含宏的行及其前后几行作为上下文
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                snippet = "".join(lines[start:end])
                # 计算相对于项目根目录的相对路径
                relative_path = os.path.relpath(file_path, project_path)
                snippet_lines.append(f"// 文件: {relative_path}, 行号: {i+1}\n{snippet}")
        
        if snippet_lines:
            # 计算相对于项目根目录的相对路径
            relative_path = os.path.relpath(file_path, project_path)
            snippets[relative_path] = "\n".join(snippet_lines)
    
    return snippets




def generate_macro_usage_examples(macro_name, used_in, project_path):
    """生成宏使用示例"""
    import random
    
    # 如果没有使用位置，返回空字符串
    if not used_in:
        return "无"
    
    # 随机选择最多5个使用位置
    selected_usages = random.sample(used_in, min(5, len(used_in)))
    
    # 提取这些位置的代码片段
    usage_snippets = extract_macro_usage_snippets(macro_name, selected_usages, project_path)
    
    # 格式化代码片段
    usage_snippets_str = ""
    if usage_snippets:
        for file_path, snippet in usage_snippets.items():
            usage_snippets_str += f"\n// === {file_path} 中的使用示例 ===\n"
            usage_snippets_str += "```c\n"
            usage_snippets_str += snippet
            usage_snippets_str += "\n```\n"
    else:
        usage_snippets_str = "无\n"
    
    return usage_snippets_str


def generate_macro_prompt(macro_info, project_path):
    """生成宏文档提示词"""
    # 提取宏使用的代码片段
    macro_name = macro_info["macro"]
    used_in = macro_info.get("used_in", [])
    
    # 生成宏使用示例
    usage_examples = generate_macro_usage_examples(macro_name, used_in, project_path)
    
    # 生成完整的宏定义
    macro_content = macro_info["content"]
    if macro_content:
        # 如果宏有内容，则生成完整的#define语句
        # 处理多行宏定义，添加续行符
        lines = macro_content.split('\n')
        if len(lines) > 1:
            # 多行宏定义
            macro_definition_lines = [f"#define {macro_name} {lines[0]} \\"]
            for i in range(1, len(lines)-1):
                # 在每行末尾添加续行符（除了最后一行）
                macro_definition_lines.append(f"    {lines[i]} \\")
            # 最后一行不加续行符
            if len(lines) > 1:
                macro_definition_lines.append(f"    {lines[-1]}")
            macro_definition = "\n".join(macro_definition_lines)
        else:
            # 单行宏定义
            macro_definition = f"#define {macro_name} {macro_content}"
    else:
        # 如果宏没有内容（如包含保护宏），则只生成宏名称
        macro_definition = f"#define {macro_name}"
    
    # 读取提示词模板
    try:
        # 首先尝试在当前目录查找模板文件
        with open("macro_doc_prompt_template.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        # 如果在当前目录找不到，尝试在codedatasetmaker目录中查找
        try:
            template_path = os.path.join(os.path.dirname(__file__), "macro_doc_prompt_template.txt")
            with open(template_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            # 如果都找不到，报错退出
            print("错误: 找不到宏文档提示词模板文件 'macro_doc_prompt_template.txt'")
            print("请确保模板文件存在于当前目录或 codedatasetmaker 目录中")
            raise
    
    # 填充模板
    prompt = prompt_template.format(
        macro_name=macro_info["macro"],
        macro_definition=macro_definition,
        macro_defined_in=macro_info["defined_in"],
        macro_used_in=json.dumps(macro_info["used_in"], indent=2, ensure_ascii=False),
        macro_usage_examples=usage_examples
    )
    
    return prompt


def generate_macro_doc(macro_info, output_dir, project_name, project_path, ai_config=None):
    """生成单个宏的文档"""
    macro_name = macro_info["macro"]

    if macro_name in processed_macros:
        print(f"已处理过宏 {macro_name}")
        return None
    
    processed_macros.add(macro_name)

    # 生成提示词
    prompt = generate_macro_prompt(macro_info, project_path)
    
    # 构建输出目录结构，按照宏定义的源文件路径组织
    defined_in = macro_info["defined_in"]
    # 移除文件扩展名，创建目录结构
    defined_in_no_ext = os.path.splitext(defined_in)[0]
    macro_output_dir = os.path.join(output_dir, project_name, "macros", defined_in_no_ext)
    os.makedirs(macro_output_dir, exist_ok=True)
    
    # 生成文件名（清理宏名称中的特殊字符）
    clean_macro_name = macro_name.replace("(", "_").replace(")", "_").replace(",", "_").replace(" ", "_")
    prompt_file_name = f"{clean_macro_name}_prompt.txt"
    doc_file_name = f"{clean_macro_name}_doc.md"
    
    # 保存提示词到文件
    prompt_file_path = os.path.join(macro_output_dir, prompt_file_name)
    with open(prompt_file_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    
    print(f"已生成宏 '{macro_name}' 的文档提示词文件: {prompt_file_path}")
    
    # 如果提供了AI配置，则调用AI API生成文档
    if ai_config:
        print(f"正在调用AI API生成宏 '{macro_name}' 的文档...")
        response = call_ai_api(prompt, ai_config)
        if response:
            # 保存AI生成的文档
            doc_file_path = os.path.join(macro_output_dir, doc_file_name)
            if save_ai_response(response, doc_file_path):
                print(f"已生成宏 '{macro_name}' 的AI文档: {doc_file_path}")
            else:
                print(f"AI API调用成功，但保存文档时出现问题")
        else:
            print(f"AI API调用失败，将仅保留提示词文件")
    
    return prompt_file_path


def main():
    parser = argparse.ArgumentParser(description="宏文档生成器")
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
    
    macro_info_path = os.path.join(output_dir, project_name, "macro_info.json")
    
    # 加载必要的JSON文件
    macro_info = load_json_file(macro_info_path)
    if macro_info is None:
        return
    
    # 加载AI配置
    ai_config = load_ai_config(args.ai_config)
    
    # 为每个宏生成文档
    for macro in macro_info:
        print(f"正在处理宏: {macro['macro']}")
        try:
            generate_macro_doc(macro, output_dir, project_name, args.project_path, ai_config)
        except Exception as e:
            print(f"处理宏 '{macro['macro']}' 时出错: {e}")


if __name__ == "__main__":
    main()
