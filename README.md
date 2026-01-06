# CodeDatasetMaker

CodeDatasetMaker 是一个专门用于分析嵌入式C项目的工具，它可以生成项目的函数调用图、结构体信息、宏定义信息等。

## 功能特性

- 生成项目的函数调用图
- 提取项目中的结构体、联合体和枚举信息
- 提取宏定义和全局变量信息
- 生成项目文件树
- 支持Keil和Eclipse CDT项目文件解析
- 模块分割分析
- 模块文档生成
- 结构体文档生成
- 函数文档生成
- 宏定义文档生成
- 全局变量文档生成
- 模块训练样本生成（Q&A格式）
- 结构体训练样本生成（Q&A格式）
- 函数训练样本生成（Q&A格式，包含源代码）
- 宏定义训练样本生成（Q&A格式，包含源代码）
- 全局变量训练样本生成（Q&A格式）

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

## 环境变量配置

为了安全起见，建议将API密钥存储在环境变量中，而不是直接写在配置文件里。

1. 复制 `.env.example` 文件并重命名为 `.env`：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入您的实际API密钥：
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

3. 在运行工具之前，确保加载环境变量：
   ```bash
   source .env  # Linux/macOS
   # 或者
   .env         # Windows
   ```

工具会优先使用环境变量中的 `OPENAI_API_KEY`，如果未设置才会从 `ai_config.json` 文件中读取。

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

### 模块文档生成

在生成代码分析数据和模块分割数据后，可以通过主脚本以doc模式运行模块文档生成工具：

```bash
python3 main.py --mode doc <项目路径>
```

例如：

```bash
python3 main.py --mode doc test_project
```

或者直接运行 `codedatasetmaker` 目录下的脚本：

```bash
python3 codedatasetmaker/generate_module_docs.py <项目路径>
```

这将在 `output/<项目名>/modules/` 目录下生成每个模块的文档提示词文件，这些文件包含了模块的源代码和元数据信息，可以提供给AI生成详细的模块文档。

### 模块训练样本生成

在生成模块文档后，可以通过主脚本以module_train模式运行模块训练样本生成工具：

```bash
python3 main.py --mode module_train <项目路径>
```

例如：

```bash
python3 main.py --mode module_train test_project
```

或者生成特定模块的训练样本：

```bash
python3 main.py --mode module_train test_project --module A0_main
```

也可以直接运行 `codedatasetmaker` 目录下的脚本：

```bash
python3 codedatasetmaker/generate_module_train.py <项目路径>
```

这将在 `output/<项目名>/train/modules/` 目录下生成每个模块的训练样本提示词文件，如果提供了有效的AI配置，还会生成完整的Q&A格式训练样本文件。

### 结构体训练样本生成

在生成结构体文档后，可以通过主脚本以struct_train模式运行结构体训练样本生成工具：

```bash
python3 main.py --mode struct_train <项目路径>
```

例如：

```bash
python3 main.py --mode struct_train test_project
```

或者生成特定结构体的训练样本：

```bash
python3 main.py --mode struct_train test_project --struct Person
```

也可以直接运行 `codedatasetmaker` 目录下的脚本：

```bash
python3 codedatasetmaker/generate_struct_train.py <项目路径>
```

这将在 `output/<项目名>/train/structs/` 目录下生成每个结构体的训练样本提示词文件，如果提供了有效的AI配置，还会生成完整的Q&A格式训练样本文件。

### 函数训练样本生成

在生成函数文档后，可以通过主脚本以function_train模式运行函数训练样本生成工具：

```bash
python3 main.py --mode function_train <项目路径>
```

例如：

```bash
python3 main.py --mode function_train test_project
```

或者生成特定函数的训练样本：

```bash
python3 main.py --mode function_train test_project --function src/main.c:main
```

也可以直接运行 `codedatasetmaker` 目录下的脚本：

```bash
python3 codedatasetmaker/generate_function_train.py <项目路径>
```

这将在 `output/<项目名>/train/functions/` 目录下生成每个函数的训练样本提示词文件，提示词文件中包含了函数的源代码。如果提供了有效的AI配置，还会生成完整的Q&A格式训练样本文件。

### 全局变量训练样本生成

在生成全局变量文档后，可以通过主脚本以global_var_train模式运行全局变量训练样本生成工具：

```bash
python3 main.py --mode global_var_train <项目路径>
```

例如：

