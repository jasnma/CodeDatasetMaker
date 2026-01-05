#!/usr/bin/env python3

import sys
import os
import argparse

# 添加codedatasetmaker目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'codedatasetmaker'))

# 导入日志模块
from codedatasetmaker import logger

def analyze_project(project_dir, args):
    """运行代码分析功能"""
    # 添加codedatasetmaker目录到Python路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'codedatasetmaker'))
    
    # 导入c_graph模块并运行
    from codedatasetmaker import c_graph
    c_graph.main([project_dir] + args)

def split_modules(project_dir, args):
    """运行模块分割功能"""
    # 添加codedatasetmaker目录到Python路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'codedatasetmaker'))
    
    # 导入module_splitter模块
    from codedatasetmaker import module_splitter
    
    # 保存原始的sys.argv
    original_argv = sys.argv[:]
    
    # 设置新的sys.argv
    sys.argv = ['module_splitter.py', project_dir] + args
    
    module_splitter.main()


def generate_module_docs(project_dir, args):
    """运行模块文档生成功能"""
    # 添加codedatasetmaker目录到Python路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'codedatasetmaker'))
    
    # 导入generate_module_docs模块
    from codedatasetmaker import generate_module_docs
    
    # 保存原始的sys.argv
    original_argv = sys.argv[:]
    
    # 设置新的sys.argv
    sys.argv = ['generate_module_docs.py', project_dir] + args
    
    try:
        # 运行模块文档生成功能
        generate_module_docs.main()
    except Exception as e:
        logger.error(f"模块文档生成功能执行出错: {e}")
    finally:
        # 恢复原始的sys.argv
        sys.argv = original_argv


def generate_function_docs(project_dir, args):
    """运行函数文档生成功能"""
    # 添加codedatasetmaker目录到Python路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'codedatasetmaker'))
    
    # 导入generate_function_docs模块
    from codedatasetmaker import generate_function_docs
    
    # 保存原始的sys.argv
    original_argv = sys.argv[:]
    
    # 设置新的sys.argv
    sys.argv = ['generate_function_docs.py', project_dir] + args
    
    try:
        # 运行函数文档生成功能
        generate_function_docs.main()
    except Exception as e:
        logger.error(f"函数文档生成功能执行出错: {e}")
    finally:
        # 恢复原始的sys.argv
        sys.argv = original_argv


def generate_macro_docs(project_dir, args):
    """运行宏文档生成功能"""
    # 添加codedatasetmaker目录到Python路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'codedatasetmaker'))
    
    # 导入generate_macro_docs模块
    from codedatasetmaker import generate_macro_docs
    
    # 保存原始的sys.argv
    original_argv = sys.argv[:]
    
    # 设置新的sys.argv
    sys.argv = ['generate_macro_docs.py', project_dir] + args
    
    try:
        # 运行宏文档生成功能
        generate_macro_docs.main()
    except Exception as e:
        logger.error(f"宏文档生成功能执行出错: {e}")
    finally:
        # 恢复原始的sys.argv
        sys.argv = original_argv


def generate_struct_docs(project_dir, args):
    """运行结构体文档生成功能"""
    # 添加codedatasetmaker目录到Python路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'codedatasetmaker'))
    
    # 导入generate_struct_docs模块
    from codedatasetmaker import generate_struct_docs
    
    # 保存原始的sys.argv
    original_argv = sys.argv[:]
    
    # 设置新的sys.argv
    sys.argv = ['generate_struct_docs.py', project_dir] + args
    
    try:
        # 运行结构体文档生成功能
        generate_struct_docs.main()
    except Exception as e:
        logger.error(f"结构体文档生成功能执行出错: {e}")
    finally:
        # 恢复原始的sys.argv
        sys.argv = original_argv


