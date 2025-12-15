#include "header.h"
#include "utils.h"
#include "advanced_features.h"

// 全局变量声明
extern int global_counter;
extern char system_state;

// 使用外部定义的结构体
// 结构体定义已移到advanced_features.h中

void function1() {
    // 函数1实现
    shared_helper();  // 调用utils中的函数
    
    // 使用全局变量
    global_counter++;
    
    // 使用结构体
    Person p;
    p.id = 1;
    p.name[0] = 'A';
    
    Point pt;
    pt.x = 10;
    pt.y = 20;
}

void function2() {
    // 函数2实现
    sub_function();
    utility_function();  // 调用utils中的函数
    
    // 使用全局变量
    system_state = 1;
    
    // 使用结构体
    Person p;
    p.id = 2;
    
    Point pt;
    pt.x = 30;
}

void sub_function() {
    // sub_function实现
    // 使用全局变量
    global_counter += 2;
    
    // 使用结构体
    Person p;
    Point pt;
    pt.y = 40;
}
