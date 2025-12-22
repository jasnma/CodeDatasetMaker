#include "../include/test_behavior.h"
#include <stdio.h>

void test_behavior_function() {
    printf("BEHAVIOR_REAL_MACRO = %d\n", BEHAVIOR_REAL_MACRO);
    printf("BEHAVIOR_ADD(1, 2) = %d\n", BEHAVIOR_ADD(1, 2));
    printf("BEHAVIOR_ANOTHER_REAL_MACRO = %d\n", BEHAVIOR_ANOTHER_REAL_MACRO);
    printf("BEHAVIOR_YET_ANOTHER_REAL_MACRO = %d\n", BEHAVIOR_YET_ANOTHER_REAL_MACRO);
}
