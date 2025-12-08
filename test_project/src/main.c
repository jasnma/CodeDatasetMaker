// 前向声明新的测试函数
void advanced_test_function();

#include "header.h"
#include "utils.h"
#include "core.h"
#include "advanced_features.h"

// 全局变量定义
int global_counter = 0;
char system_state = 0;

// 新增的全局变量定义
j_uint64_t global_uint64 = {0, 0};
Person global_person = {1, "Test User"};
Point global_point = {10, 20};

int main() {
    function1();
    function2();
    function3();
    function4();
    another_function();  // 调用helper3.c中的函数
    utility_function();  // 调用utils.c中的函数
    core_function();     // 调用core.c中的函数
    
    // 调用新的高级特性测试函数
    advanced_test_function();
    
    return 0;
}
