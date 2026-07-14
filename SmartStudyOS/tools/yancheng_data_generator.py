#!/usr/bin/env python3
# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""盐城市1-6年级各科教材数据生成器。

基于2026年盐城市小学教材版本：
  - 语文：部编版（人教版）
  - 数学：苏教版（江苏教育出版社）
  - 英语：译林版（译林出版社，三年级起）
  - 科学：苏教版

输出：resource/knowledge/yancheng_*/grade*.json
      resource/questions/yancheng_*/grade*.json
"""

from __future__ import annotations

import json
import os
import sys
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

# 确保路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "resource" / "knowledge"
QUESTIONS_DIR = PROJECT_ROOT / "resource" / "questions"

random.seed(42)


# ====================================================================
# 1. 数学（苏教版）1-6年级 知识图谱
# ====================================================================

MATH_GRADE1 = {
    "subject": "数学",
    "grade": "一年级",
    "version": "苏教版（盐城专用）",
    "nodes": [
        {"name": "数一数", "type": "chapter", "summary": "数出1-10个物体。"},
        {"name": "比一比", "type": "knowledge", "parent": "数一数", "summary": "比较多少、长短、高矮。", "exam_weight": 1},
        {"name": "1-5的认识", "type": "chapter", "summary": "认读写1-5。"},
        {"name": "1-5的读写", "type": "knowledge", "parent": "1-5的认识", "errors": ["书写不规范"], "exam_weight": 2},
        {"name": "5以内加减法", "type": "knowledge", "parent": "1-5的认识", "errors": ["计算粗心"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "认识0", "type": "knowledge", "parent": "1-5的认识", "exam_weight": 1},
        {"name": "认识6-10", "type": "chapter", "summary": "认读写6-10。"},
        {"name": "6-10的读写", "type": "knowledge", "parent": "认识6-10", "exam_weight": 2},
        {"name": "10以内加减法", "type": "knowledge", "parent": "认识6-10", "errors": ["进位出错"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "连加连减", "type": "knowledge", "parent": "认识6-10", "exam_weight": 2, "qcategory": "arithmetic"},
        {"name": "分类", "type": "chapter", "summary": "按不同标准分类。"},
        {"name": "按形状分类", "type": "knowledge", "parent": "分类", "exam_weight": 1},
        {"name": "按用途分类", "type": "knowledge", "parent": "分类", "exam_weight": 1},
        {"name": "认识物体", "type": "chapter", "summary": "认识长方体、正方体、圆柱、球。"},
        {"name": "立体图形辨认", "type": "knowledge", "parent": "认识物体", "errors": ["混淆形状"], "exam_weight": 2},
        {"name": "20以内加减法", "type": "chapter", "summary": "20以内的进位加法和退位减法。"},
        {"name": "9加几", "type": "knowledge", "parent": "20以内加减法", "errors": ["凑十法不熟练"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "8、7、6加几", "type": "knowledge", "parent": "20以内加减法", "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "20以内退位减法", "type": "knowledge", "parent": "20以内加减法", "errors": ["借位出错"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "认识钟表", "type": "chapter", "summary": "认识整时和半时。"},
        {"name": "整时认识", "type": "knowledge", "parent": "认识钟表", "exam_weight": 2},
        {"name": "半时认识", "type": "knowledge", "parent": "认识钟表", "exam_weight": 2},
    ]
}

MATH_GRADE2 = {
    "subject": "数学",
    "grade": "二年级",
    "version": "苏教版（盐城专用）",
    "nodes": [
        {"name": "100以内加减法", "type": "chapter", "summary": "两位数加减两位数。"},
        {"name": "两位数加两位数", "type": "knowledge", "parent": "100以内加减法", "errors": ["进位错误"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "两位数减两位数", "type": "knowledge", "parent": "100以内加减法", "errors": ["退位错误"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "连加连减混合", "type": "knowledge", "parent": "100以内加减法", "exam_weight": 2, "qcategory": "arithmetic"},
        {"name": "认识乘法", "type": "chapter", "summary": "乘法的初步认识。"},
        {"name": "乘法的含义", "type": "knowledge", "parent": "认识乘法", "exam_weight": 2},
        {"name": "2-6的乘法口诀", "type": "knowledge", "parent": "认识乘法", "errors": ["口诀记错"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "认识除法", "type": "chapter", "summary": "除法的初步认识。"},
        {"name": "除法的含义", "type": "knowledge", "parent": "认识除法", "exam_weight": 2},
        {"name": "用乘法口诀求商", "type": "knowledge", "parent": "认识除法", "errors": ["口诀混淆"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "位置与方向", "type": "chapter", "summary": "认识前后左右上下。"},
        {"name": "前后左右", "type": "knowledge", "parent": "位置与方向", "exam_weight": 1},
        {"name": "观察物体", "type": "knowledge", "parent": "位置与方向", "exam_weight": 2},
        {"name": "认识长度单位", "type": "chapter", "summary": "厘米和米。"},
        {"name": "厘米的认识", "type": "knowledge", "parent": "认识长度单位", "exam_weight": 2},
        {"name": "米的认识", "type": "knowledge", "parent": "认识长度单位", "exam_weight": 2},
        {"name": "7-9的乘法口诀", "type": "chapter", "summary": "7-9的乘法口诀和表内除法。"},
        {"name": "7的乘法口诀", "type": "knowledge", "parent": "7-9的乘法口诀", "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "8的乘法口诀", "type": "knowledge", "parent": "7-9的乘法口诀", "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "9的乘法口诀", "type": "knowledge", "parent": "7-9的乘法口诀", "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "时、分、秒", "type": "chapter", "summary": "认识时间单位。"},
        {"name": "认识时分", "type": "knowledge", "parent": "时、分、秒", "exam_weight": 2},
        {"name": "认识秒", "type": "knowledge", "parent": "时、分、秒", "exam_weight": 1},
    ]
}

MATH_GRADE3 = {
    "subject": "数学",
    "grade": "三年级",
    "version": "苏教版（盐城专用）",
    "nodes": [
        {"name": "两三位数乘一位数", "type": "chapter", "summary": "多位数乘一位数的乘法。"},
        {"name": "整十整百乘一位数", "type": "knowledge", "parent": "两三位数乘一位数", "exam_weight": 2, "qcategory": "arithmetic"},
        {"name": "两三位数乘一位数进位", "type": "knowledge", "parent": "两三位数乘一位数", "errors": ["进位遗忘"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "千克和克", "type": "chapter", "summary": "认识质量单位。"},
        {"name": "千克的认识", "type": "knowledge", "parent": "千克和克", "exam_weight": 2},
        {"name": "克的认识", "type": "knowledge", "parent": "千克和克", "exam_weight": 2},
        {"name": "长方形和正方形", "type": "chapter", "summary": "长方形和正方形的特征与周长。"},
        {"name": "长方形特征", "type": "knowledge", "parent": "长方形和正方形", "exam_weight": 2},
        {"name": "正方形特征", "type": "knowledge", "parent": "长方形和正方形", "exam_weight": 2},
        {"name": "长方形周长", "type": "knowledge", "parent": "长方形和正方形", "errors": ["公式记错"], "exam_weight": 3, "qcategory": "geometry"},
        {"name": "正方形周长", "type": "knowledge", "parent": "长方形和正方形", "errors": ["公式记错"], "exam_weight": 3, "qcategory": "geometry"},
        {"name": "两三位数除以一位数", "type": "chapter", "summary": "除法计算。"},
        {"name": "整十整百除以一位数", "type": "knowledge", "parent": "两三位数除以一位数", "exam_weight": 2, "qcategory": "arithmetic"},
        {"name": "两位数除以一位数", "type": "knowledge", "parent": "两三位数除以一位数", "errors": ["商中间有0漏写"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "分数的初步认识", "type": "chapter", "summary": "认识几分之一和几分之几。"},
        {"name": "几分之一", "type": "knowledge", "parent": "分数的初步认识", "errors": ["分子分母混淆"], "exam_weight": 2},
        {"name": "几分之几", "type": "knowledge", "parent": "分数的初步认识", "exam_weight": 2},
        {"name": "年月日", "type": "chapter", "summary": "认识年月日。"},
        {"name": "年月日的关系", "type": "knowledge", "parent": "年月日", "exam_weight": 2},
        {"name": "平年和闰年", "type": "knowledge", "parent": "年月日", "errors": ["闰年判断错误"], "exam_weight": 3},
    ]
}

MATH_GRADE4 = {
    "subject": "数学",
    "grade": "四年级",
    "version": "苏教版（盐城专用）",
    "nodes": [
        {"name": "升和毫升", "type": "chapter", "summary": "认识容量单位。"},
        {"name": "升的认识", "type": "knowledge", "parent": "升和毫升", "exam_weight": 2},
        {"name": "毫升的认识", "type": "knowledge", "parent": "升和毫升", "exam_weight": 2},
        {"name": "两三位数除以两位数", "type": "chapter", "summary": "除数是两位数的除法。"},
        {"name": "除数是整十数", "type": "knowledge", "parent": "两三位数除以两位数", "exam_weight": 2, "qcategory": "arithmetic"},
        {"name": "四舍五入试商", "type": "knowledge", "parent": "两三位数除以两位数", "errors": ["试商偏大偏小"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "观察物体", "type": "chapter", "summary": "从不同方向观察物体。"},
        {"name": "三视图辨认", "type": "knowledge", "parent": "观察物体", "exam_weight": 2},
        {"name": "统计表和条形统计图", "type": "chapter", "summary": "数据收集与整理。"},
        {"name": "数据收集", "type": "knowledge", "parent": "统计表和条形统计图", "exam_weight": 1},
        {"name": "条形统计图", "type": "knowledge", "parent": "统计表和条形统计图", "exam_weight": 2},
        {"name": "整数四则混合运算", "type": "chapter", "summary": "不含括号和含括号的混合运算。"},
        {"name": "不含括号混合运算", "type": "knowledge", "parent": "整数四则混合运算", "errors": ["运算顺序错误"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "含括号混合运算", "type": "knowledge", "parent": "整数四则混合运算", "errors": ["去括号符号错"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "垂线与平行线", "type": "chapter", "summary": "认识垂直与平行。"},
        {"name": "角的度量", "type": "knowledge", "parent": "垂线与平行线", "errors": ["量角器读错"], "exam_weight": 3, "qcategory": "geometry"},
        {"name": "垂直", "type": "knowledge", "parent": "垂线与平行线", "exam_weight": 2},
        {"name": "平行", "type": "knowledge", "parent": "垂线与平行线", "exam_weight": 2},
        {"name": "小数的意义和性质", "type": "chapter", "summary": "小数的初步认识。"},
        {"name": "小数的意义", "type": "knowledge", "parent": "小数的意义和性质", "errors": ["小数位值混淆"], "exam_weight": 3},
        {"name": "小数的大小比较", "type": "knowledge", "parent": "小数的意义和性质", "exam_weight": 2},
    ]
}

MATH_GRADE5 = {
    "subject": "数学",
    "grade": "五年级",
    "version": "苏教版（盐城专用）",
    "nodes": [
        {"name": "负数的初步认识", "type": "chapter", "summary": "认识正负数。"},
        {"name": "正负数的含义", "type": "knowledge", "parent": "负数的初步认识", "exam_weight": 2},
        {"name": "数轴上的正负数", "type": "knowledge", "parent": "负数的初步认识", "exam_weight": 2},
        {"name": "小数的加减法", "type": "chapter", "summary": "小数加减计算。"},
        {"name": "小数加法", "type": "knowledge", "parent": "小数的加减法", "errors": ["小数点对齐错误"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "小数减法", "type": "knowledge", "parent": "小数的加减法", "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "小数的乘除法", "type": "chapter", "summary": "小数乘除计算。"},
        {"name": "小数乘法", "type": "knowledge", "parent": "小数的乘除法", "errors": ["积的小数位数错"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "小数除法", "type": "knowledge", "parent": "小数的乘除法", "errors": ["商的小数点漏点"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "多边形面积", "type": "chapter", "summary": "平行四边形、三角形、梯形面积。"},
        {"name": "平行四边形面积", "type": "knowledge", "parent": "多边形面积", "formula": "S=ah", "exam_weight": 3, "qcategory": "geometry"},
        {"name": "三角形面积", "type": "knowledge", "parent": "多边形面积", "formula": "S=ah÷2", "errors": ["忘记除以2"], "exam_weight": 3, "qcategory": "geometry"},
        {"name": "梯形面积", "type": "knowledge", "parent": "多边形面积", "formula": "S=(a+b)h÷2", "errors": ["公式记错"], "exam_weight": 3, "qcategory": "geometry"},
        {"name": "小数乘法和除法", "type": "chapter", "summary": "小数乘除法综合。"},
        {"name": "近似数", "type": "knowledge", "parent": "小数乘法和除法", "exam_weight": 2},
        {"name": "循环小数", "type": "knowledge", "parent": "小数乘法和除法", "exam_weight": 2},
        {"name": "统计与可能性", "type": "chapter", "summary": "平均数与可能性。"},
        {"name": "平均数", "type": "knowledge", "parent": "统计与可能性", "formula": "总数÷份数", "exam_weight": 2, "qcategory": "statistics"},
        {"name": "可能性大小", "type": "knowledge", "parent": "统计与可能性", "exam_weight": 2},
        {"name": "简易方程", "type": "chapter", "summary": "用字母表示数和方程。"},
        {"name": "用字母表示数", "type": "knowledge", "parent": "简易方程", "exam_weight": 2},
        {"name": "解方程", "type": "knowledge", "parent": "简易方程", "errors": ["等式性质运用错"], "exam_weight": 3, "qcategory": "arithmetic"},
    ]
}

MATH_GRADE6 = {
    "subject": "数学",
    "grade": "六年级",
    "version": "苏教版（盐城专用）",
    "nodes": [
        {"name": "长方体和正方体", "type": "chapter", "summary": "立体图形的特征和体积。"},
        {"name": "长方体的认识", "type": "knowledge", "parent": "长方体和正方体", "exam_weight": 2},
        {"name": "正方体的认识", "type": "knowledge", "parent": "长方体和正方体", "exam_weight": 2},
        {"name": "表面积计算", "type": "knowledge", "parent": "长方体和正方体", "formula": "S=2(ab+ah+bh)", "exam_weight": 3, "qcategory": "geometry"},
        {"name": "体积计算", "type": "knowledge", "parent": "长方体和正方体", "formula": "V=abc, V=a³", "errors": ["单位混淆"], "exam_weight": 3, "qcategory": "geometry"},
        {"name": "分数乘法", "type": "chapter", "summary": "分数乘整数和分数。"},
        {"name": "分数乘整数", "type": "knowledge", "parent": "分数乘法", "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "分数乘分数", "type": "knowledge", "parent": "分数乘法", "errors": ["约分不及时"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "分数除法", "type": "chapter", "summary": "分数除法的意义和计算。"},
        {"name": "分数除以整数", "type": "knowledge", "parent": "分数除法", "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "一个数除以分数", "type": "knowledge", "parent": "分数除法", "errors": ["倒数概念混淆"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "比", "type": "chapter", "summary": "比的意义和性质。"},
        {"name": "比的意义", "type": "knowledge", "parent": "比", "exam_weight": 2},
        {"name": "比的基本性质", "type": "knowledge", "parent": "比", "exam_weight": 2},
        {"name": "按比例分配", "type": "knowledge", "parent": "比", "errors": ["比例分配计算错"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "百分数", "type": "chapter", "summary": "百分数的意义和应用。"},
        {"name": "百分数的意义", "type": "knowledge", "parent": "百分数", "exam_weight": 2},
        {"name": "百分数与小数的互化", "type": "knowledge", "parent": "百分数", "exam_weight": 2},
        {"name": "百分数应用题", "type": "knowledge", "parent": "百分数", "errors": ["单位1找错"], "exam_weight": 3, "qcategory": "arithmetic"},
        {"name": "圆", "type": "chapter", "summary": "圆的周长和面积。"},
        {"name": "圆的认识", "type": "knowledge", "parent": "圆", "exam_weight": 2},
        {"name": "圆的周长", "type": "knowledge", "parent": "圆", "formula": "C=πd=2πr", "errors": ["π取值出错"], "exam_weight": 3, "qcategory": "geometry"},
        {"name": "圆的面积", "type": "knowledge", "parent": "圆", "formula": "S=πr²", "errors": ["半径平方漏算"], "exam_weight": 3, "qcategory": "geometry"},
    ]
}

# ====================================================================
# 2. 语文（部编版）1-6年级 知识图谱
# ====================================================================

CHINESE_GRADE1 = {
    "subject": "语文",
    "grade": "一年级",
    "version": "部编版（盐城专用）",
    "nodes": [
        {"name": "汉语拼音", "type": "chapter", "summary": "声母、韵母、整体认读音节。"},
        {"name": "单韵母", "type": "knowledge", "parent": "汉语拼音", "errors": ["口型不到位"], "exam_weight": 3},
        {"name": "声母", "type": "knowledge", "parent": "汉语拼音", "exam_weight": 3},
        {"name": "复韵母", "type": "knowledge", "parent": "汉语拼音", "errors": ["前后鼻音不分"], "exam_weight": 3},
        {"name": "整体认读音节", "type": "knowledge", "parent": "汉语拼音", "exam_weight": 2},
        {"name": "识字", "type": "chapter", "summary": "常用汉字认读与书写。"},
        {"name": "基本笔画", "type": "knowledge", "parent": "识字", "errors": ["笔画顺序错"], "exam_weight": 3},
        {"name": "常用偏旁", "type": "knowledge", "parent": "识字", "exam_weight": 2},
        {"name": "汉字结构", "type": "knowledge", "parent": "识字", "exam_weight": 2},
        {"name": "阅读", "type": "chapter", "summary": "儿歌与短文阅读理解。"},
        {"name": "儿歌朗读", "type": "knowledge", "parent": "阅读", "exam_weight": 2},
        {"name": "短文理解", "type": "knowledge", "parent": "阅读", "exam_weight": 2},
        {"name": "写话", "type": "chapter", "summary": "看图写话。"},
        {"name": "看图写一句话", "type": "knowledge", "parent": "写话", "exam_weight": 2},
    ]
}

CHINESE_GRADE2 = {
    "subject": "语文",
    "grade": "二年级",
    "version": "部编版（盐城专用）",
    "nodes": [
        {"name": "识字与写字", "type": "chapter", "summary": "继续识字，积累词汇。"},
        {"name": "形声字", "type": "knowledge", "parent": "识字与写字", "exam_weight": 2},
        {"name": "多音字", "type": "knowledge", "parent": "识字与写字", "errors": ["读音混淆"], "exam_weight": 3},
        {"name": "近义词反义词", "type": "knowledge", "parent": "识字与写字", "exam_weight": 2},
        {"name": "词语积累", "type": "chapter", "summary": "成语、短语。"},
        {"name": "四字成语", "type": "knowledge", "parent": "词语积累", "exam_weight": 2},
        {"name": "量词搭配", "type": "knowledge", "parent": "词语积累", "errors": ["量词使用不当"], "exam_weight": 2},
        {"name": "阅读与理解", "type": "chapter", "summary": "初步阅读理解。"},
        {"name": "自然段", "type": "knowledge", "parent": "阅读与理解", "exam_weight": 2},
        {"name": "提取信息", "type": "knowledge", "parent": "阅读与理解", "exam_weight": 2},
        {"name": "口语交际", "type": "chapter", "summary": "学会表达与交流。"},
        {"name": "自我介绍", "type": "knowledge", "parent": "口语交际", "exam_weight": 1},
        {"name": "看图讲故事", "type": "knowledge", "parent": "口语交际", "exam_weight": 2},
        {"name": "写话", "type": "chapter", "summary": "写一段话。"},
        {"name": "日记格式", "type": "knowledge", "parent": "写话", "exam_weight": 2},
        {"name": "看图写一段话", "type": "knowledge", "parent": "写话", "exam_weight": 3},
    ]
}

CHINESE_GRADE3 = {
    "subject": "语文",
    "grade": "三年级",
    "version": "部编版（盐城专用）",
    "nodes": [
        {"name": "识字与写字", "type": "chapter", "summary": "认读2500个常用字。"},
        {"name": "生字认读", "type": "knowledge", "parent": "识字与写字", "exam_weight": 2},
        {"name": "形近字辨析", "type": "knowledge", "parent": "识字与写字", "errors": ["字形混淆"], "exam_weight": 3},
        {"name": "查字典", "type": "knowledge", "parent": "识字与写字", "exam_weight": 2},
        {"name": "词语理解与运用", "type": "chapter", "summary": "理解词义，积累词语。"},
        {"name": "词语解释", "type": "knowledge", "parent": "词语理解与运用", "exam_weight": 2},
        {"name": "成语故事", "type": "knowledge", "parent": "词语理解与运用", "exam_weight": 2},
        {"name": "关联词语", "type": "knowledge", "parent": "词语理解与运用", "errors": ["关联词搭配错"], "exam_weight": 3},
        {"name": "阅读", "type": "chapter", "summary": "段落理解与概括。"},
        {"name": "概括段意", "type": "knowledge", "parent": "阅读", "exam_weight": 3},
        {"name": "理解关键句", "type": "knowledge", "parent": "阅读", "exam_weight": 2},
        {"name": "古诗文", "type": "chapter", "summary": "诵读浅近古诗。"},
        {"name": "古诗背诵", "type": "knowledge", "parent": "古诗文", "exam_weight": 3},
        {"name": "古诗理解", "type": "knowledge", "parent": "古诗文", "exam_weight": 2},
        {"name": "习作", "type": "chapter", "summary": "写一段通顺的话。"},
        {"name": "观察日记", "type": "knowledge", "parent": "习作", "exam_weight": 2},
        {"name": "编写童话", "type": "knowledge", "parent": "习作", "exam_weight": 2},
    ]
}

CHINESE_GRADE4 = {
    "subject": "语文",
    "grade": "四年级",
    "version": "部编版（盐城专用）",
    "nodes": [
        {"name": "识字与写字", "type": "chapter", "summary": "独立识字能力。"},
        {"name": "同音字辨析", "type": "knowledge", "parent": "识字与写字", "errors": ["同音混淆"], "exam_weight": 2},
        {"name": "多义字理解", "type": "knowledge", "parent": "识字与写字", "exam_weight": 2},
        {"name": "词语积累", "type": "chapter", "summary": "丰富词汇。"},
        {"name": "歇后语", "type": "knowledge", "parent": "词语积累", "exam_weight": 1},
        {"name": "名言警句", "type": "knowledge", "parent": "词语积累", "exam_weight": 2},
        {"name": "阅读", "type": "chapter", "summary": "篇章阅读。"},
        {"name": "划分段落", "type": "knowledge", "parent": "阅读", "exam_weight": 2},
        {"name": "归纳主要内容", "type": "knowledge", "parent": "阅读", "errors": ["概括不完整"], "exam_weight": 3},
        {"name": "体会思想感情", "type": "knowledge", "parent": "阅读", "exam_weight": 3},
        {"name": "古诗文", "type": "chapter", "summary": "诵读古诗文。"},
        {"name": "古诗默写", "type": "knowledge", "parent": "古诗文", "exam_weight": 3},
        {"name": "小古文阅读", "type": "knowledge", "parent": "古诗文", "exam_weight": 2},
        {"name": "习作", "type": "chapter", "summary": "写记叙文。"},
        {"name": "写人作文", "type": "knowledge", "parent": "习作", "exam_weight": 3},
        {"name": "记事作文", "type": "knowledge", "parent": "习作", "exam_weight": 3},
    ]
}

CHINESE_GRADE5 = {
    "subject": "语文",
    "grade": "五年级",
    "version": "部编版（盐城专用）",
    "nodes": [
        {"name": "识字与写字", "type": "chapter", "summary": "自主识字的综合能力。"},
        {"name": "字义辨析", "type": "knowledge", "parent": "识字与写字", "exam_weight": 2},
        {"name": "词语辨析", "type": "chapter", "summary": "近义词辨析和词语的感情色彩。"},
        {"name": "近义词辨析", "type": "knowledge", "parent": "词语辨析", "exam_weight": 2},
        {"name": "褒义词贬义词", "type": "knowledge", "parent": "词语辨析", "exam_weight": 2},
        {"name": "阅读", "type": "chapter", "summary": "深度阅读理解。"},
        {"name": "说明文阅读", "type": "knowledge", "parent": "阅读", "exam_weight": 3},
        {"name": "叙事文阅读", "type": "knowledge", "parent": "阅读", "exam_weight": 3},
        {"name": "体会表达方法", "type": "knowledge", "parent": "阅读", "errors": ["修辞辨认不清"], "exam_weight": 3},
        {"name": "古诗文", "type": "chapter", "summary": "积累古诗文。"},
        {"name": "古诗鉴赏", "type": "knowledge", "parent": "古诗文", "exam_weight": 2},
        {"name": "文言文启蒙", "type": "knowledge", "parent": "古诗文", "exam_weight": 2},
        {"name": "习作", "type": "chapter", "summary": "写事写景作文。"},
        {"name": "写景作文", "type": "knowledge", "parent": "习作", "exam_weight": 3},
        {"name": "读后感", "type": "knowledge", "parent": "习作", "exam_weight": 2},
    ]
}

CHINESE_GRADE6 = {
    "subject": "语文",
    "grade": "六年级",
    "version": "部编版（盐城专用）",
    "nodes": [
        {"name": "汉字与词语", "type": "chapter", "summary": "综合运用。"},
        {"name": "成语运用", "type": "knowledge", "parent": "汉字与词语", "exam_weight": 2},
        {"name": "修辞手法", "type": "knowledge", "parent": "汉字与词语", "errors": ["修辞类型混淆"], "exam_weight": 3},
        {"name": "句子", "type": "chapter", "summary": "句式变换与修改。"},
        {"name": "句式变换", "type": "knowledge", "parent": "句子", "exam_weight": 2},
        {"name": "修改病句", "type": "knowledge", "parent": "句子", "errors": ["病句类型分辨不清"], "exam_weight": 3},
        {"name": "阅读", "type": "chapter", "summary": "综合阅读能力。"},
        {"name": "文学类阅读", "type": "knowledge", "parent": "阅读", "exam_weight": 3},
        {"name": "非连续性文本阅读", "type": "knowledge", "parent": "阅读", "exam_weight": 3},
        {"name": "古诗文", "type": "chapter", "summary": "古诗文综合。"},
        {"name": "古诗积累", "type": "knowledge", "parent": "古诗文", "exam_weight": 3},
        {"name": "文言文阅读", "type": "knowledge", "parent": "古诗文", "exam_weight": 3},
        {"name": "习作", "type": "chapter", "summary": "综合写作。"},
        {"name": "命题作文", "type": "knowledge", "parent": "习作", "exam_weight": 3},
        {"name": "材料作文", "type": "knowledge", "parent": "习作", "exam_weight": 3},
    ]
}

# ====================================================================
# 3. 英语（译林版）3-6年级 知识图谱
# ====================================================================

ENGLISH_GRADE3 = {
    "subject": "英语",
    "grade": "三年级",
    "version": "译林版（盐城专用）",
    "nodes": [
        {"name": "字母与发音", "type": "chapter", "summary": "26个字母及基本发音。"},
        {"name": "字母认读", "type": "knowledge", "parent": "字母与发音", "errors": ["字母混淆"], "exam_weight": 3},
        {"name": "字母书写", "type": "knowledge", "parent": "字母与发音", "exam_weight": 2},
        {"name": "基本问候", "type": "chapter", "summary": "日常问候语。"},
        {"name": "打招呼", "type": "knowledge", "parent": "基本问候", "exam_weight": 3},
        {"name": "自我介绍", "type": "knowledge", "parent": "基本问候", "exam_weight": 2},
        {"name": "动物与颜色", "type": "chapter", "summary": "常见动物和颜色词汇。"},
        {"name": "动物词汇", "type": "knowledge", "parent": "动物与颜色", "exam_weight": 2},
        {"name": "颜色词汇", "type": "knowledge", "parent": "动物与颜色", "exam_weight": 2},
        {"name": "数字与文具", "type": "chapter", "summary": "1-10数字和学习用品。"},
        {"name": "数字1-10", "type": "knowledge", "parent": "数字与文具", "exam_weight": 2},
        {"name": "文具词汇", "type": "knowledge", "parent": "数字与文具", "exam_weight": 2},
        {"name": "家庭人物", "type": "chapter", "summary": "家庭成员称谓。"},
        {"name": "家庭词汇", "type": "knowledge", "parent": "家庭人物", "exam_weight": 2},
        {"name": "简单句型", "type": "knowledge", "parent": "家庭人物", "exam_weight": 3},
    ]
}

ENGLISH_GRADE4 = {
    "subject": "英语",
    "grade": "四年级",
    "version": "译林版（盐城专用）",
    "nodes": [
        {"name": "词汇扩展", "type": "chapter", "summary": "食物、饮料、服装等词汇。"},
        {"name": "食物饮料词汇", "type": "knowledge", "parent": "词汇扩展", "exam_weight": 2},
        {"name": "服装词汇", "type": "knowledge", "parent": "词汇扩展", "exam_weight": 2},
        {"name": "there be句型", "type": "chapter", "summary": "There is/are 句型。"},
        {"name": "There is用法", "type": "knowledge", "parent": "there be句型", "errors": ["主谓一致错"], "exam_weight": 3},
        {"name": "There are用法", "type": "knowledge", "parent": "there be句型", "exam_weight": 3},
        {"name": "现在进行时", "type": "chapter", "summary": "be doing 结构。"},
        {"name": "现在分词变化", "type": "knowledge", "parent": "现在进行时", "errors": ["ing添加错"], "exam_weight": 3},
        {"name": "现在进行时句型", "type": "knowledge", "parent": "现在进行时", "exam_weight": 3},
        {"name": "天气与季节", "type": "chapter", "summary": "天气和四季表达。"},
        {"name": "天气词汇", "type": "knowledge", "parent": "天气与季节", "exam_weight": 2},
        {"name": "季节表达", "type": "knowledge", "parent": "天气与季节", "exam_weight": 2},
        {"name": "问路与指路", "type": "chapter", "summary": "方位介词和问路句型。"},
        {"name": "方位介词", "type": "knowledge", "parent": "问路与指路", "exam_weight": 2},
        {"name": "问路句型", "type": "knowledge", "parent": "问路与指路", "exam_weight": 2},
    ]
}

ENGLISH_GRADE5 = {
    "subject": "英语",
    "grade": "五年级",
    "version": "译林版（盐城专用）",
    "nodes": [
        {"name": "一般现在时", "type": "chapter", "summary": "一般现在时的肯定否定疑问。"},
        {"name": "动词三单形式", "type": "knowledge", "parent": "一般现在时", "errors": ["三单变化错"], "exam_weight": 3},
        {"name": "一般疑问句", "type": "knowledge", "parent": "一般现在时", "exam_weight": 3},
        {"name": "否定句", "type": "knowledge", "parent": "一般现在时", "exam_weight": 3},
        {"name": "能力与爱好", "type": "chapter", "summary": "can的用法和爱好表达。"},
        {"name": "can句型", "type": "knowledge", "parent": "能力与爱好", "exam_weight": 2},
        {"name": "爱好词汇", "type": "knowledge", "parent": "能力与爱好", "exam_weight": 2},
        {"name": "日期与节日", "type": "chapter", "summary": "月份、日期和节日表达。"},
        {"name": "月份词汇", "type": "knowledge", "parent": "日期与节日", "exam_weight": 2},
        {"name": "序数词", "type": "knowledge", "parent": "日期与节日", "errors": ["序数词变形错"], "exam_weight": 3},
        {"name": "节日文化", "type": "knowledge", "parent": "日期与节日", "exam_weight": 2},
        {"name": "现在进行时深化", "type": "chapter", "summary": "现在进行时的综合运用。"},
        {"name": "现在进行时特殊疑问", "type": "knowledge", "parent": "现在进行时深化", "exam_weight": 2},
        {"name": "阅读与写作", "type": "chapter", "summary": "简单阅读理解和写作。"},
        {"name": "短文阅读", "type": "knowledge", "parent": "阅读与写作", "exam_weight": 2},
        {"name": "简单写作", "type": "knowledge", "parent": "阅读与写作", "exam_weight": 2},
    ]
}

ENGLISH_GRADE6 = {
    "subject": "英语",
    "grade": "六年级",
    "version": "译林版（盐城专用）",
    "nodes": [
        {"name": "一般过去时", "type": "chapter", "summary": "过去式的构成和运用。"},
        {"name": "动词过去式变化", "type": "knowledge", "parent": "一般过去时", "errors": ["不规则变化记错"], "exam_weight": 3},
        {"name": "一般过去时句型", "type": "knowledge", "parent": "一般过去时", "exam_weight": 3},
        {"name": "形容词比较级", "type": "chapter", "summary": "比较级的变化和运用。"},
        {"name": "比较级变化规则", "type": "knowledge", "parent": "形容词比较级", "errors": ["比较级变形错"], "exam_weight": 3},
        {"name": "比较级句型", "type": "knowledge", "parent": "形容词比较级", "exam_weight": 3},
        {"name": "将来时", "type": "chapter", "summary": "be going to / will。"},
        {"name": "be going to句型", "type": "knowledge", "parent": "将来时", "exam_weight": 3},
        {"name": "will句型", "type": "knowledge", "parent": "将来时", "exam_weight": 2},
        {"name": "职业与梦想", "type": "chapter", "summary": "职业词汇和未来表达。"},
        {"name": "职业词汇", "type": "knowledge", "parent": "职业与梦想", "exam_weight": 2},
        {"name": "梦想表达", "type": "knowledge", "parent": "职业与梦想", "exam_weight": 2},
        {"name": "现在完成时", "type": "chapter", "summary": "现在完成时的初步认识。"},
        {"name": "have/has+过去分词", "type": "knowledge", "parent": "现在完成时", "exam_weight": 2},
        {"name": "综合性阅读与写作", "type": "chapter", "summary": "综合运用。"},
        {"name": "综合阅读理解", "type": "knowledge", "parent": "综合性阅读与写作", "exam_weight": 3},
        {"name": "小作文写作", "type": "knowledge", "parent": "综合性阅读与写作", "exam_weight": 3},
    ]
}

# ====================================================================
# 4. 科学（苏教版）1-6年级 知识图谱
# ====================================================================

SCIENCE_GRADE1 = {
    "subject": "科学",
    "grade": "一年级",
    "version": "苏教版（盐城专用）",
    "nodes": [
        {"name": "我们周围的物体", "type": "chapter", "summary": "认识常见物体的特征。"},
        {"name": "物体的特征", "type": "knowledge", "parent": "我们周围的物体", "exam_weight": 2},
        {"name": "轻重比较", "type": "knowledge", "parent": "我们周围的物体", "exam_weight": 2},
        {"name": "植物", "type": "chapter", "summary": "认识常见植物。"},
        {"name": "植物的结构", "type": "knowledge", "parent": "植物", "exam_weight": 2},
        {"name": "常见植物辨认", "type": "knowledge", "parent": "植物", "exam_weight": 2},
        {"name": "动物", "type": "chapter", "summary": "认识常见动物。"},
        {"name": "常见动物辨认", "type": "knowledge", "parent": "动物", "exam_weight": 2},
        {"name": "动物的特征", "type": "knowledge", "parent": "动物", "exam_weight": 2},
    ]
}

SCIENCE_GRADE2 = {
    "subject": "科学",
    "grade": "二年级",
    "version": "苏教版（盐城专用）",
    "nodes": [
        {"name": "磁铁", "type": "chapter", "summary": "磁铁的性质。"},
        {"name": "磁铁的两极", "type": "knowledge", "parent": "磁铁", "errors": ["同极相斥异极相吸记反"], "exam_weight": 3},
        {"name": "磁铁的应用", "type": "knowledge", "parent": "磁铁", "exam_weight": 2},
        {"name": "天气", "type": "chapter", "summary": "认识天气现象。"},
        {"name": "天气类型", "type": "knowledge", "parent": "天气", "exam_weight": 2},
        {"name": "温度计使用", "type": "knowledge", "parent": "天气", "exam_weight": 2},
        {"name": "影子", "type": "chapter", "summary": "光和影的关系。"},
        {"name": "影子的形成", "type": "knowledge", "parent": "影子", "exam_weight": 2},
        {"name": "影子的变化", "type": "knowledge", "parent": "影子", "exam_weight": 2},
    ]
}

SCIENCE_GRADE3 = {
    "subject": "科学",
    "grade": "三年级",
    "version": "苏教版（盐城专用）",
    "nodes": [
        {"name": "植物的生长", "type": "chapter", "summary": "种子发芽和植物生长。"},
        {"name": "种子的结构", "type": "knowledge", "parent": "植物的生长", "exam_weight": 2},
        {"name": "种子发芽条件", "type": "knowledge", "parent": "植物的生长", "errors": ["遗漏必要条件"], "exam_weight": 3},
        {"name": "植物的生长过程", "type": "knowledge", "parent": "植物的生长", "exam_weight": 2},
        {"name": "动物的生命周期", "type": "chapter", "summary": "昆虫和动物的生命周期。"},
        {"name": "昆虫生命周期", "type": "knowledge", "parent": "动物的生命周期", "exam_weight": 2},
        {"name": "动物的繁殖方式", "type": "knowledge", "parent": "动物的生命周期", "exam_weight": 2},
        {"name": "水的三态变化", "type": "chapter", "summary": "水的固态液态气态。"},
        {"name": "水的三态", "type": "knowledge", "parent": "水的三态变化", "errors": ["三态变化条件混淆"], "exam_weight": 3},
        {"name": "蒸发与凝结", "type": "knowledge", "parent": "水的三态变化", "exam_weight": 3},
    ]
}

SCIENCE_GRADE4 = {
    "subject": "科学",
    "grade": "四年级",
    "version": "苏教版（盐城专用）",
    "nodes": [
        {"name": "电路", "type": "chapter", "summary": "简单电路的认识。"},
        {"name": "电路组成", "type": "knowledge", "parent": "电路", "exam_weight": 2},
        {"name": "串联与并联", "type": "knowledge", "parent": "电路", "errors": ["串并联混淆"], "exam_weight": 3},
        {"name": "导体与绝缘体", "type": "knowledge", "parent": "电路", "exam_weight": 2},
        {"name": "岩石与矿物", "type": "chapter", "summary": "认识常见岩石。"},
        {"name": "岩石特征", "type": "knowledge", "parent": "岩石与矿物", "exam_weight": 2},
        {"name": "矿物硬度", "type": "knowledge", "parent": "岩石与矿物", "exam_weight": 2},
        {"name": "运动和力", "type": "chapter", "summary": "力与运动的关系。"},
        {"name": "推力和拉力", "type": "knowledge", "parent": "运动和力", "exam_weight": 2},
        {"name": "摩擦力", "type": "knowledge", "parent": "运动和力", "exam_weight": 2},
        {"name": "重力", "type": "knowledge", "parent": "运动和力", "exam_weight": 2},
    ]
}

SCIENCE_GRADE5 = {
    "subject": "科学",
    "grade": "五年级",
    "version": "苏教版（盐城专用）",
    "nodes": [
        {"name": "光现象", "type": "chapter", "summary": "光的传播与反射。"},
        {"name": "光的直线传播", "type": "knowledge", "parent": "光现象", "exam_weight": 2},
        {"name": "光的反射", "type": "knowledge", "parent": "光现象", "errors": ["光的折射混淆"], "exam_weight": 3},
        {"name": "声音的产生与传播", "type": "chapter", "summary": "声音的产生和传播。"},
        {"name": "声音的产生", "type": "knowledge", "parent": "声音的产生与传播", "exam_weight": 2},
        {"name": "声音的传播介质", "type": "knowledge", "parent": "声音的产生与传播", "exam_weight": 2},
        {"name": "声音的高低强弱", "type": "knowledge", "parent": "声音的产生与传播", "exam_weight": 2},
        {"name": "地球运动", "type": "chapter", "summary": "地球的自转与公转。"},
        {"name": "昼夜交替", "type": "knowledge", "parent": "地球运动", "errors": ["自转公转混淆"], "exam_weight": 3},
        {"name": "四季变化", "type": "knowledge", "parent": "地球运动", "exam_weight": 2},
        {"name": "生态与环境", "type": "chapter", "summary": "生态系统的认识。"},
        {"name": "食物链", "type": "knowledge", "parent": "生态与环境", "exam_weight": 2},
        {"name": "生态平衡", "type": "knowledge", "parent": "生态与环境", "exam_weight": 2},
    ]
}

SCIENCE_GRADE6 = {
    "subject": "科学",
    "grade": "六年级",
    "version": "苏教版（盐城专用）",
    "nodes": [
        {"name": "微小世界", "type": "chapter", "summary": "显微镜下的世界。"},
        {"name": "细胞结构", "type": "knowledge", "parent": "微小世界", "exam_weight": 2},
        {"name": "微生物", "type": "knowledge", "parent": "微小世界", "exam_weight": 2},
        {"name": "人体系统", "type": "chapter", "summary": "人体主要器官和系统。"},
        {"name": "消化系统", "type": "knowledge", "parent": "人体系统", "exam_weight": 2},
        {"name": "呼吸系统", "type": "knowledge", "parent": "人体系统", "exam_weight": 2},
        {"name": "血液循环系统", "type": "knowledge", "parent": "人体系统", "exam_weight": 2},
        {"name": "遗传与变异", "type": "chapter", "summary": "生物的遗传和变异。"},
        {"name": "遗传现象", "type": "knowledge", "parent": "遗传与变异", "exam_weight": 2},
        {"name": "变异现象", "type": "knowledge", "parent": "遗传与变异", "exam_weight": 2},
        {"name": "宇宙与航天", "type": "chapter", "summary": "太阳系和航天。"},
        {"name": "太阳系组成", "type": "knowledge", "parent": "宇宙与航天", "exam_weight": 2},
        {"name": "探索宇宙", "type": "knowledge", "parent": "宇宙与航天", "exam_weight": 1},
    ]
}


# ====================================================================
# 知识图谱数据字典
# ====================================================================

KNOWLEDGE_MAP = {
    "数学": {1: MATH_GRADE1, 2: MATH_GRADE2, 3: MATH_GRADE3, 4: MATH_GRADE4, 5: MATH_GRADE5, 6: MATH_GRADE6},
    "语文": {1: CHINESE_GRADE1, 2: CHINESE_GRADE2, 3: CHINESE_GRADE3, 4: CHINESE_GRADE4, 5: CHINESE_GRADE5, 6: CHINESE_GRADE6},
    "英语": {3: ENGLISH_GRADE3, 4: ENGLISH_GRADE4, 5: ENGLISH_GRADE5, 6: ENGLISH_GRADE6},
    "科学": {1: SCIENCE_GRADE1, 2: SCIENCE_GRADE2, 3: SCIENCE_GRADE3, 4: SCIENCE_GRADE4, 5: SCIENCE_GRADE5, 6: SCIENCE_GRADE6},
}

# ====================================================================
# 题目生成器
# ====================================================================

def _make_opts(ans, wrongs_pool):
    """标准化生成选项。"""
    wrongs = [str(w) for w in wrongs_pool if w != ans and str(w).strip()][:3]
    while len(wrongs) < 3:
        wrongs.append(str(ans + len(wrongs) + 1))
    all_c = [str(ans)] + wrongs
    random.shuffle(all_c)
    opts = []
    for i, c in enumerate(all_c):
        opts.append({"label": chr(65+i), "text": c, "correct": c == str(ans)})
    return opts


def _make_q(id_str, g, parent, name, diff, errors, content, answer, analysis, opts, subtype=""):
    """标准化构造题目对象。"""
    return {
        "id": id_str,
        "type": "选择题",
        "subject": "数学",
        "grade": g,
        "chapter": parent,
        "knowledge": [name],
        "difficulty": diff,
        "exam_weight": diff,
        "subtype": subtype or "arithmetic",
        "error_tags": errors or [],
        "content": content,
        "answer": answer,
        "analysis": analysis,
        "options": opts,
    }


def generate_math_questions(subject: str, grade: int, nodes: list) -> list:
    """为数学学科生成题目（每个知识点至少1题，确保全面覆盖）。"""
    questions = []
    g = f"{['一','二','三','四','五','六'][grade-1]}年级"
    grade_num = grade
    question_id = [1]  # 用列表包裹以实现闭包内修改
    
    def next_id():
        question_id[0] += 1
        return question_id[0] - 1
    
    def gen_arithmetic_q(name, parent, errors, diff, qcat):
        """生成计算题。"""
        qid = next_id()
        if grade_num <= 2:
            # 低年级：20以内加减法
            if "减法" in name or "退位" in name:
                a = random.randint(5, 18)
                b = random.randint(1, a-1)
                op, ans = "-", a - b
            elif "连加" in name or "连" in name:
                a, b, c = random.randint(1, 5), random.randint(1, 5), random.randint(1, 5)
                ans = a + b + c
                content = f"计算：{a} + {b} + {c} = （  ）"
                analysis = f"{a} + {b} + {c} = {ans}"
                opts = _make_opts(ans, [ans+1, ans-1, ans+2, ans+3])
                questions.append(_make_q(f"数学{g}_{parent}_calc_{qid}", g, parent, name, diff, errors, content, next(o["label"] for o in opts if o["correct"]), analysis, opts))
                return
            else:
                if grade_num == 1:
                    a, b = random.randint(1, 9), random.randint(1, 9)
                else:
                    a, b = random.randint(5, 50), random.randint(5, 50)
                op, ans = "+", a + b
            content = f"计算：{a} {op} {b} = （  ）"
            analysis = f"{a} {op} {b} = {ans}。"
        elif grade_num == 3:
            # 三年级：乘除为主
            if "乘" in name:
                a, b = random.randint(10, 99), random.randint(2, 9)
                op, ans = "×", a * b
            else:
                a = random.randint(20, 99)
                b = random.randint(2, 9)
                op, ans = "÷", a // b
                ans_real = a / b
                content = f"计算：{a} {op} {b} = （  ）"
                analysis = f"{a} {op} {b} = {a // b} 余 {a % b}。" if a % b else f"{a} {op} {b} = {ans}。"
                opts = _make_opts(ans, [ans+1, ans-1, ans*2, ans//2 if ans > 1 else ans+2])
                questions.append(_make_q(f"数学{g}_{parent}_calc_{qid}", g, parent, name, diff, errors, content, next(o["label"] for o in opts if o["correct"]), analysis, opts))
                return
        elif grade_num >= 5 and ("小数" in name or "小数的" in name):
            a = round(random.uniform(2.5, 25.5), 1)
            b = round(random.uniform(1.5, 12.5), 1)
            if "乘" in name:
                ans = round(a * b, 2)
                op = "×"
            elif "除" in name:
                ans = round(a / b, 2) if b != 0 else 0
                op = "÷"
            elif "加" in name:
                ans = round(a + b, 1)
                op = "+"
            else:
                ans = round(abs(a - b), 1)
                op = "-"
            content = f"计算：{a} {op} {b} = （  ）"
            analysis = f"{a} {op} {b} = {ans}。"
            opts = _make_opts(ans, [round(ans+0.5, 1), round(ans-0.3, 1), round(ans*1.1, 1)])
            questions.append(_make_q(f"数学{g}_{parent}_calc_{qid}", g, parent, name, diff, errors, content, next(o["label"] for o in opts if o["correct"]), analysis, opts))
            return
        else:
            a = random.randint(10, 99)
            b = random.randint(2, 9)
            if "乘" in name or "乘法" in name:
                op, ans = "×", a * b
            elif "除" in name or "除法" in name:
                ans = a // b
                ans_real = a / b
                content = f"计算：{a} ÷ {b} = （  ）"
                analysis = f"{a} ÷ {b} = {a // b} 余 {a % b}。" if a % b else f"{a} ÷ {b} = {ans}。"
                opts = _make_opts(ans, [ans+1, ans-1, ans*2])
                questions.append(_make_q(f"数学{g}_{parent}_calc_{qid}", g, parent, name, diff, errors, content, next(o["label"] for o in opts if o["correct"]), analysis, opts))
                return
            else:
                op, ans = "+" if random.random() > 0.5 else "-", a + b if random.random() > 0.5 else a - b
        content = f"计算：{a} {op} {b} = （  ）"
        analysis = f"{a} {op} {b} = {ans}。"
        opts = _make_opts(ans, [ans+1, ans-1, ans*2, ans//2 if ans > 1 else ans+5])
        questions.append(_make_q(f"数学{g}_{parent}_calc_{qid}", g, parent, name, diff, errors, content, next(o["label"] for o in opts if o["correct"]), analysis, opts))
    
    def gen_fill_q(name, parent, errors, diff, qcat):
        """生成概念/知识填空题。"""
        qid = next_id()
        fill_qs = {
            "比大小": (f"在 7 ○ 3 中应填（  ）", "＞", ["＜", "＞", "＝", "≥"]),
            "认识0": (f"一个也没有，用（  ）表示。", "0", ["1", "0", "没有", "空"]),
            "分类": (f"把苹果、香蕉、橘子分成一类，这是按（  ）分类。", "种类/类别", ["颜色", "大小", "种类/类别", "形状"]),
            "整时认识": (f"时针指向9，分针指向12，是（  ）时。", "9", ["8", "9", "10", "12"]),
            "半时认识": (f"时针走过3，分针指向6，是（  ）时半。", "3", ["2", "3", "4", "6"]),
            "乘法的含义": (f"3+3+3+3=（  ）×3", "4", ["2", "3", "4", "5"]),
            "除法的含义": (f"把12个苹果平均分给3个小朋友，每人（  ）个。", "4", ["2", "3", "4", "6"]),
            "厘米的认识": (f"1米=（  ）厘米", "100", ["10", "50", "100", "1000"]),
            "米的认识": (f"课桌高约70（  ）", "厘米", ["米", "厘米", "分米", "毫米"]),
            "千克的认识": (f"1千克=（  ）克", "1000", ["100", "500", "1000", "10000"]),
            "克的认识": (f"一个鸡蛋约重50（  ）", "克", ["千克", "克", "吨", "斤"]),
            "年月日的关系": (f"一年有（  ）个月", "12", ["10", "11", "12", "13"]),
            "平年和闰年": (f"能被4整除但不能被100整除的年份是（  ）年", "闰", ["平", "闰", "普通", "特殊"]),
            "升的认识": (f"1升=（  ）毫升", "1000", ["100", "500", "1000", "10000"]),
            "毫升的认识": (f"一瓶矿泉水约500（  ）", "毫升", ["升", "毫升", "克", "千克"]),
            "数据收集": (f"收集数据的方法不包括（  ）", "猜测", ["调查", "实验", "查阅资料", "猜测"]),
            "正负数的含义": (f"零下5℃记作（  ）℃", "-5", ["5", "-5", "+5", "0"]),
            "小数的意义": (f"0.5表示（  ）", "十分之五", ["五分之一", "十分之五", "百分之五", "千分之五"]),
            "比的意义": (f"比的前项和后项同时乘一个相同的数（0除外），比值（  ）", "不变", ["变大", "变小", "不变", "不确定"]),
            "百分数的意义": (f"65%读作（  ）", "百分之六十五", ["六十五百分", "65百分", "百分之六十五", "100分之65"]),
            "近似数": (f"3.14159保留两位小数是（  ）", "3.14", ["3.14", "3.15", "3.1", "3.141"]),
            "循环小数": (f"1÷3的商用循环小数表示是（  ）", "0.333...", ["0.3", "0.33", "0.333...", "3"]),
            "可能性大小": (f"掷硬币，正面朝上的可能性是（  ）", "1/2", ["0", "1/2", "1", "不确定"]),
            "长方体的认识": (f"长方体有（  ）个面", "6", ["4", "6", "8", "12"]),
            "正方体的认识": (f"正方体有（  ）条棱", "12", ["6", "8", "12", "24"]),
            "圆的认识": (f"同一个圆中，直径是半径的（  ）倍", "2", ["1", "2", "3", "4"]),
            "用字母表示数": (f"比x大5的数是（  ）", "x+5", ["x+5", "5x", "x-5", "x÷5"]),
            "平均数": (f"小明三次考试分别是85、90、95分，平均分是（  ）", "90", ["85", "90", "95", "270"]),
        }
        for key, (content, ans, choices) in fill_qs.items():
            if name == key:  # 精确匹配知识点名称
                opts = []
                for i, c in enumerate(choices):
                    opts.append({"label": chr(65+i), "text": c, "correct": c == ans})
                questions.append(_make_q(f"数学{g}_{parent}_concept_{qid}", g, parent, name, diff, errors, content, next(o["label"] for o in opts if o["correct"]), f"正确答案是{ans}。", opts))
                return True
        return False
    
    def gen_other_q(name, parent, errors, diff):
        """为未匹配的知识点生成通用题目。"""
        qid = next_id()
        # 方向题
        if "前后左右" in name:
            content = "你的右手边是（  ）"
            ans = "右边"
            opts = _make_opts(ans, ["左边", "右边", "前面", "后面"])
        elif "观察物体" in name or "三视图" in name:
            content = "从不同的方向观察同一个物体，看到的形状（  ）"
            ans = "可能不同"
            opts = _make_opts(ans, ["相同", "可能不同", "一定不同", "无法确定"])
        elif "垂直" in name:
            content = "两条直线相交成直角，这两条直线互相（  ）"
            ans = "垂直"
            opts = _make_opts(ans, ["平行", "垂直", "相交", "重合"])
        elif "平行" in name:
            content = "在同一平面内，不相交的两条直线叫做（  ）"
            ans = "平行线"
            opts = _make_opts(ans, ["相交线", "平行线", "垂线", "线段"])
        elif "角的度量" in name:
            content = "度量角的大小用（  ）"
            ans = "量角器"
            opts = _make_opts(ans, ["三角尺", "量角器", "直尺", "圆规"])
        elif "立体图形" in name:
            content = "下列哪个是立体图形？（  ）"
            ans = "正方体"
            opts = _make_opts(ans, ["正方形", "正方体", "圆", "三角形"])
        elif "混合运算" in name or "运算顺序" in name:
            content = "计算 8 + 4 × 2 时，应先算（  ）"
            ans = "4×2"
            opts = _make_opts(ans, ["8+4", "4×2", "8+4×2", "按顺序"])
        elif "条形统计图" in name:
            content = "条形统计图可以清楚地看出（  ）"
            ans = "数量的多少"
            opts = _make_opts(ans, ["数量的多少", "增减变化", "部分与整体", "分布情况"])
        elif "长方形特征" in name:
            content = "长方形的对边（  ）"
            ans = "相等"
            opts = _make_opts(ans, ["相等", "不相等", "互相垂直", "互相平行"])
        elif "正方形特征" in name:
            content = "正方形的四条边（  ）"
            ans = "都相等"
            opts = _make_opts(ans, ["都相等", "对边相等", "不相等", "两两相等"])
        elif "统计" in name or "数据" in name:
            return False
        else:
            return False
        
        analysis = f"正确答案是{ans}。"
        questions.append(_make_q(f"数学{g}_{parent}_other_{qid}", g, parent, name, diff, errors, content, next(o["label"] for o in opts if o["correct"]), analysis, opts))
        return True
    
    # 主循环：遍历每个知识点
    for node in nodes:
        if node["type"] != "knowledge":
            continue
        name = node["name"]
        parent = node.get("parent", "")
        errors = node.get("errors", [])
        qcat = node.get("qcategory", "arithmetic")
        diff = min(max(node.get("exam_weight", 2), 1), 5)
        
        generated = False
        
        # 1）加减乘除计算题
        if any(kw in name for kw in ["加减", "加法", "减法", "进位", "退位", "连加", "连减", "混合",
                                       "乘法", "口诀", "乘数", "除法", "求商",
                                       "两三位数乘", "两三位数除"]):
            gen_arithmetic_q(name, parent, errors, diff, qcat)
            generated = True
            # 乘法口诀额外多出1题
            if "口诀" in name:
                gen_fill_q(name, parent, errors, diff, qcat)
        
        # 2）几何题
        if any(kw in name for kw in ["周长", "面积", "体积", "表面积"]):
            gen_geometry_q = _make_embedded_geometry(name, parent, errors, diff, g, question_id)
            if gen_geometry_q:
                questions.append(gen_geometry_q)
                generated = True
        
        # 3）方程/解方程
        if "方程" in name or "解方程" in name:
            gen_arithmetic_q(name, parent, errors, diff, qcat)
            generated = True
        
        # 4）百分数
        if "百分数" in name or "百分比" in name:
            gen_percent_q = _make_embedded_percent(name, parent, errors, diff, g, question_id)
            if gen_percent_q:
                questions.append(gen_percent_q)
                generated = True
        
        # 5）比（比例）
        if "比" in name and name != "比大小":
            gen_ratio_q = _make_embedded_ratio(name, parent, errors, diff, g, question_id)
            if gen_ratio_q:
                questions.append(gen_ratio_q)
                generated = True
        
        # 6）小数计算
        if "小数" in name and any(kw in name for kw in ["加减", "加法", "减法", "乘法", "除法", "乘", "除", "加", "减"]):
            gen_arithmetic_q(name, parent, errors, diff, qcat)
            generated = True
        
        # 7）概念/填空题
        if not generated:
            if gen_fill_q(name, parent, errors, diff, qcat):
                generated = True
        
        # 8）兜底：通用题
        if not generated:
            if gen_other_q(name, parent, errors, diff):
                generated = True
    
    return questions


def _make_embedded_geometry(name, parent, errors, diff, g, qid_counter):
    """内联生成几何题。"""
    qid = qid_counter[0]
    qid_counter[0] += 1
    
    if "长方形" in name:
        if "周长" in name:
            l, w = random.randint(3, 12), random.randint(2, 8)
            ans = 2 * (l + w)
            content = f"一个长方形的长是{l}厘米，宽是{w}厘米，它的周长是多少厘米？"
            analysis = f"周长 = 2×({l}+{w}) = {ans}（厘米）。"
        elif "面积" in name:
            l, w = random.randint(3, 12), random.randint(2, 8)
            ans = l * w
            content = f"一个长方形的长是{l}厘米，宽是{w}厘米，它的面积是多少平方厘米？"
            analysis = f"面积 = {l}×{w} = {ans}（平方厘米）。"
        else:
            content = f"长方形有（  ）条边"
            ans = "4"
            analysis = "长方形有4条边。"
    elif "正方形" in name:
        if "周长" in name:
            s = random.randint(3, 10)
            ans = 4 * s
            content = f"正方形的边长是{s}厘米，周长是多少厘米？"
            analysis = f"周长 = 4×{s} = {ans}（厘米）。"
        elif "面积" in name:
            s = random.randint(3, 10)
            ans = s * s
            content = f"正方形的边长是{s}厘米，面积是多少平方厘米？"
            analysis = f"面积 = {s}×{s} = {ans}（平方厘米）。"
        else:
            content = "正方形的（  ）条边都相等"
            ans = "4"
            analysis = "正方形的4条边都相等。"
    elif "三角形" in name:
        base, h = random.randint(4, 12), random.randint(3, 10)
        ans = base * h // 2
        content = f"三角形的底是{base}厘米、高是{h}厘米，面积是多少平方厘米？"
        analysis = f"面积 = {base}×{h}÷2 = {ans}（平方厘米）。"
    elif "梯形" in name:
        a, b, h = random.randint(3, 8), random.randint(5, 12), random.randint(3, 8)
        ans = (a + b) * h // 2
        content = f"梯形的上底{a}厘米、下底{b}厘米、高{h}厘米，面积是多少平方厘米？"
        analysis = f"面积 = ({a}+{b})×{h}÷2 = {ans}（平方厘米）。"
    elif "平行四边形" in name:
        base, h = random.randint(4, 12), random.randint(3, 10)
        ans = base * h
        content = f"平行四边形的底是{base}厘米、高是{h}厘米，面积是多少平方厘米？"
        analysis = f"面积 = {base}×{h} = {ans}（平方厘米）。"
    elif "圆" in name and "周长" in name:
        r = random.randint(2, 8)
        ans = round(2 * 3.14 * r, 1)
        content = f"圆的半径是{r}厘米，周长是多少厘米？（π=3.14）"
        analysis = f"C=2πr=2×3.14×{r}={ans}（厘米）。"
    elif "圆" in name and "面积" in name:
        r = random.randint(2, 8)
        ans = round(3.14 * r * r, 1)
        content = f"圆的半径是{r}厘米，面积是多少平方厘米？（π=3.14）"
        analysis = f"S=πr²=3.14×{r}²={ans}（平方厘米）。"
    elif "表面积" in name:
        a = random.randint(3, 8)
        ans = 6 * a * a
        content = f"正方体的棱长是{a}厘米，表面积是多少平方厘米？"
        analysis = f"S=6a²=6×{a}²={ans}（平方厘米）。"
    elif "体积" in name and "长方" in name:
        l, w, h = random.randint(3, 8), random.randint(2, 6), random.randint(2, 5)
        ans = l * w * h
        content = f"长方体的长{l}厘米、宽{w}厘米、高{h}厘米，体积是多少立方厘米？"
        analysis = f"V=abc={l}×{w}×{h}={ans}（立方厘米）。"
    elif "体积" in name and "正方" in name:
        a = random.randint(3, 8)
        ans = a * a * a
        content = f"正方体的棱长是{a}厘米，体积是多少立方厘米？"
        analysis = f"V=a³={a}³={ans}（立方厘米）。"
    else:
        return None
    
    opts = _make_opts(ans, [ans+random.randint(1,5), ans*2, max(ans//2, 1), ans+random.randint(5,10)])
    return _make_q(f"数学{g}_{parent}_geo_{qid}", g, parent, name, diff, errors, content, next(o["label"] for o in opts if o["correct"]), analysis, opts, "geometry")


def _make_embedded_percent(name, parent, errors, diff, g, qid_counter):
    """内联生成百分数应用题。"""
    qid = qid_counter[0]
    qid_counter[0] += 1
    total = random.choice([100, 200, 300, 500])
    pct = random.choice([10, 15, 20, 25, 30, 50])
    part = total * pct // 100
    content = f"某校有学生{total}人，男生占{pct}%，男生有多少人？"
    ans = part
    analysis = f"{total}×{pct}%={total}×0.{pct}={ans}（人）。"
    opts = _make_opts(ans, [ans+random.randint(10,50), ans-random.randint(5,20), total-ans, total])
    return _make_q(f"数学{g}_{parent}_pct_{qid}", g, parent, name, diff, errors, content, next(o["label"] for o in opts if o["correct"]), analysis, opts)


def _make_embedded_ratio(name, parent, errors, diff, g, qid_counter):
    """内联生成比例题。"""
    qid = qid_counter[0]
    qid_counter[0] += 1
    a, b = random.randint(2, 6), random.randint(3, 8)
    total = random.choice([20, 30, 40, 50, 60])
    factor = total // (a + b)
    if factor < 1:
        return None
    ans = max(a, b) * factor
    content = f"把{total}按{a}:{b}分配，较大的部分是（  ）"
    analysis = f"总份数{a}+{b}={a+b}，每份{total}÷{a+b}={factor}，较大={max(a,b)}×{factor}={ans}"
    opts = _make_opts(ans, [min(a,b)*factor, total//2, ans+factor, ans*2])
    return _make_q(f"数学{g}_{parent}_ratio_{qid}", g, parent, name, diff, errors, content, next(o["label"] for o in opts if o["correct"]), analysis, opts)


def generate_chinese_questions(subject: str, grade: int, nodes: list) -> list:
    """为语文学科生成题目。"""
    questions = []
    g = f"{['一','二','三','四','五','六'][grade-1]}年级"
    
    question_id = 1
    for node in nodes:
        if node["type"] != "knowledge":
            continue
        name = node["name"]
        parent = node.get("parent", "")
        errors = node.get("errors", [])
        diff = min(node.get("exam_weight", 2), 5)
        diff = max(diff, 1)
        
        if "拼音" in name or "韵母" in name or "声母" in name:
            # 拼音题
            choices = [
                ("b", "p", "d", "q", "b"),
                ("m", "n", "l", "f", "m"),
                ("a", "o", "e", "i", "a"),
                ("ai", "ei", "ui", "ao", "ai"),
                ("zh", "z", "ch", "c", "zh"),
            ]
            ch = random.choice(choices)
            words = ["爸爸", "妈妈", "大", "小", "上", "下", "山", "水", "花", "鸟"]
            w = random.choice(words)
            content = f"下面哪个字的声母是「{ch[4]}」？"
            
            opts = []
            labels_all = ["A", "B", "C", "D"]
            for i, lbl in enumerate(ch[:4]):
                opts.append({"label": labels_all[i], "text": lbl, "correct": lbl == ch[4]})
            random.shuffle(opts)
            
            q = {
                "id": f"语文{g}_{parent}_pinyin_{question_id}",
                "type": "选择题",
                "subject": "语文",
                "grade": g,
                "chapter": parent,
                "knowledge": [name],
                "difficulty": diff,
                "exam_weight": diff,
                "subtype": "基础知识",
                "error_tags": errors,
                "content": content,
                "answer": next(o["label"] for o in opts if o["correct"]),
                "analysis": f"正确选项的声母是「{ch[4]}」。",
                "options": opts,
            }
            questions.append(q)
            question_id += 1
        
        elif "笔画" in name or "偏旁" in name or "结构" in name:
            # 汉字题
            chars = [
                ("山", 3, "竖折"), ("水", 4, "竖钩"), ("火", 4, "点"),
                ("木", 4, "横"), ("日", 4, "竖"), ("月", 4, "撇"),
                ("花", 7, "草字头"), ("草", 9, "草字头"), ("明", 8, "日字旁"),
            ]
            ch = random.choice(chars)
            content = f"「{ch[0]}」字共有多少画？"
            ans = ch[1]
            analysis = f"「{ch[0]}」字共有{ans}画。"
            wrongs = [ans+1, ans-1, ans+2]
            wrongs = [w for w in wrongs if w != ans and w > 0][:3]
            while len(wrongs) < 3:
                wrongs.append(ans + len(wrongs) + 2)
            
            opts = []
            labels_all = ["A", "B", "C", "D"]
            random.shuffle(labels_all)
            opts.append({"label": labels_all[0], "text": str(ans), "correct": True})
            for i, w in enumerate(wrongs[:3]):
                opts.append({"label": labels_all[i+1], "text": str(w), "correct": False})
            
            q = {
                "id": f"语文{g}_{parent}_stroke_{question_id}",
                "type": "选择题",
                "subject": "语文",
                "grade": g,
                "chapter": parent,
                "knowledge": [name],
                "difficulty": diff,
                "exam_weight": diff,
                "subtype": "基础知识",
                "error_tags": errors,
                "content": content,
                "answer": labels_all[0],
                "analysis": analysis,
                "options": opts,
            }
            questions.append(q)
            question_id += 1
        
        elif "形近" in name or "同音" in name or "多音" in name or "字义" in name:
            # 辨析题
            pairs = [
                ("已", "己", "已经", "已"),
                ("人", "入", "进入", "入"),
                ("大", "太", "大小", "大"),
                ("晴", "睛", "晴天", "晴"),
                ("做", "作", "作业", "作"),
                ("座", "坐", "坐下", "坐"),
                ("在", "再", "再见", "再"),
                ("的", "地", "高兴地说", "地"),
            ]
            pair = random.choice(pairs)
            content = f"选择正确的字：{pair[2]}中应填（  ）"
            opts = []
            labels_all = ["A", "B", "C", "D"]
            opts.append({"label": "A", "text": pair[0], "correct": pair[3] == pair[0]})
            opts.append({"label": "B", "text": pair[1], "correct": pair[3] == pair[1]})
            opts.append({"label": "C", "text": "—", "correct": False})
            opts.append({"label": "D", "text": "—", "correct": False})
            
            q = {
                "id": f"语文{g}_{parent}_distinguish_{question_id}",
                "type": "选择题",
                "subject": "语文",
                "grade": g,
                "chapter": parent,
                "knowledge": [name],
                "difficulty": diff,
                "exam_weight": diff,
                "subtype": "基础知识",
                "error_tags": errors,
                "content": content.replace("—", ""),
                "answer": next(o["label"] for o in opts if o["correct"]),
                "analysis": f"正确选项是「{pair[3]}」。",
                "options": [o for o in opts if o["text"] != "—"],
            }
            questions.append(q)
            question_id += 1
        
        elif "成语" in name or "词语" in name or "名言" in name or "歇后语" in name:
            # 词语题
            idiom_qs = [
                ("画蛇添足", "做多余的事", "画龙点睛"), ("亡羊补牢", "出了问题及时补救", "守株待兔"),
                ("掩耳盗铃", "自己欺骗自己", "刻舟求剑"), ("守株待兔", "不劳而获的侥幸心理", "拔苗助长"),
                ("叶公好龙", "口头喜欢实际害怕", "画蛇添足"),
            ]
            iq = random.choice(idiom_qs)
            content = f"「{iq[0]}」这个成语的意思是（  ）"
            ans = iq[1]
            opts = []
            labels_all = ["A", "B", "C", "D"]
            wrongs_all = [iq[2], "形容速度快", "表示数量多", "说明颜色美"]
            ww = [w for w in wrongs_all if w != ans][:3]
            all_choices = [ans] + ww
            random.shuffle(all_choices)
            for i, c in enumerate(all_choices):
                opts.append({"label": labels_all[i], "text": c, "correct": c == ans})
            
            q = {
                "id": f"语文{g}_{parent}_idiom_{question_id}",
                "type": "选择题",
                "subject": "语文",
                "grade": g,
                "chapter": parent,
                "knowledge": [name],
                "difficulty": diff,
                "exam_weight": diff,
                "subtype": "词语积累",
                "error_tags": errors,
                "content": content,
                "answer": next(o["label"] for o in opts if o["correct"]),
                "analysis": f"「{iq[0]}」的意思是{iq[1]}。",
                "options": opts,
            }
            questions.append(q)
            question_id += 1
        
        elif "古诗" in name or "古诗文" in name:
            # 古诗题
            poems = [
                ("春晓", "孟浩然", "春眠不觉晓", "处处闻啼鸟"),
                ("静夜思", "李白", "床前明月光", "疑是地上霜"),
                ("登鹳雀楼", "王之涣", "白日依山尽", "黄河入海流"),
                ("望庐山瀑布", "李白", "日照香炉生紫烟", "遥看瀑布挂前川"),
                ("绝句", "杜甫", "两个黄鹂鸣翠柳", "一行白鹭上青天"),
                ("咏柳", "贺知章", "碧玉妆成一树高", "万条垂下绿丝绦"),
                ("望天门山", "李白", "天门中断楚江开", "碧水东流至此回"),
            ]
            p = random.choice(poems)
            content = f"「{p[0]}」的作者是（  ）"
            opts = []
            labels_all = ["A", "B", "C", "D"]
            wrong_authors = ["杜甫", "白居易", "王维", "苏轼", "王安石", "杜牧"]
            wa = [w for w in wrong_authors if w != p[1]][:3]
            all_c = [p[1]] + wa
            random.shuffle(all_c)
            for i, c in enumerate(all_c):
                opts.append({"label": labels_all[i], "text": c, "correct": c == p[1]})
            
            q = {
                "id": f"语文{g}_{parent}_poem_{question_id}",
                "type": "选择题",
                "subject": "语文",
                "grade": g,
                "chapter": parent,
                "knowledge": [name],
                "difficulty": diff,
                "exam_weight": diff,
                "subtype": "古诗文",
                "error_tags": errors,
                "content": content,
                "answer": next(o["label"] for o in opts if o["correct"]),
                "analysis": f"《{p[0]}》是{p[1]}的作品。{p[2]}，{p[3]}。",
                "options": opts,
            }
            questions.append(q)
            question_id += 1
        
        elif "阅读" in name or "理解" in name or "句" in name:
            # 阅读理解题（基础）
            passages = [
                "春天来了，小燕子从南方飞回来了。小草从地下探出头来，小花也开了。",
                "秋天到了，树叶黄了。大雁往南方飞去。田野里一片丰收的景象。",
                "小兔子住在森林里。它每天早起锻炼身体，朋友们都喜欢和它一起玩。",
                "太阳从东方升起。小鸟在树上唱歌。小朋友们背着书包去上学。",
            ]
            q_types = [
                ("这段话主要写了什么？", ["春天的景色", "夏天的天气", "秋天的丰收", "冬天的寒冷"], 0),
                ("文中提到的动物是什么？", ["燕子", "大雁", "小兔子", "小鸟"], None),
            ]
            passage = random.choice(passages)
            qt = random.choice(q_types)
            correct_idx = qt[2] if qt[2] is not None else random.randint(0, len(qt[1])-1)
            content = f"阅读下面这段话，回答问题。\n「{passage}」\n{qt[0]}"
            
            opts = []
            labels_all = ["A", "B", "C", "D"]
            for i, c in enumerate(qt[1]):
                opts.append({"label": labels_all[i], "text": c, "correct": i == correct_idx})
            
            q = {
                "id": f"语文{g}_{parent}_reading_{question_id}",
                "type": "选择题",
                "subject": "语文",
                "grade": g,
                "chapter": parent,
                "knowledge": [name],
                "difficulty": diff,
                "exam_weight": diff,
                "subtype": "阅读",
                "error_tags": errors,
                "content": content,
                "answer": next(o["label"] for o in opts if o["correct"]),
                "analysis": f"正确答案是：{qt[1][correct_idx]}。",
                "options": opts,
            }
            questions.append(q)
            question_id += 1
    
    return questions


def generate_english_questions(subject: str, grade: int, nodes: list) -> list:
    """为英语学科生成题目。"""
    questions = []
    g = f"{['一','二','三','四','五','六'][grade-1]}年级"
    
    question_id = 1
    for node in nodes:
        if node["type"] != "knowledge":
            continue
        name = node["name"]
        parent = node.get("parent", "")
        errors = node.get("errors", [])
        diff = min(node.get("exam_weight", 2), 5)
        diff = max(diff, 1)
        
        if "字母" in name:
            # 字母题
            letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            l = random.choice(letters)
            lower = l.lower()
            content = f"大写字母 {l} 的小写形式是（  ）"
            wrongs = [chr(ord(l)+1).lower() if ord(l) < 90 else 'a', chr(ord(l)-1).lower() if ord(l) > 65 else 'z', l.lower()]
            wrongs = [w for w in wrongs if w != lower][:3]
            while len(wrongs) < 3:
                wrongs.append(random.choice(letters).lower())
            
            opts = []
            labels_all = ["A", "B", "C", "D"]
            random.shuffle(labels_all)
            opts.append({"label": labels_all[0], "text": lower, "correct": True})
            for i, w in enumerate(wrongs[:3]):
                opts.append({"label": labels_all[i+1], "text": w, "correct": False})
            
            q = {
                "id": f"英语{g}_{parent}_letter_{question_id}",
                "type": "选择题",
                "subject": "英语",
                "grade": g,
                "chapter": parent,
                "knowledge": [name],
                "difficulty": diff,
                "exam_weight": diff,
                "subtype": "字母",
                "error_tags": errors,
                "content": content,
                "answer": labels_all[0],
                "analysis": f"大写 {l} 的小写是 {lower}。",
                "options": opts,
            }
            questions.append(q)
            question_id += 1
        
        elif "词汇" in name or "单词" in name or "动物" in name or "颜色" in name or "数字" in name or "食物" in name or "服装" in name or "天气" in name or "季节" in name or "月份" in name or "爱好" in name or "职业" in name or "文具" in name or "家庭" in name:
            # 词汇题
            vocabs = {
                "动物": [("cat", "猫"), ("dog", "狗"), ("bird", "鸟"), ("fish", "鱼"), ("duck", "鸭子"), ("pig", "猪"), ("cow", "牛"), ("sheep", "羊")],
                "颜色": [("red", "红色"), ("blue", "蓝色"), ("green", "绿色"), ("yellow", "黄色"), ("white", "白色"), ("black", "黑色")],
                "数字": [("one", "一"), ("two", "二"), ("three", "三"), ("four", "四"), ("five", "五"), ("six", "六"), ("seven", "七"), ("eight", "八"), ("nine", "九"), ("ten", "十")],
                "食物": [("rice", "米饭"), ("bread", "面包"), ("milk", "牛奶"), ("egg", "鸡蛋"), ("apple", "苹果"), ("banana", "香蕉")],
                "文具": [("book", "书"), ("pen", "钢笔"), ("pencil", "铅笔"), ("ruler", "尺子"), ("bag", "书包")],
                "天气": [("sunny", "晴朗的"), ("cloudy", "多云的"), ("rainy", "下雨的"), ("windy", "有风的"), ("snowy", "下雪的")],
                "家庭": [("father", "爸爸"), ("mother", "妈妈"), ("brother", "兄弟"), ("sister", "姐妹"), ("family", "家庭")],
                "服装": [("shirt", "衬衫"), ("coat", "外套"), ("skirt", "裙子"), ("shoe", "鞋子"), ("hat", "帽子")],
                "月份": [("January", "一月"), ("February", "二月"), ("March", "三月"), ("April", "四月"), ("May", "五月"), ("June", "六月")],
                "职业": [("teacher", "老师"), ("doctor", "医生"), ("nurse", "护士"), ("driver", "司机"), ("farmer", "农民")],
                "爱好": [("swimming", "游泳"), ("running", "跑步"), ("reading", "阅读"), ("singing", "唱歌"), ("dancing", "跳舞")],
            }
            for cat, words_list in vocabs.items():
                if cat in name or any(w in name for w in ["单词", "词汇"]):
                    w = random.choice(words_list)
                    content = f"「{w[1]}」的英语是（  ）"
                    wrongs = [x[0] for x in words_list if x[0] != w[0]][:3]
                    while len(wrongs) < 3:
                        wrongs.append(random.choice(words_list)[0])
                    
                    opts = []
                    labels_all = ["A", "B", "C", "D"]
                    random.shuffle(labels_all)
                    opts.append({"label": labels_all[0], "text": w[0], "correct": True})
                    for i, ww in enumerate(wrongs[:3]):
                        opts.append({"label": labels_all[i+1], "text": ww, "correct": False})
                    
                    q = {
                        "id": f"英语{g}_{parent}_vocab_{question_id}",
                        "type": "选择题",
                        "subject": "英语",
                        "grade": g,
                        "chapter": parent,
                        "knowledge": [name],
                        "difficulty": diff,
                        "exam_weight": diff,
                        "subtype": "词汇",
                        "error_tags": errors,
                        "content": content,
                        "answer": labels_all[0],
                        "analysis": f"「{w[1]}」的英语是 {w[0]}。",
                        "options": opts,
                    }
                    questions.append(q)
                    question_id += 1
                    break
        
        elif "句型" in name or "there be" in name or "There" in name or "句" in name:
            # 句型题
            structures = [
                ("This __ a book.", "is", ["am", "are", "be"]),
                ("They __ students.", "are", ["is", "am", "be"]),
                ("I __ a teacher.", "am", ["is", "are", "be"]),
                ("She __ to school every day.", "goes", ["go", "going", "went"]),
                ("He __ playing football.", "is", ["am", "are", "be"]),
            ]
            s = random.choice(structures)
            content = f"选择正确的词填空：{s[0]}"
            opts = []
            labels_all = ["A", "B", "C", "D"]
            all_choices = [s[1]] + s[2]
            random.shuffle(all_choices)
            for i, c in enumerate(all_choices):
                opts.append({"label": labels_all[i], "text": c, "correct": c == s[1]})
            
            q = {
                "id": f"英语{g}_{parent}_sentence_{question_id}",
                "type": "选择题",
                "subject": "英语",
                "grade": g,
                "chapter": parent,
                "knowledge": [name],
                "difficulty": diff,
                "exam_weight": diff,
                "subtype": "语法",
                "error_tags": errors,
                "content": content,
                "answer": next(o["label"] for o in opts if o["correct"]),
                "analysis": f"正确答案是 {s[1]}。",
                "options": opts,
            }
            questions.append(q)
            question_id += 1
        
        elif "时态" in name or "进行时" in name or "过去时" in name or "将来时" in name or "完成时" in name or "比较级" in name or "序数词" in name or "三单" in name:
            # 语法题
            grammar_items = [
                ("He __ (go) to school yesterday.", "went", ["goes", "go", "going", "gone"]),
                ("She is __ (read) a book now.", "reading", ["read", "reads", "readed", "to read"]),
                ("They __ (be) going to play football.", "are", ["is", "am", "was", "were"]),
                ("My sister is __ (tall) than me.", "taller", ["tall", "tallest", "more tall", "the tallest"]),
                ("I have __ (finish) my homework.", "finished", ["finish", "finishing", "finishes", "to finish"]),
                ("This is the __ (big) apple.", "biggest", ["big", "bigger", "more big", "most big"]),
            ]
            g_item = random.choice(grammar_items)
            content = f"用所给词的适当形式填空：\n{g_item[0]}"
            opts = []
            labels_all = ["A", "B", "C", "D"]
            all_choices = list(set(g_item[2]))
            if len(all_choices) < 4:
                all_choices = g_item[2][:4]
            random.shuffle(all_choices)
            if g_item[1] not in all_choices:
                all_choices[-1] = g_item[1]
            random.shuffle(all_choices)
            for i, c in enumerate(all_choices[:4]):
                opts.append({"label": labels_all[i], "text": c, "correct": c == g_item[1]})
            
            q = {
                "id": f"英语{g}_{parent}_grammar_{question_id}",
                "type": "选择题",
                "subject": "英语",
                "grade": g,
                "chapter": parent,
                "knowledge": [name],
                "difficulty": diff,
                "exam_weight": diff,
                "subtype": "语法",
                "error_tags": errors,
                "content": content,
                "answer": next(o["label"] for o in opts if o["correct"]),
                "analysis": f"正确答案是 {g_item[1]}。",
                "options": opts,
            }
            questions.append(q)
            question_id += 1
        
        elif "问候" in name or "打招呼" in name or "介绍" in name or "问路" in name or "梦想" in name or "can" in name or "节日" in name:
            # 交际题
            dialogues = [
                ("—Hello! —__", "Hi!", ["Goodbye!", "Thank you!", "Sorry!", "Hi!"]),
                ("—Nice to meet you. —__", "Nice to meet you, too.", ["Thank you!", "Goodbye!", "I'm fine.", "Nice to meet you, too."]),
                ("—How are you? —__", "I'm fine, thank you.", ["I'm 10.", "I'm a student.", "I like apples.", "I'm fine, thank you."]),
                ("—What's this? —__", "It's a book.", ["I'm a book.", "This is me.", "That's OK.", "It's a book."]),
                ("—Where is the library? —__", "It's near the park.", ["Yes, it is.", "No, it isn't.", "I like it.", "It's near the park."]),
            ]
            d = random.choice(dialogues)
            content = f"选择合适的答语：{d[0]}"
            opts = []
            labels_all = ["A", "B", "C", "D"]
            all_choices = list(set(d[2]))
            random.shuffle(all_choices)
            for i, c in enumerate(all_choices[:4]):
                opts.append({"label": labels_all[i], "text": c, "correct": c == d[1]})
            
            q = {
                "id": f"英语{g}_{parent}_dialogue_{question_id}",
                "type": "选择题",
                "subject": "英语",
                "grade": g,
                "chapter": parent,
                "knowledge": [name],
                "difficulty": diff,
                "exam_weight": diff,
                "subtype": "交际",
                "error_tags": errors,
                "content": content,
                "answer": next(o["label"] for o in opts if o["correct"]),
                "analysis": f"正确答语是「{d[1]}」。",
                "options": opts,
            }
            questions.append(q)
            question_id += 1
        
        elif "阅读" in name:
            # 英语阅读理解
            passages_en = [
                ("Tom is a boy. He is 10. He likes playing football.", "How old is Tom?", ["9", "10", "11", "12"], 1),
                ("Mary has a cat. The cat is white. It likes fish.", "What color is the cat?", ["Black", "White", "Brown", "Yellow"], 1),
                ("I get up at 6 o'clock. I go to school at 7 o'clock.", "When do I get up?", ["At 5", "At 6", "At 7", "At 8"], 1),
            ]
            pe = random.choice(passages_en)
            content = f"阅读短文，选择正确答案：\n{pe[0]}\n{pe[1]}"
            opts = []
            labels_all = ["A", "B", "C", "D"]
            for i, c in enumerate(pe[2]):
                opts.append({"label": labels_all[i], "text": c, "correct": i == pe[3]})
            
            q = {
                "id": f"英语{g}_{parent}_reading_{question_id}",
                "type": "选择题",
                "subject": "英语",
                "grade": g,
                "chapter": parent,
                "knowledge": [name],
                "difficulty": diff,
                "exam_weight": diff,
                "subtype": "阅读",
                "error_tags": errors,
                "content": content,
                "answer": next(o["label"] for o in opts if o["correct"]),
                "analysis": f"正确答案是{pe[2][pe[3]]}。",
                "options": opts,
            }
            questions.append(q)
            question_id += 1
    
    return questions


def generate_science_questions(subject: str, grade: int, nodes: list) -> list:
    """为科学学科生成题目。"""
    questions = []
    g = f"{['一','二','三','四','五','六'][grade-1]}年级"
    
    question_id = 1
    for node in nodes:
        if node["type"] != "knowledge":
            continue
        name = node["name"]
        parent = node.get("parent", "")
        errors = node.get("errors", [])
        diff = min(node.get("exam_weight", 2), 5)
        diff = max(diff, 1)
        
        science_qs = {
            "磁铁的两极": ("磁铁的同极相互（  ）", "排斥", ["吸引", "没有作用", "有时吸引有时排斥", "排斥"]),
            "磁铁的应用": ("以下哪个物品利用了磁铁？", "指南针", ["书本", "指南针", "铅笔", "书包"]),
            "种子发芽条件": ("种子发芽不需要的条件是（  ）", "阳光", ["水", "空气", "阳光", "适宜的温度"]),
            "水的三态": ("水在0℃时会变成（  ）", "冰", ["水蒸气", "冰", "雪", "霜"]),
            "蒸发与凝结": ("湿衣服变干是（  ）现象", "蒸发", ["凝结", "蒸发", "融化", "凝固"]),
            "串联与并联": ("两个灯泡一个亮一个灭，电路可能是（  ）", "串联", ["并联", "串联", "混联", "无法判断"]),
            "导体与绝缘体": ("以下哪个是导体？", "铁钉", ["塑料尺", "铁钉", "木棒", "橡皮"]),
            "电路组成": ("一个完整的电路至少需要（  ）", "电源、导线、用电器", ["电源和导线", "导线和开关", "电源、导线、用电器", "电源、用电器、开关"]),
            "光的直线传播": ("影子形成的原因是（  ）", "光沿直线传播", ["光沿直线传播", "光的反射", "光的折射", "光的散射"]),
            "光的反射": ("我们能看见镜子里的自己是利用了（  ）", "光的反射", ["光的直线传播", "光的反射", "光的折射", "光的吸收"]),
            "昼夜交替": ("昼夜交替的原因是（  ）", "地球自转", ["地球自转", "地球公转", "月球公转", "太阳自转"]),
            "四季变化": ("四季变化的主要原因是（  ）", "地球公转", ["地球自转", "地球公转", "月球引力", "太阳活动"]),
            "食物链": ("下面哪条食物链是正确的？", "草→兔子→狼", ["草→狼→兔子", "狼→兔子→草", "草→兔子→狼", "兔子→草→狼"]),
            "细胞结构": ("植物细胞有而动物细胞没有的结构是（  ）", "细胞壁", ["细胞膜", "细胞壁", "细胞核", "细胞质"]),
            "消化系统": ("食物消化和吸收的主要场所是（  ）", "小肠", ["胃", "小肠", "大肠", "口腔"]),
            "呼吸系统": ("呼吸时，气体交换的场所是（  ）", "肺", ["气管", "肺", "鼻腔", "支气管"]),
            "太阳系组成": ("太阳系中最大的行星是（  ）", "木星", ["土星", "木星", "海王星", "地球"]),
            "重力": ("地球上的物体受到的重力方向是（  ）", "竖直向下", ["水平向右", "竖直向下", "竖直向上", "斜向上"]),
            "摩擦力": ("下列哪种做法是为了增大摩擦力？", "鞋底有花纹", ["给车轮加润滑油", "鞋底有花纹", "冰壶比赛刷冰面", "行李箱装轮子"]),
            "声音的产生": ("声音是由（  ）产生的", "振动", ["振动", "空气流动", "温度变化", "光的传播"]),
            "声音的传播介质": ("声音不能在（  ）中传播", "真空", ["空气", "水", "真空", "金属"]),
            "声音的高低强弱": ("声音的高低叫做（  ）", "音调", ["音量", "音调", "音色", "音频"]),
            "植物的结构": ("植物通过（  ）吸收水分和营养", "根", ["叶", "根", "茎", "花"]),
            "遗传现象": ("子女和父母长得很像，这是（  ）现象", "遗传", ["变异", "遗传", "进化", "适应"]),
            "变异现象": ("一株白花植物开出红花，这是（  ）现象", "变异", ["遗传", "变异", "进化", "适应"]),
        }
        
        if name in science_qs:
            sq = science_qs[name]
            content = sq[0]
            ans = sq[1]
            choices = sq[2]
            opts = []
            labels_all = ["A", "B", "C", "D"]
            for i, c in enumerate(choices):
                opts.append({"label": labels_all[i], "text": c, "correct": c == ans})
            
            q = {
                "id": f"科学{g}_{parent}_science_{question_id}",
                "type": "选择题",
                "subject": "科学",
                "grade": g,
                "chapter": parent,
                "knowledge": [name],
                "difficulty": diff,
                "exam_weight": diff,
                "subtype": "科学知识",
                "error_tags": errors,
                "content": content,
                "answer": next(o["label"] for o in opts if o["correct"]),
                "analysis": f"正确答案是「{ans}」。",
                "options": opts,
            }
            questions.append(q)
            question_id += 1
    
    return questions


# ====================================================================
# 写入函数
# ====================================================================

def save_knowledge(subject: str, grade: int, data: dict):
    """保存知识图谱JSON文件。"""
    g = f"{['一','二','三','四','五','六'][grade-1]}年级"
    subj_dir_map = {
        "数学": "yancheng_math",
        "语文": "yancheng_chinese",
        "英语": "yancheng_english",
        "科学": "yancheng_science",
    }
    subdir = subj_dir_map[subject]
    out_dir = KNOWLEDGE_DIR / subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"grade{grade}.json"
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 写入知识图谱: {out_path.relative_to(PROJECT_ROOT)} ({len(data['nodes'])} 个节点)")


def save_questions(subject: str, grade: int, questions: list):
    """保存题库JSON文件。"""
    g = f"{['一','二','三','四','五','六'][grade-1]}年级"
    subj_dir_map = {
        "数学": "yancheng_math",
        "语文": "yancheng_chinese",
        "英语": "yancheng_english",
        "科学": "yancheng_science",
    }
    subdir = subj_dir_map[subject]
    out_dir = QUESTIONS_DIR / subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"grade{grade}.json"
    
    data = {"subject": subject, "grade": g, "version": "盐城专用", "questions": questions}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 写入题库: {out_path.relative_to(PROJECT_ROOT)} ({len(questions)} 道题)")


# ====================================================================
# 主流程
# ====================================================================

GENERATORS = {
    "数学": generate_math_questions,
    "语文": generate_chinese_questions,
    "英语": generate_english_questions,
    "科学": generate_science_questions,
}

def main():
    print("=" * 60)
    print("盐城市小学1-6年级教材数据生成器")
    print("版本：苏教版（数学）/ 部编版（语文）/ 译林版（英语）/ 苏教版（科学）")
    print("=" * 60)
    
    total_knowledge = 0
    total_questions = 0
    
    for subject, grades_dict in KNOWLEDGE_MAP.items():
        print(f"\n--- {subject} ---")
        for grade_num, kg_data in sorted(grades_dict.items()):
            print(f"\n  生成 {kg_data['grade']}...")
            
            # 保存知识图谱
            save_knowledge(subject, grade_num, kg_data)
            total_knowledge += len(kg_data["nodes"])
            
            # 生成并保存题目
            if subject in GENERATORS:
                gen_func = GENERATORS[subject]
                questions = gen_func(subject, grade_num, kg_data["nodes"])
                save_questions(subject, grade_num, questions)
                total_questions += len(questions)
    
    print("\n" + "=" * 60)
    print(f"生成完成！总计：")
    print(f"  知识节点: {total_knowledge} 个")
    print(f"  题目: {total_questions} 道")
    print(f"  覆盖学科: 4 科（数学、语文、英语、科学）")
    print(f"  覆盖年级: 1-6 年级（英语 3-6 年级）")
    print("=" * 60)
    print("\n文件保存在 resource/knowledge/yancheng_*/ 和 resource/questions/yancheng_*/")
    print("运行 seed_data.py 导入数据库，或使用 tools/question_importer/importer.py 批量导入。")


if __name__ == "__main__":
    main()
