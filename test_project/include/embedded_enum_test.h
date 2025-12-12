#ifndef EMBEDDED_ENUM_TEST_H
#define EMBEDDED_ENUM_TEST_H

// 测试在结构体中内嵌枚举
typedef struct {
    int id;
    enum {
        STATUS_ACTIVE = 1,
        STATUS_INACTIVE = 0
    } status;
    char name[50];
} UserWithEmbeddedEnum;

// 测试在联合体中内嵌枚举
typedef union {
    int value;
    enum {
        TYPE_INTEGER = 0,
        TYPE_FLOAT = 1
    } type;
} DataWithEmbeddedEnum;

#endif // EMBEDDED_ENUM_TEST_H
