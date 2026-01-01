#!/usr/bin/env python3

import argparse
import os
import json
import re
import sys
import time
import clang.cindex
from anytree import Node, RenderTree
import xml.etree.ElementTree as ET
from collections import defaultdict
from . import generate_file_tree
from .c_parser_utils import find_doc_comment_start, find_prev_effective_line
from dataclasses import dataclass

# 导入日志模块
from . import logger

@dataclass
class GlobalVarInfo:
    name: str
    type: str
    file: str
    is_definition: bool

@dataclass
class ParseFileResult:
    graph: defaultdict
    rel_path: str
    file_info: defaultdict
    struct_fields:defaultdict
    struct_uses: defaultdict[str, list]
    global_var_defs: dict[str, GlobalVarInfo]
    global_var_uses: defaultdict[str, list]
    macro_defs: defaultdict
    macro_uses: defaultdict[str, list]
    includes: defaultdict[str, set]


# 确保 libclang 已正确配置
try:
    # 尝试设置 libclang 路径（根据不同系统可能需要调整）
    if os.name == 'nt':  # Windows
        clang.cindex.Config.set_library_file('C:/Program Files/LLVM/bin/libclang.dll')
    elif os.uname().sysname == 'Darwin':  # macOS
        clang.cindex.Config.set_library_file('/usr/local/opt/llvm/lib/libclang.dylib')
    else:  # Linux
        clang.cindex.Config.set_library_file('/usr/lib/llvm-14/lib/libclang.so')
except:
    pass  # 如果设置失败，使用系统默认路径

def get_c_files(directory):
    """获取目录下所有C源文件"""
    c_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.c') or file.endswith('.cpp') or file.endswith('.cc'):
                c_files.append(os.path.join(root, file))
    return c_files

def process_union(node, project_root):
    union_name = node.spelling

    # 收集内嵌结构体、联合体和枚举信息
    embedded_childrens = {}
    # 收集联合体字段信息
    fields = []
    for child in node.get_children():
        if child.kind == clang.cindex.CursorKind.UNION_DECL:
            embedded_union_name = child.get_usr()
            child_name = child.spelling
            union_info = process_union(child, project_root)
            if union_info:
                # 构造包含联合体内部字段信息的类型描述
                field_type = {"union": union_info["fields"]}
                if child_name.startswith("union (anonymous"):
                    # 未命名字段，直接添加
                    fields.append({
                        "name":"",
                        "type": field_type
                    })
                else:
                    # 可能是命名字段等待后续的FIELD_DECL节点得到名字
                    if embedded_union_name in embedded_childrens:
                        # 没有被FIELD_DECL命中，但新的usr又相同，说明是匿名字段
                        old_field_type = embedded_childrens[embedded_union_name]
                        fields.append({
                            "name":"",
                            "type": old_field_type
                        })
                    embedded_childrens[embedded_union_name] = field_type
        elif (child.kind == clang.cindex.CursorKind.STRUCT_DECL):
            embedded_struct_name = child.get_usr()
            child_name = child.spelling
            struct_info = process_struct(child, project_root)
            if struct_info:
                field_type = {"struct": struct_info["fields"]}
                if child_name.startswith("struct (anonymous"):
                    # 未命名字段，直接添加
                    fields.append({
                        "name":"",
                        "type": field_type
                    })
                else:
                    # 可能是命名字段等待后续的FIELD_DECL节点得到名字
                    if embedded_struct_name in embedded_childrens:
                        # 没有被FIELD_DECL命中，但新的usr又相同，说明是匿名字段
                        old_field_type = embedded_childrens[embedded_struct_name]
                        fields.append({
                            "name":"",
                            "type": old_field_type
                        })
                    embedded_childrens[embedded_struct_name] = field_type
        elif (child.kind == clang.cindex.CursorKind.ENUM_DECL):
            embedded_enum_name = child.get_usr()
            enum_info = process_enum(child, project_root)
            if enum_info:
                field_type = {"enum": enum_info["values"]}
                embedded_childrens[embedded_enum_name] = field_type
        elif child.kind == clang.cindex.CursorKind.FIELD_DECL:
            field_name = child.spelling
            field_type = child.type.spelling
            type_user = child.type.get_canonical().get_declaration().get_usr()
            if (type_user in embedded_childrens):
                field_type = embedded_childrens[type_user]
                del embedded_childrens[type_user]

            if field_name and field_type:
                fields.append({"name": field_name, "type": field_type})

    if embedded_childrens:
        for child in embedded_childrens:
            fields.append({"name": "", "fields": embedded_childrens[child]})

    if union_name and fields:
        # 获取联合体定义的实际位置
        if node.location.file:
            node_file_path = os.path.abspath(node.location.file.name)
            try:
                definition_location = os.path.relpath(node_file_path, project_root)
            except ValueError:
                definition_location = node_file_path

        # 获取联合体定义的起止行号
        start_line = node.extent.start.line
        end_line = node.extent.end.line

        # 为联合体创建一个特殊的条目，与结构体分开
        return {
            "union": union_name,
            "fields": fields,
            "defined_in": definition_location,
            "start_line": start_line,
            "end_line": end_line
        }
    else:
        logger.warning(f"Warning: Skipping non-union node: {node.spelling}")
    
    return None

def process_struct(node, project_root):
    struct_name = node.spelling
    
    # 收集内嵌结构体、联合体和枚举信息
    embedded_childrens = {}
    # 收集结构体字段信息
    fields = []
    for child in node.get_children():
        if child.kind == clang.cindex.CursorKind.UNION_DECL and child.is_definition():
            embedded_union_name = child.get_usr()
            child_name = child.spelling
            union_info = process_union(child, project_root)
            if union_info:
                # 构造包含联合体内部字段信息的类型描述
                field_type = {"union": union_info["fields"]}
                if child_name.startswith("union (anonymous"):
                    # 未命名字段，直接添加
                    fields.append({
                        "name":"",
                        "type": field_type
                    })
                else:
                    # 可能是命名字段等待后续的FIELD_DECL节点得到名字
                    if embedded_union_name in embedded_childrens:
                        # 没有被FIELD_DECL命中，但新的usr又相同，说明是匿名字段
                        old_field_type = embedded_childrens[embedded_union_name]
                        fields.append({
                            "name":"",
                            "type": old_field_type
                        })
                    embedded_childrens[embedded_union_name] = field_type
        elif (child.kind == clang.cindex.CursorKind.STRUCT_DECL) and child.is_definition():
            embedded_struct_name = child.get_usr()
            child_name = child.spelling
            struct_info = process_struct(child, project_root)
            if struct_info:
                field_type = {"struct": struct_info["fields"]}
                if child_name.startswith("struct (anonymous"):
                    # 未命名字段，直接添加
                    fields.append({
                        "name":"",
                        "type": field_type
                    })
                else:
                    # 可能是命名字段等待后续的FIELD_DECL节点得到名字
                    if embedded_struct_name in embedded_childrens:
                        # 没有被FIELD_DECL命中，但新的usr又相同，说明是匿名字段
                        old_field_type = embedded_childrens[embedded_struct_name]
                        fields.append({
                            "name":"",
                            "type": old_field_type
                        })
                    embedded_childrens[embedded_struct_name] = field_type
        elif (child.kind == clang.cindex.CursorKind.ENUM_DECL) and child.is_definition():
            embedded_enum_name = child.get_usr()
            enum_info = process_enum(child, project_root)
            if enum_info:
                field_type = {"enum": enum_info["values"]}
                embedded_childrens[embedded_enum_name] = field_type
        elif (child.kind == clang.cindex.CursorKind.FIELD_DECL):
            field_name = child.spelling
            field_type = child.type.spelling
            type_usr = child.type.get_canonical().get_declaration().get_usr()
            if (type_usr in embedded_childrens):
                field_type = embedded_childrens[type_usr]
                del embedded_childrens[type_usr]

            if field_name and field_type:
                fields.append({"name": field_name, "type": field_type})

    if embedded_childrens:
        for child in embedded_childrens:
            fields.append({"name": "", "fields": embedded_childrens[child]})

    if struct_name and fields:
        # 获取结构体定义的实际位置
        if node.location.file:
            node_file_path = os.path.abspath(node.location.file.name)
            try:
                definition_location = os.path.relpath(node_file_path, project_root)
            except ValueError:
                definition_location = node_file_path
                
        # 获取结构体定义的起止行号
        start_line = node.extent.start.line
        end_line = node.extent.end.line
                
        return {
            "struct": struct_name,
            "fields": fields,
            "defined_in": definition_location,
            "start_line": start_line,
            "end_line": end_line
        }
    else:
        logger.warning(f"Warning: Skipping non-struct node: {node.spelling}")

    return None

