# CodeDatasetMaker

CodeDatasetMaker 是一个用于分析C/C++项目的工具，它可以生成项目的函数调用图、结构体信息、宏定义信息等。

## 功能特性

- 生成项目的函数调用图
- 提取项目中的结构体、联合体和枚举信息
- 提取宏定义和全局变量信息
- 生成项目文件树
- 支持Keil和Eclipse CDT项目文件解析

## 安装依赖

在运行此工具之前，请确保安装了以下依赖：

```bash
pip install clang anytree lxml
```

你还需要安装 LLVM/Clang 库。在 macOS 上，你可以使用 Homebrew 安装：

```bash
brew install llvm
```

在 Ubuntu 上，你可以使用 apt 安装：

```bash
sudo apt-get install llvm-dev libclang-dev
```

## 使用方法

### 生成代码分析数据（默认模式）

```bash
python3 main.py <项目路径>
```

例如：

```bash
python3 main.py test_project
```

### 模块分割分析

在生成代码分析数据后，可以使用模块分割工具分析项目的模块边界：

```bash
python3 main.py --mode split <项目路径>
```

例如：

```bash
python3 main.py --mode split test_project
```

### 直接运行脚本

你也可以直接运行 `codedatasetmaker` 目录下的脚本：

```bash
cd codedatasetmaker
python3 c_graph.py <项目路径>
python3 module_splitter.py <项目路径>
```

## 输出文件

工具运行后会在 `output/<项目名>` 目录下生成以下文件：

- `call_graph.json`: 函数调用图
- `call_text_tree.txt`: 函数调用树的文本表示
- `file_info.json`: 文件信息，包括函数列表和包含的头文件
- `project_tree.txt`: 项目文件树
- `struct_info.json`: 结构体、联合体和枚举信息
- `macro_info.json`: 宏定义信息
- `global_var_info.json`: 全局变量信息

## 项目结构

```
codedatasetmaker/
├── c_graph.py          # 主要的分析脚本
├── generate_file_tree.py # 生成文件树的脚本
├── module_splitter.py   # 模块分割脚本
└── __init__.py         # Python 包初始化文件

main.py                 # 主入口脚本
README.md               # 说明文档
```

## 注意事项

1. 确保你的系统上安装了 LLVM/Clang 库，并且路径配置正确。
2. 对于大型项目，分析过程可能需要一些时间。
3. 工具会自动检测 Keil 和 Eclipse CDT 项目文件中的包含路径和预处理器宏定义。
