#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
启动文件解析模块
用于解析ARM Cortex-M系列微控制器的启动文件，提取中断向量表、入口函数等信息
"""

import os
import sys
import json
import re
from xml.etree import ElementTree as ET

# 添加上级目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入工具模块
from .utils import load_ai_config, call_ai_api, save_ai_response
from . import debug, info, warning, error, critical


def find_startup_file(project_path):
    """
    在项目中查找启动文件
    
    Args:
        project_path (str): 项目路径
        
    Returns:
        str: 启动文件路径，如果未找到则返回None
    """
    # 查找常见的启动文件名
    common_startup_names = [
        "lcm32f037_startup.s",
        "startup_LCM32F0xx.s",
        "lcm32f0xx_startup.s",
        "startup.s",
        "startup.S"
    ]
    
    # 首先尝试从项目配置文件中查找
    startup_file = find_startup_in_config(project_path)
    if startup_file and os.path.exists(startup_file):
        return startup_file
    
    # 如果配置文件中没有找到，则在项目目录中搜索
    search_paths = [
        os.path.join(project_path, "Device", "Source", "ARM"),
        os.path.join(project_path, "Source"),
        os.path.join(project_path, "src"),
        os.path.join(project_path, "startup"),
        project_path
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file in common_startup_names:
                        return os.path.join(root, file)
    
    # 如果还是没找到，尝试查找所有.s或.S文件
    for path in search_paths:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith(('.s', '.S')):
                        # 检查文件内容是否包含启动相关的关键词
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if any(keyword in content for keyword in ['Reset_Handler', 'Vector', '__initial_sp']):
                                    return file_path
                        except Exception as e:
                            warning(f"无法读取文件 {file_path}: {e}")
    
    return None


def find_startup_in_config(project_path):
    """
    从项目配置文件中查找启动文件路径
    
    Args:
        project_path (str): 项目路径
        
    Returns:
        str: 启动文件路径，如果未找到则返回None
    """
    # 查找常见的项目配置文件
    config_files = [
        os.path.join(project_path, "Project", "base_proj", "base.uvprojx"),
        os.path.join(project_path, "*.uvprojx"),
        os.path.join(project_path, "*.uvproj"),
        os.path.join(project_path, "*.ewp"),
        os.path.join(project_path, "Makefile"),
        os.path.join(project_path, "CMakeLists.txt")
    ]
    
    for config_file_pattern in config_files:
        if '*' in config_file_pattern:
            # 处理通配符
            import glob
            matches = glob.glob(config_file_pattern)
            for config_file in matches:
                if os.path.exists(config_file):
                    startup_file = parse_config_for_startup(config_file)
                    if startup_file:
                        # 处理相对路径
                        if not os.path.isabs(startup_file):
                            startup_file = os.path.normpath(os.path.join(os.path.dirname(config_file), startup_file))
                        return startup_file
        else:
            if os.path.exists(config_file_pattern):
                startup_file = parse_config_for_startup(config_file_pattern)
                if startup_file:
                    # 处理相对路径
                    if not os.path.isabs(startup_file):
                        startup_file = os.path.normpath(os.path.join(os.path.dirname(config_file_pattern), startup_file))
                    return startup_file
    
    return None


def parse_config_for_startup(config_file):
    """
    解析配置文件以查找启动文件
    
    Args:
        config_file (str): 配置文件路径
        
    Returns:
        str: 启动文件路径，如果未找到则返回None
    """
    try:
        if config_file.endswith(('.uvprojx', '.uvproj')):
            # 解析Keil项目文件
            tree = ET.parse(config_file)
            root = tree.getroot()
            
            # 查找startup组中的启动文件
            for group_elem in root.iter('Group'):
                group_name = group_elem.find('GroupName')
                if group_name is not None and group_name.text == 'startup':
                    # 在startup组中查找文件
                    for file_elem in group_elem.iter('File'):
                        file_path_elem = file_elem.find('FilePath')
                        if file_path_elem is not None:
                            file_path = file_path_elem.text
                            if file_path and file_path.endswith(('.s', '.S')):
                                return file_path
            
            # 如果没有找到startup组，则查找文件名包含startup的文件
            for file_elem in root.iter('File'):
                file_name = file_elem.find('FileName')
                file_path = file_elem.find('FilePath')
                
                if file_name is not None and file_path is not None:
                    if 'startup' in file_name.text.lower() and file_path.text.endswith(('.s', '.S')):
                        return file_path.text
                        
        elif config_file.endswith('.ewp'):
            # 解析IAR项目文件
            tree = ET.parse(config_file)
            root = tree.getroot()
            
            # 查找启动文件
            for file_elem in root.iter('file'):
                if 'name' in file_elem.attrib:
                    file_path = file_elem.attrib['name']
                    if 'startup' in file_path.lower() and file_path.endswith(('.s', '.S')):
                        return file_path
                        
        elif config_file.endswith('Makefile'):
            # 解析Makefile
            with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # 查找ASM_SOURCES或STARTUP相关的行
                match = re.search(r'(ASM_SOURCES|STARTUP).*?=\s*(.*?\.s)', content, re.IGNORECASE)
                if match:
                    return match.group(2)
                    
        elif config_file.endswith('CMakeLists.txt'):
            # 解析CMakeLists.txt
            with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # 查找汇编源文件
                match = re.search(r'set\s*\(\s*(ASM_SOURCES|STARTUP).*?\s+(.*?\.s)', content, re.IGNORECASE | re.DOTALL)
                if match:
                    return match.group(2)
    except Exception as e:
        warning(f"解析配置文件 {config_file} 时出错: {e}")
    
    return None


def extract_startup_info(startup_file_path):
    """
    提取启动文件中的关键信息
    
    Args:
        startup_file_path (str): 启动文件路径
        
    Returns:
        dict: 包含启动文件信息的字典
    """
    try:
        with open(startup_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return {
            "content": content,
            "startup_file": startup_file_path
        }
    except Exception as e:
        error(f"提取启动文件信息时出错: {e}")
        return None


def extract_vector_table(content):
    """
    从启动文件内容中提取中断向量表
    
    Args:
        content (str): 启动文件内容
        
    Returns:
        list: 中断向量表列表
    """
    vector_table = []
    
    # 查找中断向量表区域，使用更精确的正则表达式
    vector_section_match = re.search(r'__Vectors\s+(.*?)(__Vectors_End|__Vectors_Size)', content, re.DOTALL)
    
    if vector_section_match:
        vector_content = vector_section_match.group(1)
        # 提取DCD指令后的函数名
        # 使用更精确的正则表达式匹配DCD指令，包括可能的注释和空格
        dcd_matches = re.findall(r'DCD\s+(\w+)', vector_content)
        for i, func_name in enumerate(dcd_matches):
            vector_table.append({
                "index": i,
                "handler": func_name
            })
    
    return vector_table


def extract_entry_function(content):
    """
    从启动文件内容中提取入口函数名
    
    Args:
        content (str): 启动文件内容
        
    Returns:
        str: 入口函数名
    """
    # 查找Reset_Handler作为入口函数
    reset_handler_match = re.search(r'Reset_Handler\s+PROC', content)
    if reset_handler_match:
        return "Reset_Handler"
    
    # 查找其他可能的入口函数
    entry_matches = re.findall(r'(\w+)\s+PROC', content)
    if entry_matches:
        # 通常第一个PROC就是入口函数
        return entry_matches[0]
    
    return None


def extract_exported_functions(content):
    """
    从启动文件内容中提取导出函数表
    
    Args:
        content (str): 启动文件内容
        
    Returns:
        list: 导出函数列表
    """
    exported_functions = []
    
    # 查找EXPORT指令后的函数名
    export_matches = re.findall(r'EXPORT\s+(\w+)', content)
    for func_name in export_matches:
        exported_functions.append(func_name)
    
    return exported_functions


def extract_weak_functions(content):
    """
    从启动文件内容中提取WEAK函数信息
    
    Args:
        content (str): 启动文件内容
        
    Returns:
        list: WEAK函数列表
    """
    weak_functions = []
    
    # 查找带有[WEAK]标记的EXPORT指令
    weak_matches = re.findall(r'EXPORT\s+(\w+)\s*\[WEAK\]', content)
    for func_name in weak_matches:
        weak_functions.append(func_name)
    
    return weak_functions


def generate_ai_prompt(startup_info):
    """
    生成AI分析的提示词
    
    Args:
        startup_info (dict): 启动文件信息
        
    Returns:
        str: AI提示词
    """
    prompt = f"""请分析以下ARM Cortex-M微控制器启动文件的内容，并以严格的JSON格式输出结果：

