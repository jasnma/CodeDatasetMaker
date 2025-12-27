#!/usr/bin/env python3
"""
结构体文档生成器
根据struct_info.json生成结构体级文档
"""

import json
import os
import argparse
from collections import defaultdict
from openai import OpenAI
from openai import APIError, APIConnectionError, RateLimitError
from c_parser_utils import find_doc_comment_start


# 定义一个变量记住已经处理过的结构体
processed_structs = set()


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


def read_struct_definition_from_source(project_path, defined_in, start_line, end_line):
    """从源文件中读取结构体定义"""
    try:
        # 构建完整的文件路径
        file_path = os.path.join(project_path, defined_in)

        # 如果仍然没有找到文件，返回None
        if not os.path.exists(file_path):
            print(f"警告: 找不到源文件 {file_path}")
            return None

        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 查找文档注释的起始位置
        comment_start = find_doc_comment_start(lines, start_line)
        
        # 确定实际的起始行索引
        actual_start_idx = max(0, start_line - 1)
        if comment_start is not None:
            actual_start_idx = comment_start - 1
        
        # 提取指定行范围的内容
        # 注意：行号通常是从1开始的，而列表索引是从0开始的
        end_idx = min(len(lines), end_line)
        
        # 提取结构体定义及注释
        struct_definition = ''.join(lines[actual_start_idx:end_idx])
        
        return struct_definition.strip()
    except Exception as e:
        print(f"读取源文件时出错: {e}")
        return None


def read_function_definition_from_source(project_path, defined_in, start_line, end_line):
    """从源文件中读取函数定义"""
    try:
        # 构建完整的文件路径
        file_path = os.path.join(project_path, defined_in)

        # 如果仍然没有找到文件，返回None
        if not os.path.exists(file_path):
            print(f"警告: 找不到源文件 {file_path}")
            return None

        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 查找文档注释的起始位置
        comment_start = find_doc_comment_start(lines, start_line)
        
        # 确定实际的起始行索引
        actual_start_idx = max(0, start_line - 1)
        if comment_start is not None:
            actual_start_idx = comment_start - 1
        
        # 提取指定行范围的内容
        # 注意：行号通常是从1开始的，而列表索引是从0开始的
        end_idx = min(len(lines), end_line)
        
        # 提取函数定义及注释
        function_definition = ''.join(lines[actual_start_idx:end_idx])
        
        return function_definition.strip()
    except Exception as e:
        print(f"读取源文件时出错: {e}")
        return None


def generate_struct_definition(struct_info, project_path):
    """根据结构体信息生成结构体定义代码"""
    # 尝试从源文件中读取结构体定义
    defined_in = struct_info.get("defined_in")
    start_line = struct_info.get("start_line")
    end_line = struct_info.get("end_line")

    if defined_in and start_line and end_line:
        struct_definition = read_struct_definition_from_source(project_path, defined_in, start_line, end_line)
        if struct_definition:
            return struct_definition

    return None


def find_function_info_in_fileinfo(fileinfo_data, func_name, file_name):
    """在fileinfo数据中查找函数信息"""
    # 查找匹配的文件和函数
    for file_info in fileinfo_data:
        if file_info.get("file") == file_name:
            for func in file_info.get("functions", []):
                if func.get("name") == func_name:
                    return func
    
    return None


