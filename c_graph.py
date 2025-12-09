#!/usr/bin/env python3

import argparse
import os
import json
import re
import clang.cindex
from anytree import Node, RenderTree
import xml.etree.ElementTree as ET
from collections import defaultdict

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

def parse_file(file_path, args=None):
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
    
    # 标准化文件路径，移除工作目录前缀（如果存在）
    normalized_path = os.path.abspath(file_path)
    project_root = os.path.abspath(args[0]) if args and len(args) > 0 and not args[0].startswith('-') else os.path.dirname(normalized_path)
    try:
        relative_path = os.path.relpath(normalized_path, project_root)
    except ValueError:
        # 处理跨驱动器的情况（Windows）
        relative_path = normalized_path

    # 存储结构体字段信息
    struct_fields = {}
    
    # 存储结构体使用信息
    struct_uses = defaultdict(list)  # 结构体名 -> [(文件路径:函数名), ...]
    
    # 存储全局变量定义和使用信息
    global_var_defs = {}  # 变量名 -> (类型, 文件路径)
    global_var_uses = defaultdict(list)  # 变量名 -> [(文件路径:函数名), ...]
    
    # 存储宏定义和使用信息
    macro_defs = {}  # 宏名 -> (内容, 文件路径)
    macro_uses = defaultdict(list)  # 宏名 -> [(文件路径:函数名/上下文), ...]
    
    def visit_node(node, current_func=None):
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
                # 添加到函数列表
                if func_name and func_name not in file_info["functions"]:
                    file_info["functions"].append(func_name)
                # 使用文件路径作为前缀来区分同名函数
                if func_name:
                    unique_func_name = f"{relative_path}:{func_name}"
                    call_graph.setdefault(unique_func_name, [])
                    current_func = unique_func_name
                    
                    # 检查函数参数中的结构体类型
                    for child in node.get_children():
                        if child.kind == clang.cindex.CursorKind.PARM_DECL:
                            param_type = child.type.spelling
                            # 检查是否是结构体类型
                            if param_type.startswith("struct "):
                                struct_name = param_type[7:]  # 去掉"struct "前缀
                                if struct_name:
                                    use_location = f"{relative_path}:{func_name}"
                                    if use_location not in struct_uses[struct_name]:
                                        struct_uses[struct_name].append(use_location)
                            # 也检查不带"struct "前缀的情况
                            else:
                                # 检查是否与已知结构体匹配
                                for s_name in struct_fields.keys():
                                    if s_name == param_type:
                                        use_location = f"{relative_path}:{func_name}"
                                        if use_location not in struct_uses[s_name]:
                                            struct_uses[s_name].append(use_location)
                                        
                # 继续遍历子节点以处理函数体内的调用
                for c in node.get_children():
                    visit_node(c, current_func)
            else:
                # 这是函数声明，不是定义，我们不处理它
                pass
        # 函数调用
        elif node.kind == clang.cindex.CursorKind.CALL_EXPR and current_func:
            # 获取被调用函数的名称
            called_func_cursor = node.referenced
            if called_func_cursor and called_func_cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                called_func_name = called_func_cursor.spelling
                # 记录调用关系
                if called_func_name:
                    call_graph[current_func].append(called_func_name)
            else:
                # 如果无法通过referenced获取，尝试使用node.spelling
                called_func_name = node.spelling
                if called_func_name:
                    call_graph[current_func].append(called_func_name)
        # 结构体定义
        elif node.kind == clang.cindex.CursorKind.STRUCT_DECL:
            struct_name = node.spelling
            
            # 对于匿名结构体或Clang无法正确识别名称的结构体，尝试多种方法获取正确名称
            if not struct_name or struct_name.startswith("struct (unnamed at"):
                # 方法1: 检查语义父节点是否是typedef声明
                semantic_parent = node.semantic_parent
                if semantic_parent and semantic_parent.kind == clang.cindex.CursorKind.TYPEDEF_DECL:
                    struct_name = semantic_parent.spelling
                # 方法2: 检查直接父节点是否是typedef声明
                elif hasattr(node, 'lexical_parent'):
                    lexical_parent = node.lexical_parent
                    if lexical_parent and lexical_parent.kind == clang.cindex.CursorKind.TYPEDEF_DECL:
                        struct_name = lexical_parent.spelling
                # 方法3: 在整个AST中查找是否有typedef声明引用了这个结构体
                if not struct_name or struct_name.startswith("struct (unnamed at"):
                    # 遍历整个AST查找引用这个结构体的typedef声明
                    def find_typedef_for_struct(root_node, target_struct_node):
                        if root_node.kind == clang.cindex.CursorKind.TYPEDEF_DECL:
                            # 检查typedef的子节点是否是我们正在处理的结构体
                            for child in root_node.get_children():
                                if child.kind == clang.cindex.CursorKind.STRUCT_DECL and child == target_struct_node:
                                    return root_node.spelling
                        # 递归检查子节点
                        for child in root_node.get_children():
                            result = find_typedef_for_struct(child, target_struct_node)
                            if result:
                                return result
                        return None
                    
                    typedef_name = find_typedef_for_struct(tu.cursor, node)
                    if typedef_name:
                        struct_name = typedef_name
                # 方法4: 通过解析源代码获取typedef名称
                if not struct_name or struct_name.startswith("struct (unnamed at"):
                    typedef_name = extract_typedef_name_from_source(file_path, node.location.line)
                    if typedef_name:
                        struct_name = typedef_name
                    else:
                        # 如果无法通过解析获取，尝试使用displayname作为备选方案
                        struct_name = node.displayname if node.displayname else "unnamed_struct"
            
            # 最后的备选方案
            if not struct_name:
                struct_name = "unnamed_struct"
            
            if struct_name and struct_name not in file_info["structs"]:
                file_info["structs"].append(struct_name)
                
            # 收集结构体字段信息
            fields = []
            for child in node.get_children():
                if child.kind == clang.cindex.CursorKind.FIELD_DECL:
                    field_name = child.spelling
                    field_type = child.type.spelling
                    # 检查字段是否是联合体
                    union_children = [grandchild for grandchild in child.get_children() if grandchild.kind == clang.cindex.CursorKind.UNION_DECL]
                    if union_children:
                        # 对于命名的联合体字段，获取联合体内部的字段信息
                        if field_name:
                            # 获取联合体内部的字段
                            union_fields = []
                            for union_child in union_children:
                                for union_field in union_child.get_children():
                                    if union_field.kind == clang.cindex.CursorKind.FIELD_DECL:
                                        union_field_name = union_field.spelling
                                        union_field_type = union_field.type.spelling
                                        union_fields.append({"name": union_field_name, "type": union_field_type})
                            # 构造包含联合体内部字段信息的类型描述
                            field_type = {"union": union_fields}
                        else:
                            # 对于匿名联合体，添加union前缀
                            field_type = "union " + field_type
                    fields.append({"name": field_name, "type": field_type})
            
            if struct_name and fields:
                # 获取结构体定义的实际位置
                definition_location = relative_path
                if node.location.file:
                    node_file_path = os.path.abspath(node.location.file.name)
                    try:
                        definition_location = os.path.relpath(node_file_path, project_root)
                    except ValueError:
                        definition_location = node_file_path
                        
                struct_fields[struct_name] = {
                    "struct": struct_name,
                    "fields": fields,
                    "defined_in": definition_location
                }
        # 联合体定义
        elif node.kind == clang.cindex.CursorKind.UNION_DECL:
            union_name = node.spelling
            
            # 对于匿名联合体或Clang无法正确识别名称的联合体，尝试多种方法获取正确名称
            if not union_name or union_name.startswith("union (unnamed at"):
                # 方法1: 检查语义父节点是否是typedef声明
                semantic_parent = node.semantic_parent
                if semantic_parent and semantic_parent.kind == clang.cindex.CursorKind.TYPEDEF_DECL:
                    union_name = semantic_parent.spelling
                # 方法2: 检查直接父节点是否是typedef声明
                elif hasattr(node, 'lexical_parent'):
                    lexical_parent = node.lexical_parent
                    if lexical_parent and lexical_parent.kind == clang.cindex.CursorKind.TYPEDEF_DECL:
                        union_name = lexical_parent.spelling
                # 方法3: 在整个AST中查找是否有typedef声明引用了这个联合体
                if not union_name or union_name.startswith("union (unnamed at"):
                    # 遍历整个AST查找引用这个联合体的typedef声明
                    def find_typedef_for_union(root_node, target_union_node):
                        if root_node.kind == clang.cindex.CursorKind.TYPEDEF_DECL:
                            # 检查typedef的子节点是否是我们正在处理的联合体
                            for child in root_node.get_children():
                                if child.kind == clang.cindex.CursorKind.UNION_DECL and child == target_union_node:
                                    return root_node.spelling
                        # 递归检查子节点
                        for child in root_node.get_children():
                            result = find_typedef_for_union(child, target_union_node)
                            if result:
                                return result
                        return None
                    
                    typedef_name = find_typedef_for_union(tu.cursor, node)
                    if typedef_name:
                        union_name = typedef_name
                # 方法4: 通过解析源代码获取typedef名称
                if not union_name or union_name.startswith("union (unnamed at"):
                    typedef_name = extract_typedef_name_from_source(file_path, node.location.line)
                    if typedef_name:
                        union_name = typedef_name
                    else:
                        # 如果无法通过解析获取，尝试使用displayname作为备选方案
                        union_name = node.displayname if node.displayname else "unnamed_union"
            
            # 最后的备选方案
            if not union_name:
                union_name = "unnamed_union"
            
            # 收集联合体字段信息
            fields = []
            for child in node.get_children():
                if child.kind == clang.cindex.CursorKind.FIELD_DECL:
                    field_name = child.spelling
                    field_type = child.type.spelling
                    fields.append({"name": field_name, "type": field_type})
            
            if union_name and fields:
                # 获取联合体定义的实际位置
                definition_location = relative_path
                if node.location.file:
                    node_file_path = os.path.abspath(node.location.file.name)
                    try:
                        definition_location = os.path.relpath(node_file_path, project_root)
                    except ValueError:
                        definition_location = node_file_path
                        
                # 为联合体创建一个特殊的条目，与结构体分开
                struct_fields[union_name] = {
                    "union": union_name,
                    "fields": fields,
                    "defined_in": definition_location
                }
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
                                macro_content = lines[line_num].strip()
                                
                        # 更新宏定义的位置信息
                        macro_definition_path = macro_relative_path
                    else:
                        # 如果文件不在项目目录内，使用当前文件路径
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            # 获取宏定义所在的行
                            line_num = node.location.line - 1  # 行号从1开始，索引从0开始
                            if line_num < len(lines):
                                macro_content = lines[line_num].strip()
                        macro_definition_path = relative_path
                else:
                    # 如果没有文件信息，使用当前文件路径
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # 获取宏定义所在的行
                        line_num = node.location.line - 1  # 行号从1开始，索引从0开始
                        if line_num < len(lines):
                            macro_content = lines[line_num].strip()
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
            if include_name and include_name not in file_info["includes"]:
                file_info["includes"].append(include_name)
        # 全局变量声明/定义
        elif node.kind == clang.cindex.CursorKind.VAR_DECL and not current_func:
            var_name = node.spelling
            var_type = node.type.spelling
            if var_name:
                # 检查这是否是一个定义（有初始化值）而不仅仅是一个声明
                is_definition = False
                for child in node.get_children():
                    # 如果变量有初始化子节点，则说明是定义而非声明
                    if child.kind in [clang.cindex.CursorKind.INTEGER_LITERAL, 
                                      clang.cindex.CursorKind.STRING_LITERAL,
                                      clang.cindex.CursorKind.INIT_LIST_EXPR,
                                      clang.cindex.CursorKind.UNEXPOSED_EXPR]:
                        is_definition = True
                        break
                
                # 如果没有明确的初始化，检查是否有赋值操作
                if not is_definition:
                    # 检查节点是否包含'='符号，这表明它是定义
                    try:
                        if node.location.file:
                            var_file_path = os.path.abspath(node.location.file.name)
                            with open(var_file_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                line_num = node.location.line - 1
                                if line_num < len(lines):
                                    line_content = lines[line_num]
                                    # 检查行中是否包含'='且不在字符串或注释中
                                    if '=' in line_content and not line_content.strip().startswith('//'):
                                        is_definition = True
                    except:
                        pass
                
                # 获取变量定义/声明的实际位置
                definition_location = relative_path
                if node.location.file:
                    node_file_path = os.path.abspath(node.location.file.name)
                    try:
                        definition_location = os.path.relpath(node_file_path, project_root)
                    except ValueError:
                        definition_location = node_file_path
                
                # 对于已经存在的全局变量，优先保留定义而非声明
                if var_name in global_var_defs:
                    existing_type, existing_path = global_var_defs[var_name]
                    # 如果当前节点是定义（无论现有记录是什么），都应该更新为当前位置
                    # 因为我们现在遇到了实际的定义
                    if is_definition:
                        global_var_defs[var_name] = (var_type, definition_location)
                    # 如果当前节点是声明，而现有记录也是声明，则保持现有记录不变
                    # （这样可以确保保留第一个遇到的声明位置）
                    elif not is_definition and not existing_path.endswith(('.c', '.cpp', '.cc')):
                        # 现有记录不是源文件中的定义，保持现有记录不变
                        pass
                    # 其他情况（当前是声明，现有是定义）保持现有定义不变
                else:
                    # 新的全局变量
                    global_var_defs[var_name] = (var_type, definition_location)
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
                            use_location = f"{relative_path}:{current_func.split(':')[-1]}"
                            if use_location not in global_var_uses[var_name]:
                                global_var_uses[var_name].append(use_location)
                    # 检查是否引用了结构体
                    elif referenced_decl.kind == clang.cindex.CursorKind.STRUCT_DECL:
                        struct_name = referenced_decl.spelling
                        if struct_name:
                            # 记录结构体的使用
                            use_location = f"{relative_path}:{current_func.split(':')[-1]}"
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
                struct_name = var_type[7:]  # 去掉"struct "前缀
                if struct_name:
                    context = current_func.split(':')[-1] if current_func else "global"
                    use_location = f"{relative_path}:{context}"
                    if use_location not in struct_uses[struct_name]:
                        struct_uses[struct_name].append(use_location)
            # 也检查不带"struct "前缀的情况
            else:
                # 检查是否与已知结构体匹配
                for struct_name in struct_fields.keys():
                    if struct_name == var_type:
                        context = current_func.split(':')[-1] if current_func else "global"
                        use_location = f"{relative_path}:{context}"
                        if use_location not in struct_uses[struct_name]:
                            struct_uses[struct_name].append(use_location)
                            
            # 检查返回类型是否是结构体
            result_type = node.result_type.spelling
            if result_type.startswith("struct "):
                struct_name = result_type[7:]  # 去掉"struct "前缀
                if struct_name:
                    context = current_func.split(':')[-1] if current_func else "global"
                    use_location = f"{relative_path}:{context}"
                    if use_location not in struct_uses[struct_name]:
                        struct_uses[struct_name].append(use_location)
            else:
                # 检查返回类型是否与已知结构体匹配
                for struct_name in struct_fields.keys():
                    if struct_name == result_type:
                        context = current_func.split(':')[-1] if current_func else "global"
                        use_location = f"{relative_path}:{context}"
                        if use_location not in struct_uses[struct_name]:
                            struct_uses[struct_name].append(use_location)
                            
        # 检查函数参数中的结构体类型使用
        elif node.kind == clang.cindex.CursorKind.PARM_DECL:
            param_type = node.type.spelling
            # 检查是否是结构体类型
            if param_type.startswith("struct "):
                struct_name = param_type[7:]  # 去掉"struct "前缀
                if struct_name:
                    # 获取参数所属的函数
                    parent = node.semantic_parent
                    if parent and parent.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                        func_name = parent.spelling
                        if func_name:
                            use_location = f"{relative_path}:{func_name}"
                            if use_location not in struct_uses[struct_name]:
                                struct_uses[struct_name].append(use_location)
            # 也检查不带"struct "前缀的情况
            else:
                # 检查是否与已知结构体匹配
                for struct_name in struct_fields.keys():
                    if struct_name == param_type:
                        # 获取参数所属的函数
                        parent = node.semantic_parent
                        if parent and parent.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                            func_name = parent.spelling
                            if func_name:
                                use_location = f"{relative_path}:{func_name}"
                                if use_location not in struct_uses[struct_name]:
                                    struct_uses[struct_name].append(use_location)
                            
        # 检查函数返回类型中的结构体类型使用
        elif node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
            return_type = node.result_type.spelling
            # 检查返回类型是否是结构体类型
            if return_type.startswith("struct "):
                struct_name = return_type[7:]  # 去掉"struct "前缀
                if struct_name:
                    func_name = node.spelling
                    if func_name:
                        use_location = f"{relative_path}:{func_name}"
                        if use_location not in struct_uses[struct_name]:
                            struct_uses[struct_name].append(use_location)
            # 也检查不带"struct "前缀的情况
            else:
                # 检查返回类型是否与已知结构体匹配
                for struct_name in struct_fields.keys():
                    if struct_name == return_type:
                        func_name = node.spelling
                        if func_name:
                            use_location = f"{relative_path}:{func_name}"
                            if use_location not in struct_uses[struct_name]:
                                struct_uses[struct_name].append(use_location)
                            
            # 继续遍历子节点以处理函数内部的使用情况
            for c in node.get_children():
                visit_node(c, node.spelling)
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
            visit_node(c, current_func)

    visit_node(tu.cursor)
    
    # 通过正则表达式额外提取宏使用情况，补充Clang可能遗漏的部分
    # extract_macro_uses_from_source(file_path, macro_uses, relative_path)

    # 通过正则表达式额外提取宏定义，补充Clang可能遗漏的部分
    # extract_macros_from_source(file_path, file_info)
    
    # 收集包含目录用于检查头文件
    include_dirs = [os.path.dirname(file_path)]  # 添加当前文件所在目录
    if args:
        for arg in args:
            if arg.startswith("-I"):
                include_dirs.append(arg[2:])  # 移除"-I"前缀
    
    # 通过正则表达式额外提取包含文件，补充Clang可能遗漏的部分
    # extract_includes_from_source(file_path, file_info, include_dirs)
    
    return call_graph, relative_path, file_info, struct_fields, struct_uses, global_var_defs, global_var_uses, macro_defs, macro_uses

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
                    print(f"Warning: Header file '{include_name}' not found (included in '{file_path}')")
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
                                    # 将相对路径转换为绝对路径
                                    if not os.path.isabs(path):
                                        path = os.path.join(os.path.dirname(project_file), path)
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
            path, func_name = full_key.split(':', 1)
            if func_name not in func_to_paths:
                func_to_paths[func_name] = []
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
    resolved_graph = resolve_call_graph(call_graph)
    project_output_dir = os.path.join(output_dir, project_name)
    os.makedirs(project_output_dir, exist_ok=True)
    file_name = os.path.join(project_output_dir, "call_graph.json")
    with open(file_name, "w") as f:
        json.dump(resolved_graph, f, indent=2)
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
    # 创建所有节点
    nodes = {f: Node(f) for f in call_graph}
    
    # 创建一个集合来跟踪已经处理过的父子关系，避免循环引用
    processed_relations = set()
    
    # 处理调用关系
    for parent, children in call_graph.items():
        for child in children:
            # 创建一个元组表示父子关系
            relation = (parent, child)
            # 如果这个关系已经被处理过，跳过以避免循环
            if relation in processed_relations:
                continue
            
            if child in nodes:
                # 检查是否会形成循环引用
                if not would_create_cycle(nodes[parent], nodes[child]):
                    # 直接连接，因为child已经是完整的键
                    nodes[child].parent = nodes[parent]
                    processed_relations.add(relation)
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
                                # 检查是否会形成循环引用
                                if not would_create_cycle(nodes[parent], nodes[node_key]):
                                    nodes[node_key].parent = nodes[parent]
                                    processed_relations.add((parent, node_key))
                                child_found = True
                                break
                    if not child_found:
                        new_child_key = f"unknown:{child}"
                        if new_child_key not in nodes:
                            nodes[new_child_key] = Node(new_child_key)
                        # 检查是否会形成循环引用
                        if not would_create_cycle(nodes[parent], nodes[new_child_key]):
                            nodes[new_child_key].parent = nodes[parent]
                            processed_relations.add((parent, new_child_key))
                else:
                    # child包含路径但不在nodes中
                    new_child_key = child
                    if new_child_key not in nodes:
                        nodes[new_child_key] = Node(new_child_key)
                    # 检查是否会形成循环引用
                    if not would_create_cycle(nodes[parent], nodes[new_child_key]):
                        nodes[new_child_key].parent = nodes[parent]
                        processed_relations.add((parent, new_child_key))
    
    # 找根节点：没有父节点的节点
    roots = [key for key, node in nodes.items() if node.parent is None]

    # 保存到文件
    text_tree_content = "Text Tree: Global Project\n"
    for root in roots:
        if root in nodes:
            for pre, _, node in RenderTree(nodes[root]):
                text_tree_content += pre + node.name + "\n"
    
    project_output_dir = os.path.join(output_dir, project_name)
    os.makedirs(project_output_dir, exist_ok=True)
    file_name = os.path.join(project_output_dir, "call_text_tree.txt")
    with open(file_name, "w") as f:
        f.write(text_tree_content)
    print(f"Text tree saved to {file_name}")

def save_file_info_json(file_infos, output_dir, project_name, project_dir):
    """保存文件信息为JSON"""
    # 简化文件信息，只保留functions和includes字段
    simplified_file_infos = []
    for file_info in file_infos:
        simplified_info = {
            "file": file_info["file"],
            "functions": file_info["functions"],
            "includes": file_info["includes"]
        }
        simplified_file_infos.append(simplified_info)
    
    project_output_dir = os.path.join(output_dir, project_name)
    os.makedirs(project_output_dir, exist_ok=True)
    file_name = os.path.join(project_output_dir, "file_info.json")
    with open(file_name, "w") as f:
        json.dump(simplified_file_infos, f, indent=2)
    print(f"File info saved to {file_name}")
    
    # 生成项目文件树
    generate_project_tree(project_dir, project_output_dir)

def generate_project_tree(project_dir, output_dir):
    """生成项目文件树"""
    def walk_directory(directory, prefix=""):
        entries = os.listdir(directory)
        entries.sort()
        tree_lines = []
        
        for i, entry in enumerate(entries):
            path = os.path.join(directory, entry)
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            
            if os.path.isdir(path):
                tree_lines.append(f"{prefix}{connector}{entry}/")
                extension = "    " if is_last else "│   "
                tree_lines.extend(walk_directory(path, prefix + extension))
            else:
                tree_lines.append(f"{prefix}{connector}{entry}")
        
        return tree_lines
    
    # 生成文件树文本
    tree_lines = [os.path.basename(project_dir) + "/"]
    tree_lines.extend(walk_directory(project_dir))
    
    # 保存文件树到文件
    file_name = os.path.join(output_dir, "project_tree.txt")
    with open(file_name, "w") as f:
        f.write("\n".join(tree_lines))
    
    print(f"Project tree saved to {file_name}")

def save_struct_info_json(struct_fields, struct_uses, output_dir, project_name):
    """保存结构体信息为JSON"""
    project_output_dir = os.path.join(output_dir, project_name)
    os.makedirs(project_output_dir, exist_ok=True)
    file_name = os.path.join(project_output_dir, "struct_info.json")
    
    # 转换结构体信息格式
    struct_list = []
    for struct_name, info in struct_fields.items():
        # 检查是结构体还是联合体
        if "struct" in info:
            # 结构体
            struct_item = {
                "struct": info["struct"],
                "fields": info["fields"],
                "defined_in": info["defined_in"],
                "used_by": struct_uses.get(struct_name, [])
            }
        elif "union" in info:
            # 联合体
            struct_item = {
                "union": info["union"],
                "fields": info["fields"],
                "defined_in": info["defined_in"],
                "used_by": struct_uses.get(struct_name, [])
            }
        else:
            # 默认情况下，假设是结构体
            struct_item = {
                "struct": struct_name,
                "fields": info["fields"],
                "defined_in": info["defined_in"],
                "used_by": struct_uses.get(struct_name, [])
            }
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
        if not is_clang_builtin:
            macro_item = {
                "macro": macro_name,
                "content": content,
                "defined_in": defined_in,
                "used_in": macro_uses.get(macro_name, [])
            }
            macro_list.append(macro_item)
    
    with open(file_name, "w") as f:
        json.dump(macro_list, f, indent=2)
    print(f"Macro info saved to {file_name}")

def save_global_var_info_json(global_var_defs, global_var_uses, output_dir, project_name):
    project_output_dir = os.path.join(output_dir, project_name)
    os.makedirs(project_output_dir, exist_ok=True)
    file_name = os.path.join(project_output_dir, "global_var_info.json")
    
    # 转换全局变量信息格式
    global_var_list = []
    for var_name, (var_type, defined_in) in global_var_defs.items():
        var_item = {
            "var": var_name,
            "type": var_type,
            "defined_in": defined_in,
            "used_in": global_var_uses.get(var_name, [])
        }
        global_var_list.append(var_item)
    
    with open(file_name, "w") as f:
        json.dump(global_var_list, f, indent=2)
    print(f"Global variable info saved to {file_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate function call graph for C project')
    parser.add_argument('project_dir', help='Path to the C project directory')
    args = parser.parse_args()

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
    file_infos = []  # 存储所有文件的信息
    all_struct_fields = {}  # 存储所有结构体字段信息
    all_struct_uses = defaultdict(list)  # 存储所有结构体使用信息
    all_global_var_defs = {}  # 存储所有全局变量定义
    all_global_var_uses = defaultdict(list)  # 存储所有全局变量使用
    all_macro_defs = {}  # 存储所有宏定义
    all_macro_uses = defaultdict(list)  # 存储所有宏使用信息
    
    for f in c_files:
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
        
        graph, rel_path, file_info, struct_fields, struct_uses, global_var_defs, global_var_uses, macro_defs, macro_uses = parse_file(f, args=parse_args)
        if not graph:
            continue

        # 合并到全局调用关系
        for func, callees in graph.items():
            full_call_graph.setdefault(func, []).extend(callees)
        
        # 添加文件信息
        file_infos.append(file_info)
        
        # 合并结构体信息
        all_struct_fields.update(struct_fields)
        
        # 合并结构体使用信息
        for struct_name, uses in struct_uses.items():
            for use in uses:
                if use not in all_struct_uses[struct_name]:
                    all_struct_uses[struct_name].append(use)
        
        # 合并全局变量定义
        all_global_var_defs.update(global_var_defs)
        
        # 合并全局变量使用信息
        for var_name, uses in global_var_uses.items():
            for use in uses:
                if use not in all_global_var_uses[var_name]:
                    all_global_var_uses[var_name].append(use)
        
        # 合并宏定义信息
        all_macro_defs.update(macro_defs)
        
        # 合并宏使用信息
        for macro_name, uses in macro_uses.items():
            for use in uses:
                if use not in all_macro_uses[macro_name]:
                    all_macro_uses[macro_name].append(use)

    # 解析调用图用于显示和保存
    resolved_graph = resolve_call_graph(full_call_graph)
    
    # 保存全局调用树（只保存全局的，不保存每个文件的）
    save_text_tree(resolved_graph, output_dir, project_name)

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
