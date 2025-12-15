# 模块边界切分工具

这是一个用于分析C项目模块边界的Python脚本，可以根据调用图和文件信息自动切分模块边界。

## 模块切分原则

1. 同一个目录下，如果有调用关系的文件应当合并成同一个模块
2. 不同目录的文件即使有调用关系也划分为不同模块
3. 模块划分基于连通分量算法，确保相关联的文件被分在同一模块中
4. 如果合并后的模块总大小超过128KB，则不进行合并
5. 包含初始化函数(init, config, setup等)的文件作为独立模块处理

## 功能特点

1. 自动加载指定目录中的 `call_graph.json` 和 `file_info.json` 文件
2. 分析函数调用关系，识别模块间的依赖关系
3. 识别每个模块包含的函数及其位置信息
4. 支持导出分析结果到JSON文件

## 使用方法

### 基本用法

```bash
python3 module_splitter.py <源码目录>
```

例如：
```bash
python3 module_splitter.py test_project
```

如果不指定输出目录，脚本会默认将结果输出到 `output/{项目名}` 目录中。

### 指定输出目录

```bash
python3 module_splitter.py <源码目录> -o <输出目录>
```

例如：
```bash
python3 module_splitter.py test_project -o output/modules
```

## 输入文件格式

### call_graph.json

调用图文件，描述了函数之间的调用关系：

```json
{
  "src/main.c:main": [
    "src/helper.c:function1",
    "src/helper.c:function2"
  ]
}
```

### file_info.json

文件信息文件，描述了每个文件中包含的函数及其位置：

```json
[
  {
    "file": "src/helper.c",
    "functions": [
      {
        "name": "function1",
        "start_line": 12,
        "end_line": 26
      }
    ],
    "includes": [
      "include/header.h"
    ]
  }
]
```

## 输出说明

脚本会输出每个模块的信息，包括：
- 模块名称
- 模块中包含的文件列表
- 模块间的依赖关系

如果使用 `-o` 参数指定了输出目录，还会生成一个 `module_structure.json` 文件，包含相同的分析结果。

## 示例输出

```
模块: main
----------------------------------------
  文件: src/main.c
  依赖模块: core, helper

模块: core
----------------------------------------
  文件: src/core/core_utils.c
  文件: src/core/core_math.c
  依赖模块: 无

模块: core_4
----------------------------------------
  文件: src/core/core.c
  文件: src/core/utils.c
  依赖模块: 无
```

## 文件大小限制

- 如果合并后的模块总大小超过128KB，则不进行合并
- 大文件会被单独作为一个模块处理

## 特殊处理

- main函数所在的文件总是作为一个独立的模块，不受同目录合并模块规则影响
- 包含初始化函数(init, config, setup等)的文件作为独立模块处理

## 模块命名规则

- 单文件模块使用文件名命名
- 多文件模块优先使用文件名的公共前缀
- 如果没有明显的公共前缀，则使用目录名
- 如果同一目录下有多个多文件模块，则增加数字编号

## 依赖

- Python 3.x

## 注意事项

1. 确保输入的JSON文件格式正确
2. 确保项目目录中同时包含 `call_graph.json` 和 `file_info.json` 文件
3. 脚本会自动处理在 `file_info.json` 中存在但在 `call_graph.json` 中未出现的函数
