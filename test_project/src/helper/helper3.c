void function1() {
    // 这是第三个文件中的function1，与helper.c中的function1同名
}

void another_function() {
    function1();  // 应该调用helper3.c:function1
    sub_function();  // 应该调用helper3.c:sub_function（如果存在）
}

void sub_function() {
    // helper3.c中的sub_function
}
