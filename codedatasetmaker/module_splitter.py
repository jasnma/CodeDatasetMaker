#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import argparse
import sys
from collections import defaultdict


def load_json_file(file_path):
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误: 解析JSON文件失败 {file_path}: {e}")
        sys.exit(1)


def get_function_info(file_info, function_name):
    """根据函数名获取函数信息"""
    for file_data in file_info:
        for func in file_data.get('functions', []):
            if func['name'] == function_name:
                return {
                    'file': file_data['file'],
                    'start_line': func['start_line'],
                    'end_line': func['end_line']
                }
    return None


def get_directory(file_path):
    """获取文件所在目录"""
    return os.path.dirname(file_path)

def get_file_size(file_path, source_dir):
    """获取文件大小（字节）"""
    try:
        full_path = os.path.join(source_dir, file_path)
        return os.path.getsize(full_path)
    except OSError:
        return 0

def find_common_prefix(file_paths):
    """查找文件路径列表中的公共前缀"""
    if not file_paths:
        return ""
    
    # 获取文件名（不包括扩展名）
    file_names = [os.path.splitext(os.path.basename(path))[0] for path in file_paths]
    
    if len(file_names) == 1:
        return file_names[0]
    
    # 查找公共前缀
    prefix = ""
    min_len = min(len(name) for name in file_names)
    
    for i in range(min_len):
        char = file_names[0][i]
        if all(name[i] == char for name in file_names):
            prefix += char
        else:
            break
    
    # 如果前缀太短，返回空字符串
    # 但如果前缀以_结尾，移除下划线
    if len(prefix) > 2:
        if prefix.endswith('_'):
            prefix = prefix[:-1]
        return prefix
    return ""

def build_call_graph_map(call_graph):
    """构建调用图映射"""
    # 创建一个调用映射，方便查找
    call_map = defaultdict(set)
    reverse_call_map = defaultdict(set)
    
    for caller, callees in call_graph.items():
        caller_parts = caller.split(':')
        if len(caller_parts) >= 2:
            caller_func = caller_parts[1]
            for callee in callees:
                callee_parts = callee.split(':')
                if len(callee_parts) >= 2:
                    callee_func = callee_parts[1]
                    call_map[caller_func].add(callee_func)
                    reverse_call_map[callee_func].add(caller_func)
    
    return call_map, reverse_call_map

def find_connected_components_with_size_limit(files, file_calls, file_details, source_dir, max_size=128*1024):
    """查找连通分量（模块），考虑文件大小限制"""
    visited = set()
    components = []
    
    def dfs(file_path, component, current_size):
        visited.add(file_path)
        component.append(file_path)
        
        # 计算添加此文件后的总大小
        file_size = get_file_size(file_path, source_dir)
        current_size[0] += file_size
        
        # 查找所有相连的文件
        for neighbor in file_calls.get(file_path, []):
            if neighbor in files and neighbor not in visited:
                # 检查添加邻居文件是否会超过大小限制
                neighbor_size = get_file_size(neighbor, source_dir)
                if current_size[0] + neighbor_size <= max_size:
                    dfs(neighbor, component, current_size)
    
    # 对所有文件进行DFS查找连通分量
    for file_path in files:
        if file_path not in visited:
            component = []
            current_size = [0]  # 使用列表以便在递归中修改
            dfs(file_path, component, current_size)
            components.append(component)
    
    return components

