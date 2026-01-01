# 启动流程文档生成功能说明

## 功能概述

本功能是CodeDatasetMaker工具的一部分，专门用于分析嵌入式C/C++项目的启动流程、初始化过程和主循环结构。它会自动生成分析所需的提示词文件，供AI进一步分析使用。

## 文件组成

### 主要脚本
1. `codedatasetmaker/generate_startup_docs.py` - 启动流程文档生成器主脚本
2. `codedatasetmaker/startup_doc_prompt_template.txt` - 提示词模板文件

### 生成的文件
1. `output/{project_name}/startup_doc_prompt.txt` - 启动流程分析提示词文件

## 工作原理

### 数据提取
脚本会从以下文件中提取必要的信息：
- `call_graph.json` - 函数调用关系图
- `file_info.json` - 函数源码位置信息

### 分析过程
1. 查找项目中的main函数
2. 构建main函数的调用树
3. 提取main函数及相关函数的源码
4. 识别主循环函数
5. 生成结构化的提示词文件

### 输出文件说明

#### startup_doc_prompt.txt
包含以下信息供AI分析：
- main函数调用树的JSON表示
- main函数源码
- 被main函数调用的关键函数源码
- 主循环函数信息（文件名和函数名）
- 主循环函数源码

#### main_call_tree.json
包含main函数完整调用树的JSON表示，可用于进一步的程序分析。

## 使用方法

### 通过主程序调用
```bash
python3 main.py {project_directory} --mode=startup_doc --output={output_directory}
```

### 直接调用脚本
```bash
python3 codedatasetmaker/generate_startup_docs.py {project_directory} --output {output_directory}
```

## 特点

1. **自动化分析** - 自动识别main函数和主循环函数
2. **结构化输出** - 生成标准化的提示词模板
3. **模块化设计** - 遵循项目现有的代码风格和架构
4. **容错处理** - 对于无法找到的源文件，会生成占位符文本而不是中断执行
5. **AI友好** - 生成的提示词可以直接用于AI分析工具

## 应用场景

1. **嵌入式系统分析** - 理解复杂的嵌入式系统启动流程
2. **代码文档生成** - 自动生成系统架构文档
3. **代码审查辅助** - 帮助开发人员快速理解项目结构
4. **新员工培训** - 快速熟悉项目启动和初始化过程
5. **系统重构** - 分析现有系统的依赖关系和调用链

## 扩展性

该功能采用模块化设计，可以轻松扩展以支持：
1. 不同的提示词模板
2. 更复杂的调用树分析
3. 与其他分析工具的集成
4. 多种输出格式的支持
