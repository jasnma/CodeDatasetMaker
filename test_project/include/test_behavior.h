// 测试基于行为特征的保护宏识别

// 标准保护宏模式
#ifndef TEST_BEHAVIOR_H
#define TEST_BEHAVIOR_H

// 真实的宏定义
#define BEHAVIOR_REAL_MACRO 100

// 带参数的宏
#define BEHAVIOR_ADD(x, y) ((x) + (y))

#endif // TEST_BEHAVIOR_H

// 非标准保护宏（应该被识别为真实宏）
#ifndef test_behavior_h
#define test_behavior_h

#define BEHAVIOR_ANOTHER_REAL_MACRO 200

#endif

// 错误的保护宏模式（应该被识别为真实宏）
#ifdef TEST_BEHAVIOR_INCORRECT
#define TEST_BEHAVIOR_INCORRECT

#define BEHAVIOR_YET_ANOTHER_REAL_MACRO 300

#endif