def analyze_module_boundaries(source_dir):
    """分析模块边界"""
    # 构建metadata目录路径
    metadata_dir = os.path.join('output', os.path.basename(source_dir))

    # 构建文件路径
    call_graph_path = os.path.join(metadata_dir, 'call_graph.json')
    file_info_path = os.path.join(metadata_dir, 'file_info.json')

    # 检查metadata目录是否存在
    if not os.path.exists(metadata_dir):
        print(f"错误: 找不到metadata目录 {metadata_dir}")
        sys.exit(1)

    # 检查文件是否存在
    if not os.path.exists(call_graph_path):
        print(f"错误: 在目录 {metadata_dir} 中找不到 call_graph.json")
        sys.exit(1)

    if not os.path.exists(file_info_path):
        print(f"错误: 在目录 {metadata_dir} 中找不到 file_info.json")
        sys.exit(1)

    # 加载JSON文件
    call_graph = load_json_file(call_graph_path)
    file_info = load_json_file(file_info_path)

    # 构建文件调用图映射
    file_call_map = defaultdict(set)

    # 构建文件间的调用关系
    for caller, callees in call_graph.items():
        caller_parts = caller.split(':')
        if len(caller_parts) >= 2:
            caller_file = caller_parts[0]
            for callee in callees:
                callee_parts = callee.split(':')
                if len(callee_parts) >= 2:
                    callee_file = callee_parts[0]
                    if caller_file != callee_file:
                        file_call_map[caller_file].add(callee_file)

    # 按目录组织文件
    dir_files = defaultdict(list)
    file_details = {}
    init_files = []  # 存储包含初始化函数的文件

    # 声明变量，保存已经加入模块的文件
    added_files = set()
    
    # 将所有文件按目录分类，同时查找main函数和初始化函数所在的文件
    for file_data in file_info:
        file_path = file_data['file']
        directory = get_directory(file_path)
        file_details[file_path] = file_data

        # 检查是否有初始化函数 (main, init, config, setup等)
        init_function_names = ['main', 'init', 'initialize', 'config', 'configure', 'setup', 'start', 'begin']
        has_init_func = any(any(func['name'].lower().endswith(init_name) or 
                               func['name'].lower().startswith(init_name) or
                               init_name in func['name'].lower()
                               for init_name in init_function_names)
                           for func in file_data.get('functions', []))

        if has_init_func:
            init_files.append(file_path)
            added_files.add(file_path)
            continue

        dir_files[directory].append(file_path)
    
    # 分析结果存储
    modules = defaultdict(list)
    dependencies = defaultdict(set)
    module_counter = 0
    
    # 处理包含初始化函数的文件，并把它调用的同目录文件加入模块
    for init_file in init_files:
        # 使用文件名作为模块名
        file_name = os.path.basename(init_file)
        init_module_name = os.path.splitext(file_name)[0]
        
        # 初始化文件作为模块入口
        modules[init_module_name].append(init_file)
        added_files.add(init_file)

        # 分析初始化文件的依赖关系
        if init_file in file_call_map:
            directory = get_directory(init_file)
            for called_file in file_call_map[init_file]:
                # 如果文件在同一个目录，且没有初始化入口则加入当前模块
                if directory == get_directory(called_file) and called_file not in added_files:
                    modules[init_module_name].append(called_file)
                    added_files.add(called_file)

    # 对每个目录中的文件进行模块划分
    for directory, files in dir_files.items():
        # 构建该目录中文件的调用关系图
        local_file_calls = defaultdict(set)
        for file in files:
            if file in added_files:
                continue

            if file in file_call_map:
                # 只考虑同一目录内的调用关系
                for called_file in file_call_map[file]:
                    if called_file in files:
                        local_file_calls[file].add(called_file)
                        local_file_calls[called_file].add(file)  # 添加反向连接
            else:
                print(f"Warning: File '{file}' not found in file_call_map.")

        # 查找该目录中的连通分量（模块），考虑文件大小限制
        file_components = find_connected_components_with_size_limit(files, local_file_calls, file_details, source_dir)

        # 为每个连通分量创建一个模块
        for i, component in enumerate(file_components):
            # 根据组件大小确定模块名称
            if len(component) == 1:
                # 单文件模块使用文件名作为模块名
                file_name = os.path.basename(component[0])
                # 移除文件扩展名
                module_name = os.path.splitext(file_name)[0]
            else:
                # 多文件模块优先使用公共前缀
                common_prefix = find_common_prefix(component)
                dir_name = os.path.basename(directory) if directory else 'root'
                
                if common_prefix and len(common_prefix) > 2:  # 只有当前缀足够长时才使用
                    module_name = common_prefix
                else:
                    # 如果没有明显的公共前缀，使用目录名
                    if len(file_components) > 1:
                        # 如果同一目录下有多个多文件模块，添加数字编号
                        module_name = f"{dir_name}_{i+1}"
                    else:
                        # 否则直接使用目录名
                        module_name = dir_name
            
            # 添加文件到模块
            for file_path in component:
                if file_path in file_details:
                    modules[module_name].append(file_path)
            
            # 分析模块间依赖关系
            for file_path in component:
                if file_path in file_call_map:
                    for called_file in file_call_map[file_path]:
                        # 如果被调用文件不在当前模块中，记录依赖关系
                        in_current_module = False
                        for mod_files in modules[module_name]:
                            if called_file == mod_files:
                                in_current_module = True
                                break
                        
                        if not in_current_module:
                            # 找到被调用文件所属的模块
                            for other_module, other_files in modules.items():
                                if other_module != module_name:
                                    if called_file in other_files:
                                        dependencies[module_name].add(other_module)
                                        break
    
    # 遍历所有模块，确定他们的依赖关系
    for module_name, module_files in modules.items():
        for file in module_files:
            if file in file_call_map:
                called_files = file_call_map[file]
                # 找到被调用文件所属的模块
                for dependencies_module_name, dependencies_module_files in modules.items():
                    if dependencies_module_name == module_name:
                        continue

                    has_common = any(x in called_files for x in dependencies_module_files)
                    if has_common:
                        dependencies[module_name].add(dependencies_module_name)
                    

    # 补充在file_info.json中存在但在调用图中未出现的文件
    all_files_in_info = set()
    for file_data in file_info:
        directory = get_directory(file_data['file'])
        all_files_in_info.add(file_data['file'])
        
        # 查找是否已经在modules中
        found = False
        for module_files in modules.values():
            if file_data['file'] in module_files:
                found = True
                break

        if not found:
            # 添加未在调用图中出现的文件到相应目录的模块中
            # 找到该目录的第一个模块，或者创建一个新模块
            directory_modules = [mod for mod in modules.keys() 
                              if mod.startswith(os.path.basename(directory) if directory else 'root')]
            
            if directory_modules:
                # 添加到该目录的第一个模块
                module_name = directory_modules[0]
                modules[module_name].append(file_data['file'])
            else:
                # 创建新模块
                module_counter += 1
                module_name = f"{os.path.basename(directory) if directory else 'root'}_module_{module_counter}"
                modules[module_name].append(file_data['file'])

    return modules, dependencies


