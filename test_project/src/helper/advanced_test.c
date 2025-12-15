#include "advanced_features.h"
#include "utils.h"
#include "core.h"
#include <stdio.h>

// 使用宏定义
void test_macros() {
    int buffer[MAX_BUFFER_SIZE];
    int min_size = MIN_BUFFER_SIZE;
    
#if ENABLE_DEBUG
    printf("Debug mode enabled, version: %s\n", VERSION_STRING);
#endif
    
    int val = 5;
    int squared = SQUARE(val);
    int max_val = MAX(val, 10);
    
    printf("Squared value: %d, Max value: %d\n", squared, max_val);
}

// 使用结构体
void test_structs() {
    // 基本结构体
    Person person = {1, "John Doe"};
    Point point = {100, 200};
    
    printf("Person: ID=%d, Name=%s\n", person.id, person.name);
    printf("Point: X=%d, Y=%d\n", point.x, point.y);
    
    // 带有宏开关条件编译的结构体
    j_uint64_t uint64_val;
    uint64_val.high = 0xFFFFFFFF;
    uint64_val.low = 0x00000000;
    
    printf("j_uint64_t: High=0x%08X, Low=0x%08X\n", uint64_val.high, uint64_val.low);
    
    // 嵌套结构体
    Item item;
    item.position = point;
    item.owner = person;
    
    printf("Item: Position=(%d,%d), Owner=%s\n", 
           item.position.x, item.position.y, item.owner.name);
    
    // 数组结构体
    ArrayStruct arr_struct;
    for(int i = 0; i < 10; i++) {
        arr_struct.values[i] = i * 10;
    }
    snprintf(arr_struct.label, sizeof(arr_struct.label), "Test Array");
    
    printf("ArrayStruct: Label=%s, Values=", arr_struct.label);
    for(int i = 0; i < 10; i++) {
        printf("%d ", arr_struct.values[i]);
    }
    printf("\n");
}

// 使用全局变量
void test_globals() {
    // 使用外部定义的全局变量
    global_uint64.high = 0x12345678;
    global_uint64.low = 0x9ABCDEF0;
    
    snprintf(global_person.name, sizeof(global_person.name), "Global User");
    global_person.id = 999;
    
    global_point.x = 500;
    global_point.y = 600;
    
    printf("Global j_uint64_t: High=0x%08X, Low=0x%08X\n", 
           global_uint64.high, global_uint64.low);
    printf("Global Person: ID=%d, Name=%s\n", global_person.id, global_person.name);
    printf("Global Point: X=%d, Y=%d\n", global_point.x, global_point.y);
}

// 主测试函数
void advanced_test_function() {
    printf("=== Advanced Features Test ===\n");
    
    test_macros();
    test_structs();
    test_globals();
    
    printf("=== Test Complete ===\n");
}