def load_fileinfo_data(project_path):
    """加载fileinfo.json数据"""
    # 构建fileinfo.json的路径
    project_name = os.path.basename(os.path.abspath(project_path))
    fileinfo_path = os.path.join("output", project_name, "file_info.json")
    
    # 如果找不到fileinfo.json，返回空列表
    if not os.path.exists(fileinfo_path):
        print(f"警告: 找不到fileinfo.json文件")
        return []
    
    # 读取fileinfo.json
    try:
        with open(fileinfo_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取fileinfo.json时出错: {e}")
        return []


def load_global_var_info_data(project_path):
    """加载global_var_info.json数据"""
    # 构建global_var_info.json的路径
    project_name = os.path.basename(os.path.abspath(project_path))
    global_var_info_path = os.path.join("output", project_name, "global_var_info.json")
    
    # 如果找不到global_var_info.json，返回空列表
    if not os.path.exists(global_var_info_path):
        print(f"警告: 找不到global_var_info.json文件")
        return []
    
    # 读取global_var_info.json
    try:
        with open(global_var_info_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取global_var_info.json时出错: {e}")
        return []


def generate_struct_prompt(struct_info, project_path, global_var_info_data, fileinfo_data):
    """生成结构体文档提示词"""
    # 读取提示词模板
    try:
        # 首先尝试在当前目录查找模板文件
        with open("struct_doc_prompt_template.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        # 如果在当前目录找不到，尝试在codedatasetmaker目录中查找
        try:
            template_path = os.path.join(os.path.dirname(__file__), "struct_doc_prompt_template.txt")
            with open(template_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            # 如果都找不到，报错退出
            print("错误: 找不到结构体文档提示词模板文件 'struct_doc_prompt_template.txt'")
            print("请确保模板文件存在于当前目录或 codedatasetmaker 目录中")
            raise
    
    # 获取结构体名称
    struct_name = ""
    if "struct" in struct_info:
        struct_name = struct_info["struct"]
    elif "union" in struct_info:
        struct_name = struct_info["union"]
    elif "enum" in struct_info:
        struct_name = struct_info["enum"]
    
    # 生成结构体定义
    struct_definition = generate_struct_definition(struct_info, project_path)
    
    # 获取定义文件
    defined_in = struct_info.get("defined_in", "未知文件")
    
    # 获取使用位置列表
    used_by_list = struct_info.get("used_by", [])
    
    # 找到全局结构体类型的全局变量，并把全局变量引用的函数也加入结构体引用列表
    struct_type = ""
    if "struct" in struct_info:
        struct_type = struct_info["struct"]
    elif "union" in struct_info:
        struct_type = struct_info["union"]
    elif "enum" in struct_info:
        struct_type = struct_info["enum"]
    
    # 遍历全局变量信息
    for global_var in global_var_info_data:
        # 检查全局变量的类型是否与当前结构体类型匹配
        if global_var.get("type") == struct_type:
            # 将全局变量的使用位置添加到used_by_list中
            used_by_list.extend(global_var.get("used_in", []))
    
    # 去重
    used_by_list = list(set(used_by_list))
    
    used_by_str = "\n".join([f"- {item}" for item in used_by_list]) if used_by_list else "无"
    
    # 查找并读取引用函数的代码
    referenced_functions = ""
    function_references = []
    
    # 过滤掉"global"引用
    filtered_used_by = [item for item in used_by_list if not item.endswith(":global")]
    
    # 如果引用函数超过10个，随机选择10个
    import random
    if len(filtered_used_by) > 10:
        selected_functions = random.sample(filtered_used_by, 10)
    else:
        selected_functions = filtered_used_by
    
    # 为每个选中的函数查找其源代码
    for func_ref in selected_functions:
        # 解析函数引用信息
        # 格式为 "file.c:function_name"
        parts = func_ref.split(":")
        if len(parts) == 2:
            file_name = parts[0]
            func_name = parts[1]
            # 查找函数定义的源代码
            # 通过fileinfo.json获取函数的详细信息
            func_info = find_function_info_in_fileinfo(fileinfo_data, func_name, file_name)
            if func_info:
                func_start_line = func_info.get("start_line", 1)
                func_end_line = func_info.get("end_line", 100)  # 默认结束行为100
                
                try:
                    function_code = read_function_definition_from_source(
                        project_path, file_name, func_start_line, func_end_line
                    )
                    if function_code:
                        function_references.append(f"// 函数 {func_ref} :\n{function_code}")
                except Exception as e:
                    print(f"读取函数 {func_name} 的源代码时出错: {e}")
            else:
                print(f"未在fileinfo.json中找到函数 {func_name} 的信息")
    
    # 将引用函数代码组合成字符串
    referenced_functions = "\n\n".join(function_references) if function_references else "无"
    
    # 将结构体信息转换为JSON字符串
    import json
    struct_info_json = json.dumps(struct_info, ensure_ascii=False, indent=2)
    
    # 填充模板
    prompt = prompt_template.format(
        struct_name=struct_name,
        struct_definition=struct_definition,
        defined_in=defined_in,
        used_by_list=used_by_str,
        struct_info=struct_info_json,
        referenced_functions=referenced_functions
    )
    
    return prompt


def generate_struct_doc(struct_info, project_name, output_dir, ai_config=None, project_path=None, global_var_info_data=None, fileinfo_data=None):
    """生成单个结构体的文档"""
    # 获取结构体名称
    struct_name = ""
    if "struct" in struct_info:
        struct_name = struct_info["struct"]
    elif "union" in struct_info:
        struct_name = struct_info["union"]
    elif "enum" in struct_info:
        struct_name = struct_info["enum"]
    
    if not struct_name:
        print("错误: 无法确定结构体名称")
        return None
    
    if struct_name in processed_structs:
        print(f"已处理过结构体 {struct_name}")
        return None
    
    processed_structs.add(struct_name)
    
    # 生成提示词
    prompt = generate_struct_prompt(struct_info, project_path, global_var_info_data, fileinfo_data)
    
    # 构建输出目录结构
    struct_output_dir = os.path.join(output_dir, project_name, "structs")
    os.makedirs(struct_output_dir, exist_ok=True)
    
    # 生成文件名
    prompt_file_name = f"{struct_name}_prompt.txt"
    doc_file_name = f"{struct_name}_doc.md"
    
    # 保存提示词到文件
    prompt_file_path = os.path.join(struct_output_dir, prompt_file_name)
    with open(prompt_file_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    
    print(f"已生成结构体 '{struct_name}' 的文档提示词文件: {prompt_file_path}")
    
    # 如果提供了AI配置，则调用AI API生成文档
    if ai_config:
        print(f"正在调用AI API生成结构体 '{struct_name}' 的文档...")
        response = call_ai_api(prompt, ai_config)
        if response:
            # 保存AI生成的文档
            doc_file_path = os.path.join(struct_output_dir, doc_file_name)
            if save_ai_response(response, doc_file_path):
                print(f"已生成结构体 '{struct_name}' 的AI文档: {doc_file_path}")
            else:
                print(f"AI API调用成功，但保存文档时出现问题")
        else:
            print(f"AI API调用失败，将仅保留提示词文件")
    
    return prompt_file_path


def main():
    parser = argparse.ArgumentParser(description="结构体文档生成器")
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
    
    struct_info_path = os.path.join(output_dir, project_name, "struct_info.json")
    
    # 加载必要的JSON文件
    struct_info = load_json_file(struct_info_path)
    if struct_info is None:
        return
    
    # 加载AI配置
    ai_config = load_ai_config(args.ai_config)
    
    # 加载global_var_info.json数据
    global_var_info_data = load_global_var_info_data(args.project_path)
    
    # 加载fileinfo数据
    fileinfo_data = load_fileinfo_data(args.project_path)
    
    # 为每个结构体生成文档
    for struct_item in struct_info:
        print(f"正在处理结构体: {struct_item.get('struct', struct_item.get('union', struct_item.get('enum', '未知')))}")
        try:
            generate_struct_doc(struct_item, project_name, output_dir, ai_config, args.project_path, global_var_info_data, fileinfo_data)
        except Exception as e:
            print(f"处理结构体时出错: {e}")


if __name__ == "__main__":
    main()
