#!/usr/bin/env python3

import os
import json
import argparse

# 导入日志模块
from . import debug, info, warning, error, critical

def should_ignore_file(filename):
    """判断是否应该忽略该文件"""
    # 忽略的文件扩展名
    ignore_extensions = {
        '.o', '.obj', '.exe', '.dll', '.so', '.dylib',  # 编译产物
        '.pyc', '.pyo', '.pyd',  # Python字节码
        '.log', '.tmp', '.temp',  # 日志和临时文件
        '.gitignore', '.DS_Store', 'Thumbs.db'  # 系统文件
    }
    
    # 忽略的文件名
    ignore_filenames = {
        '.git', '__pycache__', '.vscode', '.idea',  # 目录和特殊文件
        'node_modules', 'build', 'dist',  # 构建目录
        '.env', '.venv'  # 环境文件
    }
    
    # 检查文件扩展名
    _, ext = os.path.splitext(filename)
    if ext.lower() in ignore_extensions:
        return True
        
    # 检查文件名
    if filename in ignore_filenames:
        return True
        
    return False

def should_ignore_dir(dirname):
    """判断是否应该忽略该目录"""
    # 忽略的目录名
    ignore_dirs = {
        '.git', '__pycache__', '.vscode', '.idea',
        'node_modules', 'build', 'dist',
        '.env', '.venv', 'venv', 'env'
    }
    
    return dirname in ignore_dirs

def generate_file_tree(startpath, max_depth=None, current_depth=0):
    """生成文件树"""
    if max_depth is not None and current_depth > max_depth:
        return []
        
    file_tree = []
    
    try:
        items = sorted(os.listdir(startpath))
    except PermissionError:
        return [{"name": "[Permission Denied]", "type": "error"}]
    
    for item in items:
        if should_ignore_file(item) or should_ignore_dir(item):
            continue
            
        item_path = os.path.join(startpath, item)
        
        if os.path.isdir(item_path):
            subdir_tree = generate_file_tree(item_path, max_depth, current_depth + 1)
            file_tree.append({
                "name": item,
                "type": "directory",
                "children": subdir_tree
            })
        else:
            file_tree.append({
                "name": item,
                "type": "file"
            })
    
    return file_tree

def print_file_tree(tree, prefix="", is_last=True):
    """打印文件树"""
    for i, item in enumerate(tree):
        is_last_item = (i == len(tree) - 1)
        current_prefix = "└── " if is_last_item else "├── "
        
        info(prefix + current_prefix + item["name"])
        
        if item["type"] == "directory":
            extension = "    " if is_last_item else "│   "
            if "children" in item:
                print_file_tree(item["children"], prefix + extension, is_last_item)

def save_to_json(tree, output_file):
    """保存文件树到JSON文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tree, f, indent=2, ensure_ascii=False)

def save_to_text(tree, output_file):
    """保存文件树到文本文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(".\n")
        _write_text_tree(tree, f)

def _write_text_tree(tree, file_handle, prefix="", is_last=True):
    """递归写入文本树到文件"""
    for i, item in enumerate(tree):
        is_last_item = (i == len(tree) - 1)
        current_prefix = "└── " if is_last_item else "├── "
        
        file_handle.write(prefix + current_prefix + item["name"] + "\n")
        
        if item["type"] == "directory":
            extension = "    " if is_last_item else "│   "
            if "children" in item:
                _write_text_tree(item["children"], file_handle, prefix + extension, is_last_item)

def main():
    parser = argparse.ArgumentParser(description='Generate project file tree')
    parser.add_argument('project_dir', help='Path to the project directory')
    parser.add_argument('-o', '--output', help='Output JSON file name (without path)')
    parser.add_argument('-d', '--depth', type=int, help='Maximum depth of the tree')
    
    args = parser.parse_args()
    
    project_dir = args.project_dir
    
    if not os.path.exists(project_dir):
        error(f"Error: Directory '{project_dir}' does not exist.")
        return
    
    if not os.path.isdir(project_dir):
        error(f"Error: '{project_dir}' is not a directory.")
        return
    
    # 获取项目名称
    project_name = os.path.basename(os.path.abspath(project_dir))
    
    info(f"Project file tree for: {os.path.abspath(project_dir)}")
    print()
    
    # 生成文件树
    file_tree = generate_file_tree(project_dir, args.depth)
    
    # 打印文件树
    print(".")
    print_file_tree(file_tree)
    
    # 确保output目录存在
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 创建项目特定的输出目录
    project_output_dir = os.path.join(output_dir, project_name)
    if not os.path.exists(project_output_dir):
        os.makedirs(project_output_dir)
    
    # 保存到JSON文件
    if args.output:
        # 生成完整的输出路径
        output_file = os.path.join(project_output_dir, args.output)
        save_to_json(file_tree, output_file)
        info(f"\nFile tree saved to: {output_file}")
    else:
        # 默认输出为文本格式
        default_output = "file_tree.txt"
        output_file = os.path.join(project_output_dir, default_output)
        save_to_text(file_tree, output_file)
        info(f"\nFile tree saved to: {output_file} (default)")

if __name__ == "__main__":
    main()
