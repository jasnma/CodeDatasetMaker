#include "../include/test_guards.h"
#include <stdio.h>

void test_guards_function() {
    printf("REAL_MACRO = %d\n", REAL_MACRO);
    printf("REAL_MACRO2 = %d\n", REAL_MACRO2);
    printf("REAL_MACRO3 = %d\n", REAL_MACRO3);
    printf("REAL_MACRO4 = %d\n", REAL_MACRO4);
    printf("REAL_MACRO5 = %d\n", REAL_MACRO5);
    printf("REAL_MACRO6 = %d\n", REAL_MACRO6);
}