def process_enum(node, project_root):
    enum_name = node.spelling

    # 收集枚举值信息
    enum_values = []
    for child in node.get_children():
        if child.kind == clang.cindex.CursorKind.ENUM_CONSTANT_DECL:
            constant_name = child.spelling
            # 获取常量值（如果可获得）
            constant_value = None
            try:
                # 尝试获取枚举常量的值
                constant_value = child.enum_value
            except:
                pass
            
            if constant_name:
                if constant_value is not None:
                    enum_values.append({"name": constant_name, "value": constant_value})
                else:
                    enum_values.append({"name": constant_name})

    if enum_name and enum_values:
        # 获取枚举定义的实际位置
        if node.location.file:
            node_file_path = os.path.abspath(node.location.file.name)
            try:
                definition_location = os.path.relpath(node_file_path, project_root)
            except ValueError:
                definition_location = node_file_path

        # 获取枚举定义的起止行号
        start_line = node.extent.start.line
        end_line = node.extent.end.line

        # 为枚举创建一个特殊的条目
        return {
            "enum": enum_name,
            "values": enum_values,
            "defined_in": definition_location,
            "start_line": start_line,
            "end_line": end_line
        }
    
    return None

def print_ast(node, indent=0):
    prefix = "  " * indent
    print(f"{prefix}{node.kind} {node.spelling} [{node.type.spelling}]")
    for child in node.get_children():
        print_ast(child, indent + 1)


def strip_ptr_ref_const(type_str: str) -> str:
    """
    剥离 C/C++ 类型字符串中的：
    - 指针 *
    - 引用 & / &&
    - const 修饰符（任意位置）
    只保留最底层类型名
    """
    if not type_str:
        return type_str

    s = type_str.strip()

    # 1. 去掉所有 const（作为独立关键字）
    s = re.sub(r'\bconst\b', '', s)

    # 2. 反复去掉末尾的 * & &&
    while True:
        new = re.sub(r'\s*(\*|\&{1,2})\s*$', '', s)
        if new == s:
            break
        s = new

    # 3. 清理多余空格
    s = re.sub(r'\s+', ' ', s)

    return s.strip()

