#ifndef ADVANCED_FEATURES_H
#define ADVANCED_FEATURES_H

// 宏定义
#define MAX_BUFFER_SIZE 1024
#define MIN_BUFFER_SIZE 256
#define ENABLE_DEBUG 1
#define VERSION_STRING "1.0.0"

// 条件编译宏定义
#define CONFIG_BYTE_ORDER 1
#define CPU_BIG_ENDIAN 1

// 带参数的宏
#define SQUARE(x) ((x) * (x))
#define MAX(a, b) ((a) > (b) ? (a) : (b))

// 结构体定义
typedef struct {
    int id;
    char name[32];
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

// 全局变量声明
extern j_uint64_t global_uint64;
extern Person global_person;
extern Point global_point;

#endif // ADVANCED_FEATURES_H
