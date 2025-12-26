#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
C语言解析工具函数
用于查找注释、剥离注释等操作
"""

def find_doc_comment_start(lines, start_line):
    """
    支持：
      - // 单行注释
      - /* ... */ 单行块注释
      - /**** 多行块注释，带对齐 * 
    """
    i = start_line - 2  # 上一行
    comment_start = None
    in_block_comment = False

    while i >= 0:
        line = lines[i].rstrip()
        stripped = line.strip()

        # 空行
        if stripped == "" and not in_block_comment:
            break

        # 行注释 //
        if stripped.startswith("//"):
            comment_start = i + 1
            i -= 1
            continue

        # 块注释结束 */
        if stripped.endswith("*/"):
            comment_start = i + 1
            in_block_comment = True
            i -= 1
            continue

        # 块注释中间行（* 对齐）
        if in_block_comment:
            comment_start = i + 1
            if stripped.startswith("/*"):
                in_block_comment = False
            i -= 1
            continue

        # 单行块注释 /* ... */
        if stripped.startswith("/*") and stripped.endswith("*/"):
            comment_start = i + 1
            i -= 1
            continue

        # 非注释，终止
        break

    return comment_start


# 从一行中剥离 C 注释，这是反向向前推的，每处理一行代码，下一行代码是当前行的前一行
def strip_c_comments_r(line, in_block_comment):
    """
    反向扫描一行，剥离 C 注释
    :param line: 字符串
    :param in_block_comment: 是否当前在多行注释内部
    :return: (clean_line, in_block_comment)
    """
    i = len(line) - 1
    result = []

    while i >= 0:
        # 当前在块注释内部，找开始标记 /*
        if in_block_comment:
            if i > 0 and line[i-1:i+1] == "/*":
                in_block_comment = False
                i -= 2
            else:
                i -= 1
            continue

        # 当前不在块注释内部，遇到结束标记 */
        if i > 0 and line[i-1:i+1] == "*/":
            in_block_comment = True
            i -= 2
            continue

        # 普通字符，加入结果
        result.append(line[i])
        i -= 1

    # 反转回正常顺序
    result.reverse()
    return "".join(result), in_block_comment


def find_prev_effective_line(lines, start_line):
    j = start_line - 1
    in_block_comment = False

    while j >= 0:
        raw = lines[j].rstrip()
        cleaned, in_block_comment = strip_c_comments_r(raw, in_block_comment)
        stripped = cleaned.strip()

        if not stripped:
            j -= 1
            continue

        if stripped.startswith("//"):
            j -= 1
            continue

        return j, stripped

    return None, None