### 1️⃣ 必须提供（硬性）
### （1）结构体完整定义（原样）
```plain
typedef struct {
    uint16_t voltage;
    uint16_t current;
    uint8_t  state;
} MotorStatus_t;
```

**绝对不要只给字段名**

---

### （2）定义位置 + 文件
```plain
{
  "defined_in": "Motor/motor_types.h",
  "scope": "module | global"
}
```

---

### 2️⃣ 强烈建议提供（决定“是不是专家级文档”）
### （3）每个字段的「使用上下文」
你不需要 100%，**只要字段被谁读 / 谁写**：

```plain
"fields_usage": {
  "voltage": {
    "written_in": ["ADC_Task"],
    "read_in": ["Motor_Control"]
  }
}
```

LLM 能自动推断：

+ 数据来源
+ 数据流向
+ 是否状态变量 / 输入量 / 计算结果

---

### （4）结构体实例信息（非常关键）
```plain
"instances": [
  {
    "name": "g_motor_status",
    "storage": "global",
    "lifetime": "system"
  }
]
```

这一步 **直接决定风险分析是否可信**

---

### （5）是否作为接口结构体
比如：

+ 函数参数
+ ISR 与主循环共享
+ 模块 API 暴露

```plain
{
  "used_as": ["function_param", "global_state", "ipc"]
}
```

---

## 四、Prompt 中应明确告诉 LLM「你要它做什么」
**示例 Prompt（结构体）**

```plain
你是一名资深嵌入式软件架构师。

请基于以下信息，为结构体 `MotorStatus_t` 生成专业文档说明，要求包括：
1. 结构体整体设计意图
2. 各字段的业务语义与数据来源
3. 使用场景与典型生命周期
4. 并发/中断/一致性风险
5. 使用与扩展注意事项

请避免复述代码，侧重设计层面的说明。
```

