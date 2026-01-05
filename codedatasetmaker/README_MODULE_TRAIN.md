# 模块级训练样本生成器

## 功能概述

`generate_module_train.py` 是一个模块级训练样本生成器，用于根据已生成的模块文档（位于 `output/项目名/modules/` 目录下）生成Q&A格式的训练样本。这些训练样本可以用于大模型微调，帮助模型理解嵌入式系统的模块设计。

## 使用方法

### 1. 通过 main.py 调用（推荐）

```bash
# 生成所有模块的训练样本
python3 main.py <项目路径> --mode module_train --output <输出目录>

# 生成特定模块的训练样本
python3 main.py <项目路径> --mode module_train --output <输出目录> --module <模块名>
```

**参数说明：**
- `<项目路径>`: 嵌入式C/C++项目的根目录路径
- `--output`: 输出目录路径（可选，默认为 `output`）
- `--module`: 指定生成特定模块的训练样本（可选）

### 2. 直接调用 generate_module_train.py

```bash
# 生成所有模块的训练样本
python3 codedatasetmaker/generate_module_train.py <项目路径> --output <输出目录> --ai-config <AI配置文件>

# 生成特定模块的训练样本
python3 codedatasetmaker/generate_module_train.py <项目路径> --output <输出目录> --ai-config <AI配置文件> --module <模块名>
```

**参数说明：**
- `<项目路径>`: 嵌入式C/C++项目的根目录路径
- `--output, -o`: 输出目录路径（可选，默认为 `output`）
- `--ai-config, -c`: AI配置文件路径（可选，默认为 `ai_config.json`）
- `--module, -m`: 指定生成特定模块的训练样本（可选）

## 输出结构

生成的文件将保存在以下目录结构中：
```
output/
└── <项目名>/
    └── train/
        └── modules/
            ├── <模块名>_train_prompt.txt    # 训练样本提示词文件
            └── <模块名>_train.md           # AI生成的训练样本文件（如果有有效的AI配置）
```

## 依赖文件

- **模块结构文件**: `output/<项目名>/module_structure.json`
- **模块文档文件**: `output/<项目名>/modules/<模块名>_doc.md`
- **提示词模板**: `codedatasetmaker/module_train_prompt_template.txt`

## AI 配置

如果提供了有效的AI配置文件（包含api_key），系统将自动调用AI API生成完整的训练样本（`.md`文件）。如果没有提供有效的AI配置，系统将只生成提示词文件（`.txt`文件），供手动使用。

AI配置文件示例 (`ai_config.json`)：
```json
{
    "api_key": "your-api-key",
    "model": "gpt-4",
    "train_model": "gpt-4-turbo",
    "base_url": "https://api.openai.com/v1"
}
```

## 训练样本格式

生成的训练样本遵循以下Q&A格式：

```markdown
### Q: [问题内容]
### A: [简短回答]
[详细解释内容]
[相关功能内容，如果没有可不写]  
[注意事项内容，如果没有可不写]
---
```

问题类型覆盖：
- 模块的核心职责与边界
- 模块在系统中的角色和作用
- 模块的依赖关系（输入依赖和输出能力）
- 模块的生命周期（初始化时机、运行周期、销毁情况）
- 模块的设计约束与潜在风险
- 模块的关键实现细节
- 模块与其他模块的交互方式

## 示例

生成 `A0_main` 模块的训练样本：

```bash
python3 main.py output/LCM32F0307_BLDC_V25.01-SDC717-250903-FS --mode module_train --module A0_main
```

这将生成：
- `output/LCM32F0307_BLDC_V25.01-SDC717-250903-FS/train/modules/A0_main_train_prompt.txt`
- 如果有有效的AI配置，还会生成 `output/LCM32F0307_BLDC_V25.01-SDC717-250903-FS/train/modules/A0_main_train.md`

## 注意事项

1. 确保已经运行过模块文档生成功能（`--mode doc`），因为模块训练样本生成器依赖于已生成的模块文档。
2. 模块名称必须与 `module_structure.json` 文件中的模块名称完全匹配。
3. 如果某个模块的文档文件不存在，该模块将被跳过。
4. AI API调用需要有效的API密钥和网络连接。