启动文件路径: {startup_info.get('startup_file', 'Unknown')}

启动文件原始内容:
```
{startup_info.get('content', '')}
```

请从上述启动文件中提取以下信息，并按照以下JSON格式输出分析结果：
{{
  "vector_table": [
    {{
      "index": 0,
      "handler": "函数名",
      "description": "中断处理函数描述"
    }}
  ],
  "entry_function": "入口函数名",
  "entry_function_calls": [
    "被入口函数调用的函数名"
  ],
  "exported_functions": [
    {{
      "name": "函数名",
      "description": "函数描述",
      "is_weak": true
    }}
  ],
  "analysis": "整体分析描述"
}}

请注意：
- entry_function_calls: 入口函数（通常是Reset_Handler）调用的函数列表
- exported_functions: 所有通过EXPORT指令导出的函数，每个函数都应包含is_weak字段来标识是否为弱函数（带有[WEAK]标记）

请确保输出是严格的JSON格式，不要包含任何额外的文本或解释。
"""
    
    return prompt


def main(project_path=None):
    """
    主函数
    
    Args:
        project_path (str): 项目路径
        
    Returns:
        bool: 执行成功返回True，否则返回False
    """
    # 如果没有提供项目路径，则从命令行参数获取
    if project_path is None:
        if len(sys.argv) < 2:
            print("用法: python parse_startup.py <项目路径>")
            sys.exit(1)
        
        project_path = sys.argv[1]
        if not os.path.exists(project_path):
            print(f"错误: 项目路径不存在: {project_path}")
            sys.exit(1)
    
    info(f"正在分析项目Startup: {project_path}")
    
    # 查找启动文件
    startup_file = find_startup_file(project_path)
    if not startup_file:
        error("未找到启动文件")
        return False
    
    info(f"找到启动文件: {startup_file}")
    
    # 提取启动文件信息
    startup_info = extract_startup_info(startup_file)
    if not startup_info:
        error("无法提取启动文件信息")
        return False
    
    # 生成AI提示词
    prompt = generate_ai_prompt(startup_info)
    
    # 确保output目录存在
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 创建项目特定的输出目录
    project_name = os.path.basename(os.path.abspath(project_path))
    project_output_dir = os.path.join(output_dir, project_name)
    if not os.path.exists(project_output_dir):
        os.makedirs(project_output_dir)

    result_file = os.path.join(project_output_dir, 'startup_analysis_result.json')
    if os.path.exists(result_file):
        info(f"Result file {result_file} already exists. Skipping analysis.")
        return True

    # 加载AI配置
    ai_config = load_ai_config()
    if not ai_config:
        # 如果没有AI配置，只保存提示词
        prompt_file = os.path.join(project_output_dir, 'startup_analysis_prompt.txt')
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)
        info(f"已生成提示词文件: {prompt_file}")
        return True

    # 调用AI API
    info("正在调用AI分析...")
    response = call_ai_api(prompt, ai_config)

    # 保存AI响应
    if response:
        success = save_ai_response(response, result_file)
        if success:
            info(f"已保存AI分析结果: {result_file}")
        else:
            error("保存AI分析结果失败")
            return False
    else:
        warning("AI分析失败，只保存提示词")
        prompt_file = os.path.join(project_output_dir, 'startup_analysis_prompt.txt')
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)
        info(f"已生成提示词文件: {prompt_file}")

    return True


if __name__ == "__main__":
    success = main()
    if success:
        print("启动文件分析完成")
        sys.exit(0)
    else:
        print("启动文件分析失败")
        sys.exit(1)
