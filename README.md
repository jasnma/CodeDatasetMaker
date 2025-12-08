# Code Dataset Maker

这个工具集可以帮助你分析C语言项目，提取函数调用关系、结构体、宏定义等信息，并生成项目文件树。

## 功能特性

1. **函数调用图生成** - 分析C项目中的函数调用关系
2. **代码元素提取** - 提取函数、结构体、宏定义等信息
3. **项目文件树生成** - 生成项目文件结构树，可忽略不必要的文件

## 依赖安装

```bash
pip install clang libclang anytree
```

在macOS上，你可能还需要安装LLVM：

```bash
brew install llvm
```

## 使用方法

### 1. 函数调用图生成

```bash
python3 c_graph.py <project_directory>
```

这将生成以下文件：
- `output/<project_name>/call_graph.json` - 函数调用关系JSON
- `output/<project_name>/file_info.json` - 文件信息（函数、结构体、宏定义等）
- `output/<project_name>/global_project_text_tree.txt` - 文本格式的调用树

### 2. 项目文件树生成

```bash
# 基本用法（默认会输出到 output/<project_name>/file_tree.txt）
python3 generate_file_tree.py <project_directory>

# 保存为指定的JSON文件名
python3 generate_file_tree.py <project_directory> -o <output_file_name>

# 限制树的深度
python3 generate_file_tree.py <project_directory> -d <max_depth>
```

所有输出文件都会自动保存在 `output/<project_name>/` 目录中。如果不指定输出文件名，将默认保存为 `file_tree.txt`（文本格式）。如果需要JSON格式，可以使用 `-o file_tree.json` 参数。

## 输出格式说明

### 函数调用图 (call_graph.json)

```json
{
  "src/main.c:main": [
    "src/helper.c:function1",
    "src/helper.c:function2"
  ],
  "src/helper.c:function1": [
    "src/utils.c:utility_function"
  ]
}
```

### 文件信息 (file_info.json)

```json
[
  {
    "file": "motor.c",
    "functions": [
      "motor_init",
      "motor_start"
    ],
    "structs": [
      "MotorState",
      "PIDController"
    ],
    "macros": [
      "MOTOR_MAX_SPEED",
      "MOTOR_MIN_SPEED"
    ],
    "includes": [
      "motor.h",
      "bldc_ctrl.h"
    ]
  }
]
```

### 项目文件树 (JSON格式)

```json
[
  {
    "name": "src",
    "type": "directory",
    "children": [
      {
        "name": "main.c",
        "type": "file"
      }
    ]
  }
]
```

## 忽略的文件类型

以下文件和目录会被自动忽略：
- 编译产物：`.o`, `.obj`, `.exe`, `.dll`, `.so`, `.dylib`
- Python字节码：`.pyc`, `.pyo`, `.pyd`
- 日志和临时文件：`.log`, `.tmp`, `.temp`
- 系统文件：`.gitignore`, `.DS_Store`, `Thumbs.db`
- 特殊目录：`.git`, `__pycache__`, `.vscode`, `.idea`
- 构建目录：`node_modules`, `build`, `dist`
- 环境文件：`.env`, `.venv`, `venv`, `env`

## 示例

分析一个C项目：

```bash
python3 c_graph.py ./test_project
python3 generate_file_tree.py ./test_project -o project_tree.json
