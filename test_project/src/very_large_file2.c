#include <stdio.h>

// 创建另一个非常大的文件用于测试大小限制功能

void another_very_large_function_1() {
    int i;
    for (i = 0; i < 5000; i++) {
        printf("This is another very large function 1, iteration %d\n", i);
    }
}

void another_very_large_function_2() {
    int i;
    for (i = 0; i < 5000; i++) {
        printf("This is another very large function 2, iteration %d\n", i);
    }
}

void another_very_large_function_3() {
    int i;
    for (i = 0; i < 5000; i++) {
        printf("This is another very large function 3, iteration %d\n", i);
    }
}