def generate_global_var_docs(project_dir, args):
    """运行全局变量文档生成功能"""
    # 添加codedatasetmaker目录到Python路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'codedatasetmaker'))
    
    # 导入generate_global_var_docs模块
    from codedatasetmaker import generate_global_var_docs
    
    # 保存原始的sys.argv
    original_argv = sys.argv[:]
    
    # 设置新的sys.argv
    sys.argv = ['generate_global_var_docs.py', project_dir] + args
    
    try:
        # 运行全局变量文档生成功能
        generate_global_var_docs.main()
    except Exception as e:
        logger.error(f"全局变量文档生成功能执行出错: {e}")
    finally:
        # 恢复原始的sys.argv
        sys.argv = original_argv


def parse_startup(project_dir, args):
    """运行启动文件解析功能"""
    # 添加codedatasetmaker目录到Python路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'codedatasetmaker'))
    
    # 导入parse_startup模块
    from codedatasetmaker import parse_startup
    
    parse_startup.main([project_dir] + args)


def generate_startup_docs(project_dir, args):
    """运行启动流程文档生成功能"""
    # 添加codedatasetmaker目录到Python路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'codedatasetmaker'))
    
    # 导入generate_startup_docs模块
    from codedatasetmaker import generate_startup_docs
    
    # 保存原始的sys.argv
    original_argv = sys.argv[:]
    
    # 设置新的sys.argv
    sys.argv = ['generate_startup_docs.py', project_dir] + args
    
    try:
        # 运行启动流程文档生成功能
        generate_startup_docs.main()
    except Exception as e:
        logger.error(f"启动流程文档生成功能执行出错: {e}")
    finally:
        # 恢复原始的sys.argv
        sys.argv = original_argv


def generate_startup_train(project_dir, args):
    """运行启动流程训练样本生成功能"""
    # 添加codedatasetmaker目录到Python路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'codedatasetmaker'))
    
    # 导入generate_startup_train模块
    from codedatasetmaker import generate_startup_train
    
    # 保存原始的sys.argv
    original_argv = sys.argv[:]
    
    # 设置新的sys.argv
    sys.argv = ['generate_startup_train.py', project_dir] + args
    
    try:
        # 运行启动流程训练样本生成功能
        generate_startup_train.main()
    except Exception as e:
        logger.error(f"启动流程训练样本生成功能执行出错: {e}")
    finally:
        # 恢复原始的sys.argv
        sys.argv = original_argv


def generate_module_train(project_dir, args):
    """运行模块训练样本生成功能"""
    # 添加codedatasetmaker目录到Python路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'codedatasetmaker'))
    
    # 导入generate_module_train模块
    from codedatasetmaker import generate_module_train
    
    # 保存原始的sys.argv
    original_argv = sys.argv[:]
    
    # 设置新的sys.argv
    sys.argv = ['generate_module_train.py', project_dir] + args
    
    try:
        # 运行模块训练样本生成功能
        generate_module_train.main()
    except Exception as e:
        logger.error(f"模块训练样本生成功能执行出错: {e}")
    finally:
        # 恢复原始的sys.argv
        sys.argv = original_argv


def generate_struct_train(project_dir, args):
    """运行结构体训练样本生成功能"""
    # 添加codedatasetmaker目录到Python路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'codedatasetmaker'))
    
    # 导入generate_struct_train模块
    from codedatasetmaker import generate_struct_train
    
    # 保存原始的sys.argv
    original_argv = sys.argv[:]
    
    # 设置新的sys.argv
    sys.argv = ['generate_struct_train.py', project_dir] + args
    
    try:
        # 运行结构体训练样本生成功能
        generate_struct_train.main()
    except Exception as e:
        logger.error(f"结构体训练样本生成功能执行出错: {e}")
    finally:
        # 恢复原始的sys.argv
        sys.argv = original_argv


