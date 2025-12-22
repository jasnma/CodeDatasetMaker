// 测试各种形式的保护宏

// 标准形式1: FILENAME_H
#ifndef TEST_GUARDS_H
#define TEST_GUARDS_H

#define REAL_MACRO 1

#endif // TEST_GUARDS_H

// 标准形式2: _FILENAME_H_
#ifndef _TEST_GUARDS2_H_
#define _TEST_GUARDS2_H_

#define REAL_MACRO2 2

#endif // _TEST_GUARDS2_H_

// 标准形式3: FILENAME_H_
#ifndef TEST_GUARDS3_H_
#define TEST_GUARDS3_H_

#define REAL_MACRO3 3

#endif

// 标准形式4: FILENAME_INC
#ifndef TEST_GUARDS_INC
#define TEST_GUARDS_INC

#define REAL_MACRO4 4

#endif

// 标准形式5: FILENAME_INCLUDE
#ifndef TEST_GUARDS_INCLUDE
#define TEST_GUARDS_INCLUDE

#define REAL_MACRO5 5

#endif

// 非标准但应识别为保护宏的形式
#ifndef test_guards_h
#define test_guards_h

#define REAL_MACRO6 6

#endif
