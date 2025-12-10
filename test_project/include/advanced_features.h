#ifndef ADVANCED_FEATURES_H
#define ADVANCED_FEATURES_H

// 宏定义
#define MAX_BUFFER_SIZE 1024
#define MIN_BUFFER_SIZE 256
#define ENABLE_DEBUG 1
#define VERSION_STRING "1.0.0"

// 条件编译宏定义
#define CPU_BIG_ENDIAN 1
#define CPU_LITTLE_ENDIAN 0
#define CONFIG_BYTE_ORDER CPU_BIG_ENDIAN

// 带参数的宏
#define SQUARE(x) ((x) * (x))
#define MAX(a, b) ((a) > (b) ? (a) : (b))

#define TAILQ_ENTRY(type)                                               \
struct {                                                                \
    struct type *tqe_next;  /* next element */                          \
    struct type *tqe_prev; /* address of previous next element */      \
}

// 结构体定义
typedef struct {
    int id;
    char name[32];

    TAILQ_ENTRY(Person) next;
} Person;

typedef struct {
    int x;
    int y;
} Point;

// 带有宏开关条件编译的结构体（这是我们要重点测试的功能）
typedef struct {
#if CONFIG_BYTE_ORDER == CPU_BIG_ENDIAN
    unsigned int high;
    unsigned int low;
#else
    unsigned int low;
    unsigned int high;
#endif

#if _DEBUG
    char debug_info[256];
#else
    char release_info[256];
#endif
} j_uint64_t;

// 嵌套结构体
typedef struct {
    Point position;
    Person owner;
} Item;

// 包含数组的结构体
typedef struct {
    int values[10];
    char label[20];
} ArrayStruct;

// 包含指针的结构体
typedef struct {
    char* name;
    int* data;
} PointerStruct;

// 包含函数指针的结构体
typedef struct {
    int (*compare)(int a, int b);
    void (*callback)(void);
} CallbackStruct;

typedef unsigned char uint8_t;
typedef unsigned short uint16_t;

/* String character encodings */
typedef enum {
    J_ST_ASCII,
    J_ST_UTF8,
    J_ST_UTF16,
    J_ST_UTF16BE, /* Only valid for @src_type parameters */
    J_ST_UTF16LE  /* Only valid for @src_type parameters */
} j_string_type_t;

typedef union {
    char ascii_tag;
    uint8_t utf8_tag;
    uint16_t utf16_tag;
} string_tag;

/* JOS string */
typedef struct {
    j_string_type_t type;
    string_tag tag;
    union {
        char     ascii[1];
        uint8_t  utf8[1];
        uint16_t utf16[1];
    } s;
} j_string_t;

union advanced_features
{
    struct {
        int a_value;
        int a_count;
    } a;

    struct {
        int b_value;
        int b_count;
    } b;
};

// 全局变量声明
extern j_uint64_t global_uint64;
extern Person global_person;
extern Point global_point;

#endif // ADVANCED_FEATURES_H