```bash
python3 main.py --mode global_var_train test_project
```

或者生成特定全局变量的训练样本：

```bash
python3 main.py --mode global_var_train test_project --var g_system_state
```

也可以直接运行 `codedatasetmaker` 目录下的脚本：

```bash
python3 codedatasetmaker/generate_global_var_train.py <项目路径>
```

这将在 `output/<项目名>/train/global_vars/` 目录下生成每个全局变量的训练样本提示词文件，如果提供了有效的AI配置，还会生成完整的Q&A格式训练样本文件。

### 宏定义训练样本生成

在生成宏定义文档后，可以通过主脚本以macro_train模式运行宏定义训练样本生成工具：

```bash
python3 main.py --mode macro_train <项目路径>
```

例如：

```bash
python3 main.py --mode macro_train test_project
```

或者生成特定宏定义的训练样本：

```bash
python3 main.py --mode macro_train test_project --macro MAX_BUFFER_SIZE:include/config.h
```

也可以直接运行 `codedatasetmaker` 目录下的脚本：

```bash
python3 codedatasetmaker/generate_macro_train.py <项目路径>
```

这将在 `output/<项目名>/train/macros/` 目录下生成每个宏定义的训练样本提示词文件，提示词文件中包含了宏定义的源代码。如果提供了有效的AI配置，还会生成完整的Q&A格式训练样本文件。

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
- `module_structure.json`: 模块结构信息

### 模块文档生成

使用 `generate_module_docs.py` 脚本可以为项目中的每个模块生成文档提示词文件，这些文件位于 `output/<项目名>/modules/` 目录下，可以提供给AI生成详细的模块文档。

### 模块训练样本生成

使用 `generate_module_train.py` 脚本可以为项目中的每个模块生成训练样本提示词文件，这些文件位于 `output/<项目名>/train/modules/` 目录下。如果提供了有效的AI配置，还会生成完整的Q&A格式训练样本文件（`.md`格式），用于大模型微调。

### 结构体训练样本生成

使用 `generate_struct_train.py` 脚本可以为项目中的每个结构体生成训练样本提示词文件，这些文件位于 `output/<项目名>/train/structs/` 目录下。如果提供了有效的AI配置，还会生成完整的Q&A格式训练样本文件（`.md`格式），用于大模型微调。

## 项目结构

```
codedatasetmaker/
├── c_graph.py                         # 主要的分析脚本
├── generate_file_tree.py              # 生成文件树的脚本
├── module_splitter.py                 # 模块分割脚本
├── generate_module_docs.py            # 模块文档生成脚本
├── generate_struct_docs.py            # 结构体文档生成脚本
├── generate_function_docs.py          # 函数文档生成脚本
├── generate_macro_docs.py             # 宏定义文档生成脚本
├── generate_global_var_docs.py        # 全局变量文档生成脚本
├── generate_module_train.py           # 模块训练样本生成脚本
├── generate_struct_train.py           # 结构体训练样本生成脚本
├── generate_function_train.py         # 函数训练样本生成脚本
├── generate_global_var_train.py       # 全局变量训练样本生成脚本
├── generate_macro_train.py            # 宏定义训练样本生成脚本
├── module_doc_prompt_template.txt     # 模块文档提示词模板
├── struct_doc_prompt_template.txt     # 结构体文档提示词模板
├── function_doc_prompt_template.txt   # 函数文档提示词模板
├── global_var_doc_prompt_template.txt # 全局变量文档提示词模板
├── macro_doc_prompt_template.txt      # 宏定义文档提示词模板
├── module_train_prompt_template.txt   # 模块训练样本提示词模板
├── struct_train_prompt_template.txt   # 结构体训练样本提示词模板
├── function_train_prompt_template.txt # 函数训练样本提示词模板
├── global_var_train_prompt_template.txt # 全局变量训练样本提示词模板
├── macro_train_prompt_template.txt    # 宏定义训练样本提示词模板
└── __init__.py                       # Python 包初始化文件

main.py                 # 主入口脚本
ai_config.json          # AI访问配置文件
README.md               # 说明文档
```

## 注意事项

1. 确保你的系统上安装了 LLVM/Clang 库，并且路径配置正确。
2. 对于大型项目，分析过程可能需要一些时间。
3. 工具会自动检测 Keil 和 Eclipse CDT 项目文件中的包含路径和预处理器宏定义。