def print_module_analysis(modules, dependencies):
    """打印模块分析结果"""
    print("=" * 60)
    print("模块边界分析结果")
    print("=" * 60)
    
    for module, files in modules.items():
        print(f"\n模块: {module}")
        print("-" * 40)
        for file_path in files:
            print(f"  文件: {file_path}")
        
        # 打印依赖关系
        if module in dependencies and dependencies[module]:
            print(f"  依赖模块: {', '.join(sorted(dependencies[module]))}")
        else:
            print("  依赖模块: 无")


def export_module_structure(modules, dependencies, output_dir):
    """导出模块结构到文件"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 导出模块信息
    module_info = {}
    for module, files in modules.items():
        module_info[module] = {
            'files': files,
            'dependencies': list(dependencies.get(module, []))
        }
    
    output_file = os.path.join(output_dir, 'module_structure.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(module_info, f, indent=2, ensure_ascii=False)
    
    print(f"\n模块结构已导出到: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='分析C项目模块边界')
    parser.add_argument('project_dir', help='项目目录路径')
    parser.add_argument('-o', '--output', help='输出目录路径')
    
    args = parser.parse_args()
    
    # 验证项目目录是否存在
    if not os.path.isdir(args.project_dir):
        print(f"错误: 项目目录 {args.project_dir} 不存在")
        sys.exit(1)
    
    # 分析模块边界
    modules, dependencies = analyze_module_boundaries(args.project_dir)
    
    # 打印分析结果
    print_module_analysis(modules, dependencies)
    
    # 确定输出目录
    if args.output:
        output_dir = args.output
    else:
        # 默认输出目录为 output/{project_name}
        project_name = os.path.basename(args.project_dir)
        output_dir = os.path.join('output', project_name)
    
    # 导出结果
    export_module_structure(modules, dependencies, output_dir)


if __name__ == '__main__':
    main()