def parse_file(file_path, struct_union_maps, args=None):
    index = clang.cindex.Index.create()
    if args is None:
        args = []
    # 使用更全面的解析选项以确保能正确识别所有结构体定义，包括在头文件中定义的结构体
    # 移除PARSE_SKIP_FUNCTION_BODIES标志以确保解析函数体内的调用
    tu = index.parse(
        file_path, 
        args=args,
        options= clang.cindex.TranslationUnit.PARSE_INCOMPLETE |
                clang.cindex.TranslationUnit.PARSE_PRECOMPILED_PREAMBLE |
                clang.cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
    )

    call_graph = {}
    
    # 存储文件的信息
    file_info = {
        "file": os.path.basename(file_path),
        "functions": [],
        "structs": [],
        "macros": [],
        "includes": []
    }

    # 保存include信息，某个文件包含了哪些头文件
    includes = defaultdict(set)

    # 标准化文件路径，移除工作目录前缀（如果存在）
    normalized_path = os.path.abspath(file_path)
    # 从命令行参数中获取项目根目录
    project_root = os.path.abspath(args[0]) if args and len(args) > 0 and not args[0].startswith('-') else os.getcwd()
    try:
        # 计算文件相对于项目根目录的路径
        relative_path = os.path.relpath(normalized_path, project_root)
    except ValueError:
        # 处理跨驱动器的情况（Windows）
        relative_path = normalized_path
        
    # 更新file_info中的文件路径为相对于项目根目录的路径
    file_info["file"] = relative_path

    # 存储结构体字段信息
    struct_fields = {}
    
    # 存储结构体使用信息
    struct_uses = defaultdict(list)  # 结构体名 -> [(文件路径:函数名), ...]

    typedefs = {}
    
    # 存储全局变量定义和使用信息
    global_var_defs: dict[str, GlobalVarInfo] = {}  # 变量名 -> GlobalVarInfo
    global_var_uses = defaultdict(list)  # 变量名 -> [(文件路径:函数名), ...]
    
    # 存储宏定义和使用信息
    macro_defs = {}  # 宏名 -> (内容, 文件路径)
    macro_uses = defaultdict(list)  # 宏名 -> [(文件路径:函数名/上下文), ...]
    
    # 在visit_node函数外部定义一个变量来存储上次输出的时间
    last_print_time = [0.0]

    def is_struct(name):
        name = strip_ptr_ref_const(name)

        if name in struct_fields:
            return True
        
        if name in typedefs:
            return typedefs[name] in struct_fields
        
        return False
    
    def visit_node(node, current_func=None, parent_node=None):
        # 控制输出频率，只有在时间超过1秒时才输出
        current_time = time.time()
        if current_time - last_print_time[0] > 1.0:
            print(f"Visiting node: {node.kind}, {node.spelling if node.spelling else 'Unnamed'}")
            last_print_time[0] = current_time
            
        # 处理所有节点，包括来自头文件的节点
        # 但要避免无限递归，只处理项目内的文件
        if node.location.file:
            node_file_path = os.path.abspath(node.location.file.name)
            # 检查是否在项目目录内
            if not node_file_path.startswith(os.path.abspath(project_root)):
                # 不在项目目录内的文件（如系统头文件）不需要处理
                return

        # 如果节点不属于任何文件（如根节点），也进行处理
            
        # 函数定义
        if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
            func_name = node.spelling
            # 检查是否是函数定义（有函数体）而不仅仅是声明
            is_definition = False
            for child in node.get_children():
                # 如果函数有复合语句子节点，则说明是定义而非声明
                if child.kind == clang.cindex.CursorKind.COMPOUND_STMT:
                    is_definition = True
                    break
            
            # 只有函数定义才添加到函数列表和调用图中
            if is_definition:
                # 计算函数的起始行号和结束行号
                start_line = node.extent.start.line
                end_line = node.extent.end.line
                func_file = os.path.abspath(node.location.file.name)
                definded_in = os.path.relpath(func_file, project_root)

                with open(func_file, 'r', encoding='utf-8', errors='ignore') as f:
                    func_content = f.readlines()
                    comment_start = find_doc_comment_start(func_content, start_line)
                    if comment_start is not None:
                        start_line = comment_start
                
                # 添加到函数列表
                if func_name and func_name not in file_info["functions"]:
                    file_info["functions"].append({
                        "name": func_name,
                        "definded_in": definded_in,
                        "start_line": start_line,
                        "end_line": end_line
                    })
                # 使用文件路径作为前缀来区分同名函数
                if func_name:
                    unique_func_name = f"{definded_in}:{func_name}"
                    call_graph.setdefault(unique_func_name, [])
                    current_func = unique_func_name
                    
                    # 检查函数参数中的结构体类型
                    for child in node.get_children():
                        if child.kind == clang.cindex.CursorKind.PARM_DECL:
                            param_type = child.type.spelling
                            # 检查是否是结构体类型
                            if param_type.startswith("struct "):
                                struct_name = strip_ptr_ref_const(param_type[7:])  # 去掉"struct "前缀
                                if struct_name:
                                    use_location = current_func if current_func else f"{relative_path}:global"
                                    if use_location not in struct_uses[struct_name]:
                                        struct_uses[struct_name].append(use_location)
                            # 也检查不带"struct "前缀的情况
                            else:
                                # 检查是否与已知结构体匹配
                                if is_struct(param_type):
                                    struct_name = strip_ptr_ref_const(param_type)
                                    use_location = current_func if current_func else f"{relative_path}:global"
                                    if use_location not in struct_uses[struct_name]:
                                        struct_uses[struct_name].append(use_location)
                                        
                # 继续遍历子节点以处理函数体内的调用
                for c in node.get_children():
                    visit_node(c, current_func, node)
            else:
                # 这是函数声明，不是定义，我们不处理它
                pass
        # 函数调用
        elif node.kind == clang.cindex.CursorKind.CALL_EXPR and current_func:
            # 获取被调用函数的名称
            called_func_cursor = node.referenced
            if called_func_cursor and called_func_cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                called_func_name = called_func_cursor.spelling
                # 记录调用关系，避免重复记录
                if called_func_name and called_func_name not in call_graph[current_func]:
                    call_graph[current_func].append(called_func_name)
            else:
                # 如果无法通过referenced获取，尝试使用node.spelling
                called_func_name = node.spelling
                # 记录调用关系，避免重复记录
                if called_func_name and called_func_name not in call_graph[current_func]:
                    call_graph[current_func].append(called_func_name)
        elif node.kind == clang.cindex.CursorKind.TYPEDEF_DECL:
            typedefs[
                strip_ptr_ref_const(node.spelling)
            ] = strip_ptr_ref_const(
                node.underlying_typedef_type.spelling
            )
        # 结构体定义
        elif node.kind == clang.cindex.CursorKind.STRUCT_DECL and node.is_definition():
            struct_info = None
            struct_usr = node.get_usr()
            if (struct_usr in struct_union_maps):
                struct_info = struct_union_maps[struct_usr]
                struct_name = struct_info["struct"]
            else:
                struct_info = process_struct(node, project_root)
                if struct_info:
                    struct_union_maps[struct_usr] = struct_info
                    struct_name = node.spelling
            if not struct_info:
                return
            
            # 对于匿名结构体或Clang无法正确识别名称的结构体，尝试多种方法获取正确名称
            if not struct_name or struct_name.startswith("struct (unnamed at"):
                # 方法1: 使用parent_node的spelling
                if (parent_node and parent_node.kind == clang.cindex.CursorKind.TYPEDEF_DECL):
                    struct_name =  parent_node.spelling
                else:
                    return
            
            if struct_name and struct_name not in file_info["structs"]:
                file_info["structs"].append(struct_name)
            
            struct_info["struct"] = struct_name
            if struct_name and struct_info:
                # 获取结构体定义的实际位置
                definition_location = struct_info["defined_in"]
                if not definition_location:
                    definition_location = relative_path
                    struct_info["defined_in"] = definition_location
                        
                struct_fields[struct_name] = struct_info

            # struct 定义子节点已经全部处理完毕，返回
            return
                
        # 联合体定义
        elif node.kind == clang.cindex.CursorKind.UNION_DECL and node.is_definition():
            union_info = None
            union_usr = node.get_usr()
            if (union_usr in struct_union_maps):
                union_info = struct_union_maps[union_usr]
                union_name = union_info["union"]
            else:
                union_info = process_union(node, project_root)
                if union_info:
                    struct_union_maps[union_usr] = union_info
                    union_name = union_info["union"]
            if not union_info:
                return

            # 对于匿名联合体或Clang无法正确识别名称的联合体，尝试多种方法获取正确名称
            if not union_name or union_name.startswith("union (unnamed at"):
                # 方法1: 使用parent_node的spelling
                if (parent_node and parent_node.kind == clang.cindex.CursorKind.TYPEDEF_DECL):
                    union_name =  parent_node.spelling
                else:
                    return

            union_info["union"] = union_name
            if union_name and union_info:
                # 获取联合体定义的实际位置
                if not union_info["defined_in"]:
                    union_info["defined_in"] = relative_path
                        
                # 为联合体创建一个特殊的条目，与结构体分开
                struct_fields[union_name] = union_info

            # union 字节点已处理完毕，返回
            return
        # 枚举定义
        elif node.kind == clang.cindex.CursorKind.ENUM_DECL and node.is_definition():
            enum_info = None
            enum_usr = node.get_usr()
            if (enum_usr in struct_union_maps):
                enum_info = struct_union_maps[enum_usr]
                enum_name = enum_info["enum"]
            else:
                enum_info = process_enum(node, project_root)
                if enum_info:
                    struct_union_maps[enum_usr] = enum_info
                    enum_name = enum_info["enum"]
            if not enum_info:
                return

            # 对于匿名枚举或Clang无法正确识别名称的枚举，尝试多种方法获取正确名称
            if not enum_name or enum_name.startswith("enum (unnamed at"):
                # 方法1: 使用parent_node的spelling
                if (parent_node and parent_node.kind == clang.cindex.CursorKind.TYPEDEF_DECL):
                    enum_name =  parent_node.spelling
                else:
                    return

            enum_info["enum"] = enum_name
            if enum_name and enum_info:
                # 获取枚举定义的实际位置
                if not enum_info["defined_in"]:
                    enum_info["defined_in"] = relative_path
                        
                # 为枚举创建一个特殊的条目，与结构体和联合体分开
                struct_fields[enum_name] = enum_info

            # enum 字节点已处理完毕，返回
            return
        # 宏定义
        elif node.kind == clang.cindex.CursorKind.MACRO_DEFINITION:
            macro_name = node.spelling
            # 获取宏定义的内容
            macro_content = ""
            macro_definition_path = relative_path  # 默认使用当前文件路径
            
            try:
                # 尝试获取宏定义的原始文本
                if node.location.file:
                    macro_file_path = os.path.abspath(node.location.file.name)
                    try:
                        macro_relative_path = os.path.relpath(macro_file_path, project_root)
                    except ValueError:
                        macro_relative_path = macro_file_path
                    
                    # 只有当文件在项目目录内时才读取内容
                    if macro_file_path.startswith(os.path.abspath(project_root)):
                        with open(macro_file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            # 获取宏定义所在的行
                            line_num = node.location.line - 1  # 行号从1开始，索引从0开始
                            if line_num < len(lines):
                                # 处理多行宏定义
                                line = lines[line_num].rstrip().rstrip('\\').rstrip()
                                macro_lines = [line]
                                # 检查是否是多行宏定义（以\结尾）
                                j = line_num
                                while j < len(lines) and lines[j].rstrip().endswith('\\'):
                                    if j + 1 < len(lines):
                                        line = lines[j + 1].rstrip()
                                        line = line.rstrip('\\').rstrip()
                                        macro_lines.append(line)
                                        j += 1
                                
                                # 重新构造宏定义内容
                                macro_content = '\n'.join(macro_lines)
                            
                            # 向前推第一行有效代码是否是#ifndef macro_name，如果是的话说明是一个保护宏不输出它
                            macro_value = macro_content.replace("#define", "").strip()
                            macro_value = macro_value.replace(macro_name, "").strip()

                            if not macro_value: # 如果宏定义内容为空才去做检查
                                line_num = node.location.line - 1  # 行号从1开始，索引从0开始
                                _, line = find_prev_effective_line(lines, line_num)

                                if line and line.startswith("#ifndef "):
                                    find_macro_name = line[len("#ifndef "):].strip()
                                    if macro_name in find_macro_name:
                                        return

                        # 更新宏定义的位置信息
                        macro_definition_path = macro_relative_path
                    else:
                        # 如果文件不在项目目录内，使用当前文件路径
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            # 获取宏定义所在的行
                            line_num = node.location.line - 1  # 行号从1开始，索引从0开始
                            if line_num < len(lines):
                                # 处理多行宏定义
                                macro_lines = [lines[line_num].rstrip()]
                                # 检查是否是多行宏定义（以\结尾）
                                j = line_num + 1
                                while j < len(lines) and lines[j].rstrip().endswith('\\'):
                                    macro_lines.append(lines[j].rstrip())
                                    j += 1
                                # 添加最后一行（不以\结尾的行）
                                if j < len(lines) and lines[j].strip():
                                    macro_lines.append(lines[j].rstrip())
                                
                                # 重新构造宏定义内容
                                macro_content = '\n'.join(macro_lines)
                        macro_definition_path = relative_path
                else:
                    # 如果没有文件信息，使用当前文件路径
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # 获取宏定义所在的行
                        line_num = node.location.line - 1  # 行号从1开始，索引从0开始
                        if line_num < len(lines):
                            # 处理多行宏定义
                            macro_lines = [lines[line_num].rstrip()]
                            # 检查是否是多行宏定义（以\结尾）
                            j = line_num + 1
                            while j < len(lines) and lines[j].rstrip().endswith('\\'):
                                macro_lines.append(lines[j].rstrip())
                                j += 1
                            # 添加最后一行（不以\结尾的行）
                            if j < len(lines) and lines[j].strip():
                                macro_lines.append(lines[j].rstrip())
                            
                            # 重新构造宏定义内容
                            macro_content = '\n'.join(macro_lines)
                    macro_definition_path = relative_path
            except:
                # 如果出现异常，使用当前文件路径
                macro_definition_path = relative_path
                pass
            
            # 对于已经存在的宏定义，优先保留头文件中的定义
            if macro_name in macro_defs:
                # 如果当前宏定义在头文件中，优先使用
                existing_path = macro_defs[macro_name][1]
                # 如果当前路径是头文件，或者现有路径不是头文件，则更新
                if macro_definition_path.startswith("include/") or not existing_path.startswith("include/"):
                    macro_defs[macro_name] = (macro_content, macro_definition_path)
            else:
                if macro_name and macro_name not in file_info["macros"]:
                    file_info["macros"].append(macro_name)
                
                # 记录宏定义信息
                macro_defs[macro_name] = (macro_content, macro_definition_path)
        # 包含文件
        elif node.kind == clang.cindex.CursorKind.INCLUSION_DIRECTIVE:
            include_name = node.spelling

            location_file = node.location.file.name
            if location_file:
                include_file_path = os.path.abspath(location_file)
                include_dir = os.path.dirname(include_file_path)
                relative_location_file = os.path.relpath(include_file_path, project_root)

                # 对于相对路径包含（""）尝试解析实际路径
                if not include_name.startswith('<') and not include_name.endswith('>'):
                    # 根据当前文件的相对路径、include path逐个去匹配
                    # 首先尝试在当前文件所在目录查找
                    potential_path = os.path.join(include_dir, include_name)
                    if os.path.exists(potential_path):
                        try:
                            relative_include_path = os.path.relpath(potential_path, project_root)
                            includes[relative_location_file].add(relative_include_path)
                        except ValueError:
                            # 处理跨驱动器的情况（Windows）
                            includes[relative_location_file].add(include_name)
                    else:
                        # 如果在当前文件目录找不到，尝试在项目包含路径中查找
                        found = False
                        # 遍历所有包含路径
                        for include_path in args[1:]:  # 使用args中的包含路径
                            if include_path.startswith("-I"):
                                include_path = include_path[2:]
                            include_path = os.path.abspath(include_path)
                            potential_path = os.path.join(include_path, include_name)
                            if os.path.exists(potential_path):
                                try:
                                    relative_include_path = os.path.relpath(potential_path, project_root)
                                    includes[relative_location_file].add(relative_include_path)
                                    found = True
                                    break
                                except ValueError:
                                    # 处理跨驱动器的情况（Windows）
                                    includes[relative_location_file].add(include_name)
                                    found = True
                                    break
                        
                        # 如果在所有包含路径中都找不到，仍然使用原始名称
                        if not found:
                            includes[relative_location_file].add(include_name)
                else:
                    # 对于系统包含（<>）直接添加
                    includes[relative_location_file].add(include_name)

        # 全局变量声明/定义
        elif node.kind == clang.cindex.CursorKind.VAR_DECL and not current_func:
            var_name = node.spelling
            var_type = node.type.spelling

            def is_var_definition(node):
                # extern 修饰的一定不是定义（除非你要处理 extern + initializer 的极端情况）
                if node.storage_class == clang.cindex.StorageClass.EXTERN:
                    return False

                # 其余情况全部是定义（包括 int g; 这种）
                return True

            if var_name:
                # 检查这是否是一个定义而不仅仅是一个声明
                is_definition = is_var_definition(node)
                
                # 获取变量定义/声明的实际位置
                definition_location = relative_path
                if not is_definition and node.location.file:
                    node_file_path = os.path.abspath(node.location.file.name)
                    try:
                        definition_location = os.path.relpath(node_file_path, project_root)
                    except ValueError:
                        definition_location = node_file_path
                
                # 对于已经存在的全局变量，优先保留定义而非声明
                if var_name in global_var_defs:
                    # 如果当前节点是定义（无论现有记录是什么），都应该更新为当前位置
                    # 因为我们现在遇到了实际的定义
                    if is_definition:
                        global_var_defs[var_name] = GlobalVarInfo(
                                name = var_name,
                                type = var_type,
                                file = definition_location,
                                is_definition = is_definition,
                            )
                else:
                    # 新的全局变量
                    global_var_defs[var_name] = GlobalVarInfo(
                            name = var_name,
                            type = var_type,
                            file = definition_location,
                            is_definition = is_definition,
                        )
        # 变量引用（在函数内部）
        elif node.kind == clang.cindex.CursorKind.DECL_REF_EXPR and current_func:
            # 检查是否引用了全局变量或结构体
            try:
                referenced_decl = node.referenced
                if referenced_decl:
                    # 检查是否引用了全局变量
                    if referenced_decl.kind == clang.cindex.CursorKind.VAR_DECL:
                        var_name = referenced_decl.spelling
                        if var_name in global_var_defs:
                            # 记录全局变量的使用
                            use_location = current_func
                            if use_location not in global_var_uses[var_name]:
                                global_var_uses[var_name].append(use_location)
                    # 检查是否引用了结构体
                    elif referenced_decl.kind == clang.cindex.CursorKind.STRUCT_DECL:
                        struct_name = referenced_decl.spelling
                        if struct_name:
                            # 记录结构体的使用
                            use_location = current_func
                            if use_location not in struct_uses[struct_name]:
                                struct_uses[struct_name].append(use_location)
            except AttributeError:
                # 如果无法获取引用信息，则跳过
                pass
        
        # 检查变量声明中的结构体类型使用
        elif node.kind == clang.cindex.CursorKind.VAR_DECL:
            # 检查变量声明中的类型
            var_type = node.type.spelling
            # 检查是否是结构体类型
            if var_type.startswith("struct "):
                struct_name = strip_ptr_ref_const(var_type[7:])  # 去掉"struct "前缀
                if struct_name:
                    use_location = current_func if current_func else f"{relative_path}:global"
                    if use_location not in struct_uses[struct_name]:
                        struct_uses[struct_name].append(use_location)
            # 也检查不带"struct "前缀的情况
            else:
                # 检查是否与已知结构体匹配
                if is_struct(var_type):
                    struct_name = strip_ptr_ref_const(var_type)
                    use_location = current_func if current_func else f"{relative_path}:global"
                    if use_location not in struct_uses[struct_name]:
                        struct_uses[struct_name].append(use_location)
                            
            # 检查返回类型是否是结构体
            result_type = node.result_type.spelling
            if result_type.startswith("struct "):
                struct_name = strip_ptr_ref_const(result_type[7:])  # 去掉"struct "前缀
                if struct_name:
                    use_location = current_func if current_func else f"{relative_path}:global"
                    if use_location not in struct_uses[struct_name]:
                        struct_uses[struct_name].append(use_location)
            else:
                # 检查返回类型是否与已知结构体匹配
                if is_struct(result_type):
                    struct_name = strip_ptr_ref_const(result_type)
                    use_location = current_func if current_func else f"{relative_path}:global"
                    if use_location not in struct_uses[struct_name]:
                        struct_uses[struct_name].append(use_location)
                            
        # 检查函数参数中的结构体类型使用
        elif node.kind == clang.cindex.CursorKind.PARM_DECL:
            param_type = node.type.spelling
            # 检查是否是结构体类型
            if param_type.startswith("struct "):
                struct_name = strip_ptr_ref_const(param_type[7:])  # 去掉"struct "前缀
                if struct_name:
                    # 获取参数所属的函数
                    parent = node.semantic_parent
                    if parent and parent.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                        use_location = current_func if current_func else f"{relative_path}:global"
                        if use_location not in struct_uses[struct_name]:
                            struct_uses[struct_name].append(use_location)
            # 也检查不带"struct "前缀的情况
            else:
                # 检查是否与已知结构体匹配
                if is_struct(param_type):
                    struct_name = strip_ptr_ref_const(param_type)
                    use_location = current_func if current_func else f"{relative_path}:global"
                    if use_location not in struct_uses[struct_name]:
                        struct_uses[struct_name].append(use_location)
                            
        # 检查函数返回类型中的结构体类型使用
        elif node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
            return_type = node.result_type.spelling
            # 检查返回类型是否是结构体类型
            if return_type.startswith("struct "):
                struct_name = strip_ptr_ref_const(return_type[7:])  # 去掉"struct "前缀
                if struct_name:
                    use_location = current_func if current_func else f"{relative_path}:global"
                    if use_location not in struct_uses[struct_name]:
                        struct_uses[struct_name].append(use_location)
            # 也检查不带"struct "前缀的情况
            else:
                # 检查返回类型是否与已知结构体匹配
                if is_struct(return_type):
                    struct_name = strip_ptr_ref_const(return_type)
                    use_location = current_func if current_func else f"{relative_path}:global"
                    if use_location not in struct_uses[struct_name]:
                            struct_uses[struct_name].append(use_location)
                            
            # 继续遍历子节点以处理函数内部的使用情况
            for c in node.get_children():
                visit_node(c, node.spelling, node)
        # 检查是否是宏使用（通过标识符引用）
        elif node.kind == clang.cindex.CursorKind.MACRO_INSTANTIATION:
            macro_name = node.spelling
            # 记录宏的使用位置
            context = current_func.split(':')[-1] if current_func else "global"
            use_location = f"{relative_path}:{context}"
            if use_location not in macro_uses[macro_name]:
                macro_uses[macro_name].append(use_location)
        
        # 遍历子节点
        for c in node.get_children():
            visit_node(c, current_func, node)

    visit_node(tu.cursor)

    # 整理struct_uses，有的是针对typedef的引用，指向正确的struct
    for type_name in typedefs.keys():
        alias_of = typedefs[type_name]

        if type_name in struct_uses and alias_of in struct_fields:
            use_locations = set()
            locations = struct_uses[type_name]
            del struct_uses[type_name]
            if locations:
                use_locations.update(locations)

            # 原名的也要取出来合并
            if alias_of in struct_uses:
                locations = struct_uses[alias_of]
                if locations:
                    use_locations.update(locations)

            struct_uses[alias_of] = list(use_locations)
            
    return ParseFileResult(graph=call_graph,
            rel_path=relative_path,
            file_info=file_info,
            struct_fields=struct_fields,
            struct_uses=struct_uses,
            global_var_defs=global_var_defs,
            global_var_uses=global_var_uses,
            macro_defs=macro_defs,
            macro_uses=macro_uses,
            includes=includes
        )

def extract_macros_from_source(file_path, file_info):
    """通过正则表达式从源代码中提取宏定义"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        import re
        # 匹配#define宏定义
        macro_pattern = r'^\s*#\s*define\s+(\w+)'
        for match in re.finditer(macro_pattern, content, re.MULTILINE):
            macro_name = match.group(1)
            if macro_name and macro_name not in file_info["macros"]:
                file_info["macros"].append(macro_name)
    except Exception as e:
        pass  # 忽略文件读取错误

def extract_macro_uses_from_source(file_path, macro_uses, relative_path):
    """通过正则表达式从源代码中提取宏使用情况"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        import re
        # 匹配标识符（可能是宏）
        identifier_pattern = r'\b([A-Z_][A-Z0-9_]*)\b'
        for match in re.finditer(identifier_pattern, content):
            macro_name = match.group(1)
            # 简单地将文件路径作为使用位置记录
            use_location = f"{relative_path}:global"
            if use_location not in macro_uses[macro_name]:
                macro_uses[macro_name].append(use_location)
    except Exception as e:
        pass  # 忽略文件读取错误

def extract_includes_from_source(file_path, file_info, include_dirs=[]):
    """通过正则表达式从源代码中提取包含文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        import re
        # 匹配#include指令，捕获整个指令行以区分<>和""
        include_pattern = r'^\s*#\s*include\s+([<"])([^>"]+)([>"])'
        for match in re.finditer(include_pattern, content, re.MULTILINE):
            quote_start = match.group(1)
            include_name = match.group(2)
            quote_end = match.group(3)
            
            if include_name and include_name not in file_info["includes"]:
                file_info["includes"].append(include_name)
                
                # 检查头文件是否存在
                found = False
                
                # 对于双引号包围的头文件，先检查相对路径
                if quote_start == '"' and quote_end == '"':
                    include_file = os.path.join(os.path.dirname(file_path), include_name)
                    if os.path.exists(include_file):
                        found = True
                    
                    # 如果没找到，检查包含目录
                    if not found:
                        for include_dir in include_dirs:
                            include_file = os.path.join(include_dir, include_name)
                            if os.path.exists(include_file):
                                found = True
                                break
                
                # 对于尖括号包围的系统头文件，只在系统目录和指定包含目录中查找
                elif quote_start == '<' and quote_end == '>':
                    # 系统包含目录
                    system_include_dirs = [
                        "/usr/include",
                        "/usr/local/include"
                    ]
                    
                    # 检查系统目录和指定包含目录
                    for include_dir in system_include_dirs + include_dirs:
                        include_file = os.path.join(include_dir, include_name)
                        if os.path.exists(include_file):
                            found = True
                            break
                
                # 如果仍然没找到，输出警告日志
                # 但对于某些常见的系统头文件，我们不输出警告
                common_system_headers = [
                    "stdio.h", "stdlib.h", "string.h", "stdint.h", "stdbool.h",
                    "stddef.h", "limits.h", "math.h", "time.h", "unistd.h",
                    "assert.h", "stdarg.h", "ctype.h", "errno.h", "float.h",
                    "locale.h", "setjmp.h", "signal.h", "tgmath.h"
                ]
                
                if not found and include_name not in common_system_headers:
                    logger.warning(f"Warning: Header file '{include_name}' not found (included in '{file_path}')")
    except Exception as e:
        pass  # 忽略文件读取错误

def extract_typedef_name_from_source(file_path, line_number):
    """从源代码中提取typedef名称"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 从指定行向上搜索typedef关键字
        for i in range(line_number - 1, -1, -1):
            line = lines[i].strip()
            # 匹配typedef struct {...} name; 或 typedef struct name {...} name;
            # 改进的正则表达式，能够处理预处理指令
            typedef_match = re.search(r'typedef\s+struct(?:\s+\w+)?\s*\{[^}]*\}\s*(\w+)(?:\s*,\s*\*\w+)?\s*;', line, re.DOTALL)
            if typedef_match:
                return typedef_match.group(1)
            
            # 匹配多行的typedef struct
            if 'typedef' in line and 'struct' in line:
                # 向下搜索直到找到分号
                typedef_lines = [line]
                brace_count = line.count('{') - line.count('}')
                for j in range(i + 1, len(lines)):
                    current_line = lines[j].strip()
                    # 跳过预处理指令行
                    if not current_line.startswith('#'):
                        typedef_lines.append(current_line)
                        brace_count += current_line.count('{') - current_line.count('}')
                        if brace_count == 0 and ';' in current_line:
                            typedef_text = ' '.join(typedef_lines)
                            # 更宽松的正则表达式匹配，支持逗号分隔的多个标识符
                            typedef_match = re.search(r'typedef\s+struct(?:\s+\w+)?\s*\{[^}]*\}\s*(\w+)(?:\s*,\s*\*\w+)?\s*;', typedef_text, re.DOTALL)
                            if typedef_match:
                                return typedef_match.group(1)
                            break
                        elif brace_count < 0:
                            # 括号不匹配，跳出循环
                            break
    except Exception as e:
        pass
    return None

def extract_include_paths_from_project(project_dir):
    """从项目文件中提取包含路径"""
    include_paths = []
    
    # 查找Keil项目文件
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith(('.uvproj', '.uvprojx')):
                project_file = os.path.join(root, file)
                print(f"Found project file: {project_file}")
                try:
                    # 解析XML文件
                    tree = ET.parse(project_file)
                    root_element = tree.getroot()
                    
                    # 查找包含路径
                    # 在Keil项目文件中，包含路径通常在以下位置：
                    # <Project><Targets><Target><TargetName><Toolset><Cads><IncludePath>
                    for include_path in root_element.iter('IncludePath'):
                        path_text = include_path.text
                        if path_text:
                            # 分割多个路径（通常用分号分隔）
                            paths = path_text.split(';')
                            for path in paths:
                                path = path.strip()
                                if path and path not in include_paths:
                                    path = path.replace("\\", "/")
                                    # 将相对路径转换为绝对路径
                                    if not os.path.isabs(path):
                                        path = os.path.join(os.path.dirname(project_file), path)
                                        path = os.path.normpath(path)
                                    include_paths.append(path)
                except Exception as e:
                    # 忽略解析错误
                    pass
    
    # 查找Eclipse CDT项目文件(.cproject)
    abs_project_dir = os.path.abspath(project_dir)
    for root, dirs, files in os.walk(abs_project_dir):
        for file in files:
            if file == '.cproject':
                project_file = os.path.join(root, file)
                try:
                    # 解析XML文件
                    tree = ET.parse(project_file)
                    root_element = tree.getroot()
                    
                    # 查找包含路径
                    # 在.cproject文件中，包含路径通常在以下位置：
                    # <storageModule><cconfiguration><storageModule configurationId="cdtBuildSystem"><configuration><folderInfo><toolChain><tool><option superClass="gnu.c.compiler.option.include.paths">
                    for option in root_element.iter('option'):
                        if option.get('superClass') == 'gnu.c.compiler.option.include.paths':
                            for listOptionValue in option.findall('listOptionValue'):
                                path_value = listOptionValue.get('value')

                                if path_value:
                                    # 移除引号
                                    path_value = path_value.strip('"')

                                    # 处理工作空间变量
                                    original_path_value = path_value
                                    if '${workspace_loc:' in path_value:
                                        # 替换工作空间变量
                                        workspace_loc = os.path.dirname(abs_project_dir)
                                        path_value = path_value.replace('${workspace_loc:', workspace_loc)
                                        path_value = path_value.rstrip('}')

                                        # 处理项目名称变量
                                        if '${ProjName}' in path_value:
                                            # 提取项目名称（从项目目录）
                                            project_name = os.path.basename(abs_project_dir)
                                            path_value = path_value.replace('${ProjName}', project_name)

                                    path_value = os.path.normpath(path_value)
                                    include_paths.append(path_value)

                except Exception as e:
                    # 忽略解析错误
                    pass
    
    return include_paths

def extract_preprocessor_macros_from_project(project_dir):
    """从项目文件中提取预处理宏定义"""
    macros = {}
    
    # 查找Keil项目文件
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith(('.uvproj', '.uvprojx')):
                project_file = os.path.join(root, file)
                print(f"Found project file: {project_file}")
                try:
                    # 解析XML文件
                    tree = ET.parse(project_file)
                    root_element = tree.getroot()
                    
                    # 查找预处理宏定义
                    # 在Keil项目文件中，宏定义通常在以下位置：
                    # <Project><Targets><Target><TargetName><Toolset><Cads><Define>
                    for define_element in root_element.iter('Define'):
                        define_text = define_element.text
                        if define_text:
                            # 分割多个宏定义（通常用分号分隔）
                            # Keil使用分号分隔宏定义
                            macro_definitions = define_text.split(';')
                            for macro_def in macro_definitions:
                                macro_def = macro_def.strip()
                                if macro_def:
                                    # 分离宏名和值（如果有的话）
                                    if '=' in macro_def:
                                        macro_name, macro_value = macro_def.split('=', 1)
                                        macros[macro_name.strip()] = macro_value.strip()
                                    else:
                                        # 没有指定值的宏定义，默认为1
                                        macros[macro_def] = "1"
                except Exception as e:
                    # 忽略解析错误
                    pass
    
    # 查找Eclipse CDT项目文件(.cproject)
    abs_project_dir = os.path.abspath(project_dir)
    for root, dirs, files in os.walk(abs_project_dir):
        for file in files:
            if file == '.cproject':
                project_file = os.path.join(root, file)
                try:
                    # 解析XML文件
                    tree = ET.parse(project_file)
                    root_element = tree.getroot()
                    
                    # 查找预处理宏定义
                    # 在.cproject文件中，宏定义通常在以下位置：
                    # <storageModule><cconfiguration><storageModule configurationId="cdtBuildSystem"><configuration><folderInfo><toolChain><tool><option superClass="gnu.c.compiler.option.preprocessor.def.symbols">
                    for option in root_element.iter('option'):
                        if option.get('superClass') == 'gnu.c.compiler.option.preprocessor.def.symbols':
                            for listOptionValue in option.findall('listOptionValue'):
                                macro_value = listOptionValue.get('value')
                                if macro_value:
                                    # 移除引号
                                    macro_value = macro_value.strip('"')
                                    
                                    # 分离宏名和值（如果有的话）
                                    if '=' in macro_value:
                                        macro_name, macro_val = macro_value.split('=', 1)
                                        macros[macro_name.strip()] = macro_val.strip()
                                    else:
                                        # 没有指定值的宏定义，默认为1
                                        macros[macro_value] = "1"

                except Exception as e:
                    # 忽略解析错误
                    pass
    
    return macros

def build_text_tree(call_graph, tree_name="Global"):
    """根据函数调用关系生成文本树"""
    # 创建所有节点
    nodes = {f: Node(f) for f in call_graph}
    
    # 处理调用关系
    for parent, children in call_graph.items():
        for child in children:
            if child in nodes:
                # 直接连接，因为child已经是完整的键
                nodes[child].parent = nodes[parent]
            else:
                # 如果child不在nodes中，可能是未定义的函数或格式问题
                # 检查是否是函数名（不包含路径）
                if ':' not in child:
                    # 尝试查找匹配的函数名
                    child_found = False
                    for node_key in nodes:
                        if ':' in node_key:
                            node_func_name = node_key.split(':', 1)[1]
                            if node_func_name == child:
                                nodes[node_key].parent = nodes[parent]
                                child_found = True
                                break
                    if not child_found:
                        new_child_key = f"unknown:{child}"
                        if new_child_key not in nodes:
                            nodes[new_child_key] = Node(new_child_key)
                        nodes[new_child_key].parent = nodes[parent]
                else:
                    # child包含路径但不在nodes中
                    new_child_key = child
                    if new_child_key not in nodes:
                        nodes[new_child_key] = Node(new_child_key)
                    nodes[new_child_key].parent = nodes[parent]
    
    # 找根节点：没有父节点的节点
    roots = [key for key, node in nodes.items() if node.parent is None]

    print(f"\nText Tree: {tree_name}")
    for root in roots:
        if root in nodes:
            for pre, _, node in RenderTree(nodes[root]):
                print(pre + node.name)

def resolve_call_graph(full_call_graph):
    """解析调用图，将函数调用映射到正确的文件路径"""
    # 创建函数名到完整路径的映射
    func_to_paths = {}
    for full_key in full_call_graph:
        if ':' in full_key:
            _, func_name = full_key.split(':', 1)
            if func_name not in func_to_paths:
                func_to_paths[func_name] = [full_key]
            else:
                func_to_paths[func_name].append(full_key)
    
    # 解析调用关系
    resolved_graph = {}
    for caller_key, callees in full_call_graph.items():
        resolved_graph[caller_key] = []
        caller_file = caller_key.split(':', 1)[0] if ':' in caller_key else ""
        
        for callee_name in callees:
            if callee_name in func_to_paths:
                # 优先选择同一个文件中的函数
                same_file_func = None
                other_funcs = []
                
                for func_path in func_to_paths[callee_name]:
                    func_file = func_path.split(':', 1)[0]
                    if func_file == caller_file:
                        same_file_func = func_path
                    else:
                        other_funcs.append(func_path)
                
                if same_file_func:
                    resolved_graph[caller_key].append(same_file_func)
                elif other_funcs:
                    # 如果同一个文件中没有，选择第一个其他文件中的函数
                    resolved_graph[caller_key].append(other_funcs[0])
            else:
                # 未知函数，保持原样
                resolved_graph[caller_key].append(f"unknown:{callee_name}")
    
    return resolved_graph

def save_json(call_graph, output_dir, project_name):
    """保存调用图为JSON"""
    
    project_output_dir = os.path.join(output_dir, project_name)
    os.makedirs(project_output_dir, exist_ok=True)
    file_name = os.path.join(project_output_dir, "call_graph.json")
    with open(file_name, "w") as f:
        json.dump(call_graph, f, indent=2)
    print(f"Global call graph saved to {file_name}")

def would_create_cycle(parent_node, child_node):
    """检查设置parent是否会导致循环引用"""
    # 如果父节点是子节点的后代，则会形成循环
    current = parent_node
    while current.parent is not None:
        if current.parent == child_node:
            return True
        current = current.parent
    return False

def save_text_tree(call_graph, output_dir, project_name):
    """根据函数调用关系生成全局文本树并保存到文件"""
    roots = set(call_graph)
    for _, children in call_graph.items():
        for child in children:
            roots.discard(child)

    root_nodes = []
    def procressFunction(fuction, parents = set()):
        node = None
        if fuction in parents:
            # 这是循环引用了
            return node

        if fuction in call_graph:
            node = Node(fuction)
            parents.add(fuction)
            children = call_graph[fuction]
            for child in children:
                child_node = procressFunction(child)
                if child_node:
                    child_node.parent = node
            parents.discard(fuction)

        return node

    for root in roots:
        node = procressFunction(root)
        if node:
            root_nodes.append(node)

    # 保存到文件
    text_tree_content = "Text Tree: Global Project\n"
    for root in root_nodes:
        for pre, _, node in RenderTree(root):
            text_tree_content += pre + node.name + "\n"

    project_output_dir = os.path.join(output_dir, project_name)
    os.makedirs(project_output_dir, exist_ok=True)
    file_name = os.path.join(project_output_dir, "call_text_tree.txt")
    with open(file_name, "w") as f:
        f.write(text_tree_content)
    logger.info(f"Text tree saved to {file_name}")

def save_file_info_json(file_infos, output_dir, project_name, project_dir):
    """保存文件信息为JSON"""
    # 简化文件信息，只保留functions和includes字段
    simplified_file_infos = []
    for file_path, file_info in file_infos.items():
        simplified_info = {
            "file": file_path,
            "functions": file_info["functions"],
            "includes": file_info["includes"]
        }
        simplified_file_infos.append(simplified_info)
    
    project_output_dir = os.path.join(output_dir, project_name)
    os.makedirs(project_output_dir, exist_ok=True)
    file_name = os.path.join(project_output_dir, "file_info.json")
    with open(file_name, "w") as f:
        json.dump(simplified_file_infos, f, indent=2)
    logger.info(f"File info saved to {file_name}")
    
    # 生成项目文件树
    generate_project_tree(project_dir, project_output_dir)

def generate_project_tree(project_dir, output_dir):
    """生成项目文件树"""
    # 生成文件树
    file_tree = generate_file_tree.generate_file_tree(project_dir)

    # 保存文件树到文本文件
    file_name = os.path.join(output_dir, "project_tree.txt")
    generate_file_tree.save_to_text(file_tree, file_name)

    logger.info(f"Project tree saved to {file_name}")

def save_struct_info_json(struct_fields, struct_uses, output_dir, project_name):
    """保存结构体信息为JSON"""
    project_output_dir = os.path.join(output_dir, project_name)
    os.makedirs(project_output_dir, exist_ok=True)
    file_name = os.path.join(project_output_dir, "struct_info.json")
    
    # 转换结构体信息格式
    struct_list = []
    for struct_name, info in struct_fields.items():
        # 检查是结构体、联合体还是枚举
        if "struct" in info:
            # 结构体
            struct_item = {
                "struct": info["struct"],
                "fields": info["fields"],
                "defined_in": info["defined_in"],
                "used_by": struct_uses.get(struct_name, [])
            }
            # 添加起止行号信息（如果存在）
            if "start_line" in info and "end_line" in info:
                struct_item["start_line"] = info["start_line"]
                struct_item["end_line"] = info["end_line"]
        elif "union" in info:
            # 联合体
            struct_item = {
                "union": info["union"],
                "fields": info["fields"],
                "defined_in": info["defined_in"],
                "used_by": struct_uses.get(struct_name, [])
            }
            # 添加起止行号信息（如果存在）
            if "start_line" in info and "end_line" in info:
                struct_item["start_line"] = info["start_line"]
                struct_item["end_line"] = info["end_line"]
        elif "enum" in info:
            # 枚举
            struct_item = {
                "enum": info["enum"],
                "values": info["values"],
                "defined_in": info["defined_in"],
                "used_by": struct_uses.get(struct_name, [])
            }
            # 添加起止行号信息（如果存在）
            if "start_line" in info and "end_line" in info:
                struct_item["start_line"] = info["start_line"]
                struct_item["end_line"] = info["end_line"]
        else:
            # 默认情况下，假设是结构体
            struct_item = {
                "struct": struct_name,
                "fields": info["fields"],
                "defined_in": info["defined_in"],
                "used_by": struct_uses.get(struct_name, [])
            }
            # 添加起止行号信息（如果存在）
            if "start_line" in info and "end_line" in info:
                struct_item["start_line"] = info["start_line"]
                struct_item["end_line"] = info["end_line"]
        struct_list.append(struct_item)
    
    with open(file_name, "w") as f:
        json.dump(struct_list, f, indent=2)
    print(f"Struct info saved to {file_name}")

def save_macro_info_json(macro_defs, macro_uses, output_dir, project_name):
    """保存宏信息为JSON"""
    project_output_dir = os.path.join(output_dir, project_name)
    os.makedirs(project_output_dir, exist_ok=True)
    file_name = os.path.join(project_output_dir, "macro_info.json")
    
    # 定义需要排除的 Clang 内置宏前缀和特定宏名
    clang_builtin_prefixes = [
        '__llvm__', '__clang__', '__clang_major__', '__clang_minor__', '__clang_patchlevel__', '__clang_version__',
        '__GNUC__', '__GNUC_MINOR__', '__GNUC_PATCHLEVEL__', '__GXX_ABI_VERSION', '__ATOMIC_', '__MEMORY_SCOPE_',
        '__OPENCL_MEMORY_SCOPE_', '__FPCLASS_', '__PRAGMA_REDEFINE_EXTNAME', '__VERSION__', '__OBJC_BOOL_IS_BOOL',
        '__CONSTANT_CFSTRINGS__', '__block', '__BLOCKS__', '__clang_literal_encoding__', '__clang_wide_literal_encoding__',
        '__ORDER_', '__BYTE_ORDER__', '__LITTLE_ENDIAN__', '_LP64', '__LP64__', '__CHAR_BIT__', '__BOOL_WIDTH__',
        '__SHRT_WIDTH__', '__INT_WIDTH__', '__LONG_WIDTH__', '__LLONG_WIDTH__', '__BITINT_MAXWIDTH__', '__SCHAR_MAX__',
        '__SHRT_MAX__', '__INT_MAX__', '__LONG_MAX__', '__LONG_LONG_MAX__', '__WCHAR_MAX__', '__WCHAR_WIDTH__',
        '__WINT_MAX__', '__WINT_WIDTH__', '__INTMAX_MAX__', '__INTMAX_WIDTH__', '__SIZE_MAX__', '__SIZE_WIDTH__',
        '__UINTMAX_MAX__', '__UINTMAX_WIDTH__', '__PTRDIFF_MAX__', '__PTRDIFF_WIDTH__', '__INTPTR_MAX__', '__INTPTR_WIDTH__',
        '__UINTPTR_MAX__', '__UINTPTR_WIDTH__', '__SIZEOF_', '__INTMAX_TYPE__', '__INTMAX_FMT', '__INTMAX_C',
        '__UINTMAX_TYPE__', '__UINTMAX_FMT', '__UINTMAX_C', '__PTRDIFF_TYPE__', '__PTRDIFF_FMT', '__INTPTR_TYPE__',
        '__INTPTR_FMT', '__SIZE_TYPE__', '__SIZE_FMT', '__WCHAR_TYPE__', '__WINT_TYPE__', '__SIG_ATOMIC_',
        '__CHAR16_TYPE__', '__CHAR32_TYPE__', '__UINTPTR_TYPE__', '__UINTPTR_FMT', '__FLT16_', '__FLT_',
        '__DBL_', '__LDBL_', '__POINTER_WIDTH__', '__BIGGEST_ALIGNMENT__', '__INT8_TYPE__', '__INT8_FMT',
        '__INT8_C', '__INT16_TYPE__', '__INT16_FMT', '__INT16_C', '__INT32_TYPE__', '__INT32_FMT',
        '__INT32_C', '__INT64_TYPE__', '__INT64_FMT', '__INT64_C', '__UINT8_TYPE__', '__UINT8_FMT',
        '__UINT8_C', '__UINT8_MAX__', '__INT8_MAX__', '__UINT16_TYPE__', '__UINT16_FMT', '__UINT16_C',
        '__UINT16_MAX__', '__INT16_MAX__', '__UINT32_TYPE__', '__UINT32_FMT', '__UINT32_C', '__UINT32_MAX__',
        '__INT32_MAX__', '__UINT64_TYPE__', '__UINT64_FMT', '__UINT64_C', '__UINT64_MAX__', '__INT64_MAX__',
        '__INT_LEAST', '__UINT_LEAST', '__INT_FAST', '__UINT_FAST', '__USER_LABEL_PREFIX__', '__NO_MATH_ERRNO__',
        '__FINITE_MATH_ONLY__', '__GNUC_STDC_INLINE__', '__GCC_ATOMIC_', '__CLANG_ATOMIC_', '__GCC_DESTRUCTIVE_SIZE',
        '__GCC_CONSTRUCTIVE_SIZE', '__NO_INLINE__', '__PIC__', '__pic__', '__FLT_RADIX__', '__DECIMAL_DIG__',
        '__SSP__', '__nonnull', '__null_unspecified', '__nullable', 'TARGET_OS_', '__GCC_ASM_FLAG_OUTPUTS__',
        '__code_model_small__', '__amd64', '__x86_64', '__SEG_', '__seg_', '__core2', '__tune_core2__',
        '__REGISTER_PREFIX__', '__NO_MATH_INLINES', '__LAHF_SAHF__', '__FXSR__', '__SSE4_1__', '__SSSE3__',
        '__SSE3__', '__SSE2__', '__SSE_MATH__', '__MMX__', '__GCC_HAVE_SYNC_COMPARE_AND_SWAP_', '__APPLE_',
        '__weak', '__strong', '__unsafe_unretained', '__DYNAMIC__', '__MACH__', '__STDC_NO_THREADS__',
        '__ENVIRONMENT_', '__STDC__', '__STDC_HOSTED__', '__STDC_VERSION__', '__STDC_UTF_', '__STDC_EMBED_',
        '__GCC_HAVE_DWARF2_CFI_ASM'
    ]
    
    # 特定需要排除的宏名
    clang_builtin_names = [
        'TARGET_IPHONE_SIMULATOR', '__SSE2_MATH__', '__SSE__'
    ]
    
    # 转换宏信息格式，并过滤掉 Clang 内置宏
    macro_list = []
    for macro_name, (content, defined_in) in macro_defs.items():
        # 检查是否是需要排除的 Clang 内置宏
        is_clang_builtin = False
        
        # 检查前缀匹配
        for prefix in clang_builtin_prefixes:
            if macro_name.startswith(prefix):
                is_clang_builtin = True
                break
        
        # 检查特定宏名匹配
        if not is_clang_builtin:
            for name in clang_builtin_names:
                if macro_name == name:
                    is_clang_builtin = True
                    break
        
        # 如果不是 Clang 内置宏，则添加到列表中
        params = ""
        macro_value = ""
        if not is_clang_builtin:
            # 提取宏定义的值，去除定义名字部分
            if content:
                # 使用正则表达式提取宏定义的值，去除定义名字部分
                # 匹配 #define MACRO_NAME VALUE 或 #define MACRO_NAME(VALUE) VALUE 这样的模式
                # 首先尝试匹配带参数的宏定义
                pattern = (
                    r'^\s*#\s*define\s+'
                    + re.escape(macro_name) +
                    r'(\([^)\n]*\))\s*(.*)$'
                )
                match = re.match(pattern, content, re.DOTALL)
                if match:
                    params = match.group(1).strip()
                    macro_value = match.group(2).strip()
                else:
                    # 然后尝试匹配不带参数的宏定义
                    match = re.match(r'^\s*#\s*define\s+' + re.escape(macro_name) + r'\s*(.*)$', content, re.DOTALL)
                    if match:
                        macro_value = match.group(1).strip()
                    else:
                        # 如果没有匹配到，可能是没有值的宏定义（如 #define MACRO_NAME）
                        # 或者是多行宏定义，这种情况下我们保留原始内容
                        macro_value = content
                
                # 对于多行宏定义，我们还需要进一步处理以去除定义名字部分
                # 如果宏值中还包含宏定义本身，我们需要去除它
                lines = macro_value.split('\n')
                cleaned_lines = []
                for line in lines:
                    # 检查每一行是否包含宏定义
                    if line.strip().startswith("#define "):
                        # 提取宏定义之后的内容
                        line_match = re.match(r'^#\s*define\s+\w+(?:\s*\([^)]*\))?\s*(.*)$', line)
                        if line_match:
                            cleaned_lines.append(line_match.group(1))
                        else:
                            # 如果没有匹配到，保留空字符串（对于没有值的宏定义）
                            cleaned_lines.append("")
                    else:
                        # 不是宏定义的行直接保留
                        cleaned_lines.append(line)
                macro_value = '\n'.join(cleaned_lines).strip()
                
                # 如果处理后的结果以宏名开头，再次处理
                if macro_value.startswith("#define " + macro_name):
                    lines = macro_value.split('\n')
                    # 去除第一行的宏定义部分
                    first_line_match = re.match(r'^#\s*define\s+' + re.escape(macro_name) + r'(?:\s*\([^)]*\))?\s*(.*)$', lines[0])
                    if first_line_match:
                        lines[0] = first_line_match.group(1)
                    macro_value = '\n'.join(lines).strip()
                
                # 特殊处理：如果宏值就是宏定义本身（没有值的宏），则设为空字符串
                if macro_value == "#define " + macro_name:
                    macro_value = ""
        
        
            macro_item = {
                "macro": macro_name + params,
                "content": macro_value,
                "defined_in": defined_in,
                "used_in": macro_uses.get(macro_name, [])
            }
            macro_list.append(macro_item)
    
    with open(file_name, "w") as f:
        json.dump(macro_list, f, indent=2)
    logger.info(f"Macro info saved to {file_name}")

def save_global_var_info_json(global_var_defs, global_var_uses, output_dir, project_name):
    project_output_dir = os.path.join(output_dir, project_name)
    os.makedirs(project_output_dir, exist_ok=True)
    file_name = os.path.join(project_output_dir, "global_var_info.json")
    
    # 转换全局变量信息格式
    global_var_list = []
    for var_name, define_info in global_var_defs.items():
        var_item = {
            "var": var_name,
            "type": define_info.type,
            "defined_in": define_info.file,
            "used_in": global_var_uses.get(var_name, [])
        }
        global_var_list.append(var_item)
    
    with open(file_name, "w") as f:
        json.dump(global_var_list, f, indent=2)
    logger.info(f"Global variable info saved to {file_name}")

def load_startup_analysis_result(full_call_graph, file_infos, output_dir, project_name):
    """加载启动分析结果并更新调用图和文件信息"""
    try:
        # 构建 startup_analysis_result.json 的路径
        startup_analysis_path = os.path.join(output_dir, project_name, "startup_analysis_result.json")
        if os.path.exists(startup_analysis_path):
            with open(startup_analysis_path, 'r', encoding='utf-8') as f:
                startup_data = json.load(f)
            
            # 构造启动文件的虚拟路径
            startup_file_path = "startup_file"  # 这里可以替换为实际的启动文件路径
            
            # 临时列表存储需要添加的函数
            funcs_to_add = []
            
            # 处理导出的函数
            exported_functions = startup_data.get("exported_functions", [])
            for func_info in exported_functions:
                func_name = func_info["name"]
                is_weak = func_info.get("is_weak", False)
                
                # 如果是 weak 函数且已经存在同名函数，则不覆盖
                if is_weak:
                    # 检查是否已经存在同名函数
                    func_exists = False
                    for existing_key in full_call_graph.keys():
                        if existing_key.endswith(f":{func_name}"):
                            func_exists = True
                            break
                    
                    # 如果函数不存在，则添加到临时列表
                    if not func_exists:
                        funcs_to_add.append(func_info)
                else:
                    # 非 weak 函数，直接添加到临时列表
                    funcs_to_add.append(func_info)
            
            # 统一处理添加函数到调用图和文件信息
            # 为启动文件生成一个全新的 file_info
            startup_file_info = {
                "file": startup_file_path,
                "functions": [],
                "includes": []
            }
            
            for func_info in funcs_to_add:
                func_name = func_info["name"]
                # 构造完整的函数键
                full_func_key = f"{startup_file_path}:{func_name}"
                
                # 添加到调用图
                full_call_graph[full_func_key] = []
                
                # 直接添加到启动文件的函数列表中，无需检查是否已存在
                startup_file_info["functions"].append({
                    "name": func_name,
                    "definded_in": startup_file_path,
                    "start_line": -1,
                    "end_line": -1
                })
            
            # 更新 file_infos
            file_infos[startup_file_path] = startup_file_info
            
            # 处理入口函数及其调用关系
            entry_function = startup_data.get("entry_function")
            entry_function_calls = startup_data.get("entry_function_calls", [])
            
            if entry_function:
                # 构造入口函数的完整键
                entry_func_key = f"{startup_file_path}:{entry_function}"
                
                # 确保入口函数在调用图中存在
                if entry_func_key not in full_call_graph:
                    full_call_graph[entry_func_key] = []
                    # 直接添加入口函数到启动文件的函数列表中，无需检查是否已存在
                    file_infos[startup_file_path]["functions"].append({
                        "name": entry_function,
                        "definded_in": startup_file_path,
                        "start_line": -1,
                        "end_line": -1
                    })

                # 添加入口函数调用的函数
                for called_func in entry_function_calls:
                    if called_func == "__main":
                        called_func = "main"
                    full_call_graph[entry_func_key].append(called_func)
        else:
            print(f"Startup analysis result file not found: {startup_analysis_path}")
    except Exception as e:
        logger.error(f"Loading startup analysis result: {e}")

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
        
    parser = argparse.ArgumentParser(description='Generate function call graph for C project')
    parser.add_argument('project_dir', help='Path to the C project directory')
    args = parser.parse_args(argv)

    project_dir = args.project_dir
    # 获取项目目录名
    project_name = os.path.basename(os.path.abspath(project_dir))
    # 创建输出目录
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # 从项目文件中提取包含路径
    project_include_paths = extract_include_paths_from_project(project_dir)
    
    # 去除重复的路径
    unique_project_include_paths = []
    for path in project_include_paths:
        if path not in unique_project_include_paths:
            unique_project_include_paths.append(path)
    project_include_paths = unique_project_include_paths
    
    # 从项目文件中提取预处理宏定义
    project_macros = extract_preprocessor_macros_from_project(project_dir)
    
    c_files = get_c_files(project_dir)

    full_call_graph = {}
    file_infos = {}  # 存储所有文件的信息
    all_struct_fields = {}  # 存储所有结构体字段信息
    all_struct_uses = defaultdict(list)  # 存储所有结构体使用信息
    all_global_var_defs: dict[str, GlobalVarInfo] = {}  # 存储所有全局变量定义
    all_global_var_uses = defaultdict(list)  # 存储所有全局变量使用
    all_macro_defs = {}  # 存储所有宏定义
    all_macro_uses = defaultdict(list)  # 存储所有宏使用信息

    # 添加更多参数以启用详细的AST解析
    parse_args = [
        project_dir, 
        "-I./include",
        "-I" + os.path.join(project_dir, "include"),
        "-I/usr/include",
        "-I/usr/local/include"
    ]
    
    # 添加从项目文件中提取的包含路径
    # 直接使用从项目配置中读取的路径
    for include_path in project_include_paths:
        parse_args.append("-I" + include_path)
    
    # 添加从项目文件中提取的预处理宏定义
    for macro_name, macro_value in project_macros.items():
        parse_args.append("-D" + macro_name + "=" + macro_value)

        
    # 保存未命名的结构与联合定义，后续如果再遇到同样的定义则不用解析
    struct_union_maps = {}

    for f in c_files:
        result = parse_file(f, struct_union_maps, args=parse_args)

        # 合并到全局调用关系
        for func, callees in result.graph.items():
            full_call_graph.setdefault(func, []).extend(callees)

        # 处理inline 函数
        functions = result.file_info["functions"]
        if functions:
            file = result.rel_path
            for func in functions:
                if func["definded_in"] != file:
                    definded_in = func["definded_in"]
                    if definded_in in file_infos:
                        file_infos[definded_in]["functions"].append(func)
                    else:
                        file_infos[definded_in] = {
                            "file": definded_in,
                            "functions": [func],
                            "includes": []
                        }

            result.file_info["functions"] = [
                func for func in functions if func["definded_in"] == file
            ]

        # 添加文件信息
        file_infos.update({
                result.rel_path: result.file_info
            }
        )

        #  处理头文件include
        for include_location_file in result.includes.keys():
            if include_location_file in file_infos:
                file_infos[include_location_file]["includes"] = list(result.includes[include_location_file])
            else:
                file_infos[include_location_file] = {
                    "file": include_location_file,
                    "functions": [],
                    "includes": list(result.includes[include_location_file])
                }
        
        # 合并结构体信息
        all_struct_fields.update(result.struct_fields)
        
        # 合并结构体使用信息
        for struct_name, uses in result.struct_uses.items():
            for use in uses:
                if use not in all_struct_uses[struct_name]:
                    all_struct_uses[struct_name].append(use)

        # 合并全局变量定义
        for var_name, def_info in result.global_var_defs.items():
            if def_info.is_definition:
                all_global_var_defs[var_name] = def_info
        
        # 合并全局变量使用信息
        for var_name, uses in result.global_var_uses.items():
            for use in uses:
                if use not in all_global_var_uses[var_name]:
                    all_global_var_uses[var_name].append(use)
        
        # 合并宏定义信息
        all_macro_defs.update(result.macro_defs)
        
        # 合并宏使用信息
        for macro_name, uses in result.macro_uses.items():
            for use in uses:
                if use not in all_macro_uses[macro_name]:
                    all_macro_uses[macro_name].append(use)
        
    # 函数调用去重
    for func_name, calls in full_call_graph.items():
        full_call_graph[func_name] = list(set(calls))

    # 加载启动分析结果并更新调用图和文件信息
    load_startup_analysis_result(full_call_graph, file_infos, output_dir, project_name)

    # 解析调用图绑定函数调的函数所在的文件，用于显示和保存
    full_call_graph = resolve_call_graph(full_call_graph)
    
    # 保存全局调用树（只保存全局的，不保存每个文件的）
    save_text_tree(full_call_graph, output_dir, project_name)

    # 保存调用图 JSON
    save_json(full_call_graph, output_dir, project_name)
    
    # 保存文件信息 JSON
    save_file_info_json(file_infos, output_dir, project_name, project_dir)
    
    # 保存结构体信息 JSON
    save_struct_info_json(all_struct_fields, all_struct_uses, output_dir, project_name)
    
    # 保存全局变量信息 JSON
    save_global_var_info_json(all_global_var_defs, all_global_var_uses, output_dir, project_name)
    
    # 保存宏信息 JSON
    save_macro_info_json(all_macro_defs, all_macro_uses, output_dir, project_name)