def main():
    parser = argparse.ArgumentParser(description='CodeDatasetMaker - C/C++项目分析工具')
    parser.add_argument('project_dir', help='项目目录路径')
    parser.add_argument('--mode', '-m', choices=['analyze', 'doc', 'f_doc', 'm_doc', 's_doc', 'g_doc', 'startup', 'startup_doc', 'startup_train', 'module_train', 'struct_train'], default='analyze',
                        help='运行模式: analyze(代码分析)、doc(生成模块文档)、f_doc(生成函数文档)、m_doc(生成宏文档)、s_doc(生成结构体文档)、g_doc(生成全局变量文档)、startup(解析启动文件)、startup_doc(生成启动流程文档)、startup_train(生成启动流程训练样本)、module_train(生成模块训练样本) 或 struct_train(生成结构体训练样本) (默认: analyze)')
    parser.add_argument('--output', '-o', help='输出目录路径')
    
    # 解析已知参数
    args, unknown_args = parser.parse_known_args()
    
    # 根据模式调用不同功能
    if args.mode == 'analyze':
        # 将未知参数传递给启动文件解析功能
        startup_args = unknown_args[:]
        if args.output:
            startup_args.extend(['--output', args.output])
        parse_startup(args.project_dir, startup_args)

        # 将未知参数传递给分析功能
        analyze_args = unknown_args[:]
        if args.output:
            analyze_args.extend(['--output', args.output])
        analyze_project(args.project_dir, analyze_args)

        split_args = unknown_args[:]
        if args.output:
            split_args.extend(['--output', args.output])
        split_modules(args.project_dir, split_args)
    elif args.mode == 'doc':
        # 将未知参数传递给模块文档生成功能
        doc_args = unknown_args[:]
        if args.output:
            doc_args.extend(['--output', args.output])
        generate_module_docs(args.project_dir, doc_args)
    elif args.mode == 'f_doc':
        # 将未知参数传递给函数文档生成功能
        f_doc_args = unknown_args[:]
        if args.output:
            f_doc_args.extend(['--output', args.output])
        generate_function_docs(args.project_dir, f_doc_args)
    elif args.mode == 'm_doc':
        # 将未知参数传递给宏文档生成功能
        m_doc_args = unknown_args[:]
        if args.output:
            m_doc_args.extend(['--output', args.output])
        generate_macro_docs(args.project_dir, m_doc_args)
    elif args.mode == 's_doc':
        # 将未知参数传递给结构体文档生成功能
        s_doc_args = unknown_args[:]
        if args.output:
            s_doc_args.extend(['--output', args.output])
        generate_struct_docs(args.project_dir, s_doc_args)
    elif args.mode == 'g_doc':
        # 将未知参数传递给全局变量文档生成功能
        g_doc_args = unknown_args[:]
        if args.output:
            g_doc_args.extend(['--output', args.output])
        generate_global_var_docs(args.project_dir, g_doc_args)
    elif args.mode == 'startup':
        # 将未知参数传递给启动文件解析功能
        startup_args = unknown_args[:]
        if args.output:
            startup_args.extend(['--output', args.output])
        parse_startup(args.project_dir, startup_args)
    elif args.mode == 'startup_doc':
        # 将未知参数传递给启动流程文档生成功能
        startup_doc_args = unknown_args[:]
        if args.output:
            startup_doc_args.extend(['--output', args.output])
        generate_startup_docs(args.project_dir, startup_doc_args)
    elif args.mode == 'startup_train':
        # 将未知参数传递给启动流程训练样本生成功能
        startup_train_args = unknown_args[:]
        if args.output:
            startup_train_args.extend(['--output', args.output])
        generate_startup_train(args.project_dir, startup_train_args)
    elif args.mode == 'module_train':
        # 将未知参数传递给模块训练样本生成功能
        module_train_args = unknown_args[:]
        if args.output:
            module_train_args.extend(['--output', args.output])
        generate_module_train(args.project_dir, module_train_args)
    elif args.mode == 'struct_train':
        # 将未知参数传递给结构体训练样本生成功能
        struct_train_args = unknown_args[:]
        if args.output:
            struct_train_args.extend(['--output', args.output])
        generate_struct_train(args.project_dir, struct_train_args)


if __name__ == "__main__":
    main()
