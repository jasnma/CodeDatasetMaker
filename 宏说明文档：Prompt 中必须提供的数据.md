## 宏说明文档：Prompt 中必须提供的数据
### 1️⃣ 必须提供（硬性）
这是**不可缺失的最小集合**：

### （1）宏的原始定义（强制）
```plain
#define ADC_MAX_VALUE 4095
#define SET_BIT(reg, bit) ((reg) |= (1U << (bit)))
```

→ **原样提供，不要裁剪**

---

### （2）宏所在文件 + 行号（或作用域）
```plain
{
  "defined_in": "Driver/ADC/adc_defs.h",
  "line": 123
}
```

**作用**：

+ 判断这是 **配置宏 / 运算宏 / 接口宏**
+ 判断模块归属

---

### （3）宏分类（你可以自动给）
你已有 JSON 就可以生成：

```plain
{
  "macro_type": "constant | function-like | bit-mask | config-switch"
}
```

LLM 对不同类型的说明方式完全不同。

---

### 2️⃣ 强烈建议提供（决定说明深度）
### （4）宏被引用的位置（非常重要）
至少给 **Top N（如前 5）引用点**：

```plain
"used_in": [
  {
    "file": "adc.c",
    "function": "ADC_Init",
    "line": 88
  }
]
```

**LLM 能据此推断：**

+ 是否是初始化宏
+ 是否影响状态机
+ 是否是安全关键宏

⚠️ 没有使用点，LLM 只能写“这是一个用于……的宏”（废话级）

---

### （5）是否参与条件编译
```plain
#if defined(ENABLE_ADC_DMA)
#define ADC_USE_DMA 1
#endif
```

→ 提供：

```plain
{
  "conditional": true,
  "condition": "ENABLE_ADC_DMA"
}
```

---

### 3️⃣ 可选但极有价值
### （6）宏展开后的表达式类型（可自动推断）
```plain
{
  "expands_to": "integer constant | expression | statement | block"
}
```

用于风险分析（副作用、多次求值）。

