# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""江苏盐城体系 · 数学知识树构建器（Phase 1.5-D，知识图谱规模化版）。

相对 Phase 1.5-C 的升级：
1. 初中知识图谱规模化至 ~1200 节点：按苏科版七/八/九完整章节扩充基础概念
   （实数 / 平面直角坐标 / 三角形 / 全等 / 不等式 / 因式 / 旋转 / 锐角三角函数 /
   反比例 / 统计图表 / 概率 等），叶子知识点经面状展开(facets) 5× 增至 ~1200。
2. 题型矩阵全覆盖：每个叶子知识点映射至 generator 的 120 类 qcategory
   （含 Phase 1.5-D 新增 86 类），保证生成器输出题型多样。
3. 知识关联密度强化：扩展「数学思想方法」枢纽节点的 relations，并在多个
   普通节点间建立横向 relations，构成「概念 ↔ 思想方法」稠密网络。

输出到 resources/knowledge/{primary_math,middle_math}/gradeN.json。
"""
from __future__ import annotations

import json
from pathlib import Path

import config.settings as cfg

VERSION = "苏科版"

# 面状展开的子节点类型（受控粒度扩展，提高图谱密度与掌握度追踪精度）
FACETS = ["·概念理解", "·基础运算", "·性质应用", "·易错辨析", "·综合提高"]


def nd(name, parent=None, type="knowledge", summary="", formula=None,
       important=False, predecessor=None, successor=None, errors=None,
       exam_weight=1, qcategory=None, relations=None):
    d = {"name": name, "type": type}
    if parent:
        d["parent"] = parent
    if summary:
        d["summary"] = summary
    if formula is not None:
        d["formula"] = formula
    if important:
        d["important"] = True
    if predecessor:
        d["predecessor"] = predecessor
    if successor:
        d["successor"] = successor
    if errors:
        d["errors"] = errors
    if exam_weight and exam_weight != 1:
        d["exam_weight"] = exam_weight
    if qcategory:
        d["qcategory"] = qcategory
    if relations:
        d["relations"] = relations
    return d


# ===========================================================================
# 七年级（苏科版）
# ===========================================================================
def grade7() -> dict:
    return {
        "subject": "数学", "grade": "七年级", "version": VERSION,
        "nodes": [
            # 有理数
            nd("有理数", type="chapter", summary="整数与分数的统称，含正有理数、0、负有理数。"),
            nd("正数与负数", parent="有理数", summary="大于0为正，小于0为负；0既非正也非负。",
               qcategory="rational_compare", exam_weight=2),
            nd("有理数分类", parent="有理数", summary="有理数分为整数与分数。",
               qcategory="rational_compare", exam_weight=2),
            nd("数轴", parent="有理数", summary="规定了原点、正方向、单位长度的直线。",
               qcategory="rational_compare", exam_weight=3, important=True,
               errors=["混淆原点与单位长度", "不会用数轴比较大小"]),
            nd("相反数", parent="有理数", summary="只有符号不同的两个数互为相反数。",
               qcategory="rational_compare", exam_weight=3, errors=["误认为相反数一定一正一负"]),
            nd("绝对值", parent="有理数", summary="数轴上数到原点的距离；|a|≥0。",
               qcategory="rational_compare", exam_weight=4, important=True,
               errors=["忽略绝对值非负性", "化简|a|不分类讨论"]),
            nd("有理数加法", parent="有理数", summary="同号相加取同号；异号取绝对值大者符号。",
               qcategory="rational_op", exam_weight=3),
            nd("有理数减法", parent="有理数", summary="减去一个数等于加它的相反数。",
               qcategory="integer_add_sub", exam_weight=3, errors=["减法不变为加相反数"]),
            nd("有理数乘法", parent="有理数", summary="同号得正异号得负；0乘任何数为0。",
               qcategory="integer_mult", exam_weight=3, errors=["符号判断错误"]),
            nd("有理数除法", parent="有理数", summary="除以非零数等于乘其倒数。",
               qcategory="integer_div", exam_weight=3),
            nd("乘方", parent="有理数", summary="aⁿ 表示 n 个 a 相乘；注意 (-a)ⁿ 与 -aⁿ 区别。",
               qcategory="exponent_rule", exam_weight=3, errors=["混淆底数是否含负号"]),
            nd("科学记数法", parent="有理数", summary="a×10ⁿ（1≤|a|<10，n 为整数）表示大数。",
               qcategory="scientific_notation", exam_weight=2),
            # 整式加减
            nd("整式加减", type="chapter", summary="单项式与多项式的统称及运算。"),
            nd("单项式", parent="整式加减", summary="数与字母的积；单独一个数或字母也是单项式。",
               qcategory="integer_expr", exam_weight=2),
            nd("多项式", parent="整式加减", summary="几个单项式的和；次数取最高次项。",
               qcategory="integer_expr", exam_weight=2),
            nd("整式系数次数", parent="整式加减", summary="单项式系数与次数；多项式按次数排列。",
               qcategory="integer_expr", exam_weight=2),
            nd("合并同类项", parent="整式加减", summary="字母及指数相同的项可合并，系数相加。",
               qcategory="integer_expr", exam_weight=4, important=True,
               errors=["漏项", "系数相加时符号错"]),
            nd("去括号", parent="整式加减", summary="括号前负号时内层各项变号。",
               qcategory="integer_expr", exam_weight=3, errors=["负号漏变号"]),
            nd("整式加减运算", parent="整式加减", summary="先去括号再合并同类项。",
               qcategory="integer_expr", exam_weight=3),
            nd("代数式求值", parent="整式加减", summary="代入数值计算代数式的值。",
               qcategory="algebra_value", exam_weight=3, errors=["代入漏括号"]),
            nd("列代数式", parent="整式加减", summary="用字母表示数量关系。",
               qcategory="equation_basic", exam_weight=3),
            # 一元一次方程
            nd("一元一次方程", type="chapter", summary="含一个未知数且次数为1的整式方程。"),
            nd("方程概念", parent="一元一次方程", summary="含未知数的等式；使等式成立的值叫解。",
               qcategory="linear_equation", exam_weight=2),
            nd("等式性质", parent="一元一次方程", summary="等式两边同加/减/乘同一数仍相等。",
               qcategory="linear_equation", exam_weight=3),
            nd("移项", parent="一元一次方程", summary="把项从等号一边移到另一边要变号。",
               qcategory="linear_equation", exam_weight=4, errors=["移项不变号"]),
            nd("解一元一次方程", parent="一元一次方程", summary="去分母→去括号→移项→合并→系数化为1。",
               qcategory="linear_equation", exam_weight=5, important=True,
               errors=["移项不变号", "去分母漏乘常数项"]),
            nd("含参一元一次方程", parent="一元一次方程", summary="系数含字母，讨论解的存在性。",
               qcategory="linear_equation", exam_weight=3, errors=["忽略参数讨论"]),
            nd("一元一次方程应用", parent="一元一次方程", summary="审题→设元→列等量关系→求解。",
               qcategory="linear_equation", exam_weight=4, errors=["等量关系列错", "单位不统一"]),
            nd("工程问题", parent="一元一次方程", summary="工作量=效率×时间，合作问题求和。",
               qcategory="equation_app_work", exam_weight=4, errors=["效率和算错"]),
            nd("行程问题", parent="一元一次方程", summary="路程=速度×时间，相遇追及建模。",
               qcategory="linear_equation", exam_weight=4, errors=["等量关系列错"]),
            nd("利润问题", parent="一元一次方程", summary="利润=售价-进价，利润率建模。",
               qcategory="equation_app_mix", exam_weight=4, errors=["利润率公式错"]),
            nd("数字问题", parent="一元一次方程", summary="数位值表示与交换建模。",
               qcategory="equation_app_digit", exam_weight=3, errors=["数位表示错"]),
            # 几何图形初步
            nd("几何图形初步", type="chapter", summary="点、线、面、体及基本位置关系。"),
            nd("立体图形", parent="几何图形初步", summary="柱、锥、球等立体图形认识。",
               qcategory="geometry_basic", exam_weight=2),
            nd("平面图形", parent="几何图形初步", summary="线段、角、三角形等平面图形。",
               qcategory="geometry_basic", exam_weight=2),
            nd("点线面", parent="几何图形初步", summary="几何基本元素点、线、面、体。",
               qcategory="geometry_basic", exam_weight=1),
            nd("线段", parent="几何图形初步", summary="两点间线段最短；两点确定一条线段。",
               qcategory="geometry_basic", exam_weight=2),
            nd("射线", parent="几何图形初步", summary="有一个端点向一方无限延伸。",
               qcategory="geometry_basic", exam_weight=2),
            nd("直线", parent="几何图形初步", summary="无端点向两方无限延伸。",
               qcategory="geometry_basic", exam_weight=2),
            nd("线段长短比较", parent="几何图形初步", summary="度量法或叠合法比较线段。",
               qcategory="coord_distance", exam_weight=3),
            nd("线段中点", parent="几何图形初步", summary="中点分线段为相等两段。",
               qcategory="geometry_basic", exam_weight=3),
            nd("角", parent="几何图形初步", summary="有公共端点的两条射线组成角。",
               qcategory="angle_calc", exam_weight=3),
            nd("度分秒", parent="几何图形初步", summary="1°=60′，1′=60″；角度换算。",
               qcategory="angle_calc", exam_weight=3, errors=["进制换算错"]),
            nd("角的比较与运算", parent="几何图形初步", summary="角的和差倍分计算。",
               qcategory="angle_calc", exam_weight=3),
            nd("角平分线", parent="几何图形初步", summary="平分角的射线。",
               qcategory="angle_calc", exam_weight=3),
            nd("余角", parent="几何图形初步", summary="和为90°的两角互余。",
               qcategory="parallel_prop", exam_weight=3, errors=["混淆余补"]),
            nd("补角", parent="几何图形初步", summary="和为180°的两角互补。",
               qcategory="parallel_prop", exam_weight=3, errors=["混淆余补"]),
            nd("方位角", parent="几何图形初步", summary="以正北/正南为基准的方向角。",
               qcategory="coord_plane", exam_weight=2),
            # 数据统计初步
            nd("数据统计初步", type="chapter", summary="收集、整理、描述、分析数据。"),
            nd("数据收集", parent="数据统计初步", summary="全面调查与抽样调查。",
               qcategory="data_collect", exam_weight=3),
            nd("全面调查", parent="数据统计初步", summary="对全体对象调查。",
               qcategory="data_collect", exam_weight=2),
            nd("抽样调查", parent="数据统计初步", summary="抽取样本推断总体。",
               qcategory="data_collect", exam_weight=3, errors=["样本不具代表性"]),
            nd("条形统计图", parent="数据统计初步", summary="用条形高度表示数量。",
               qcategory="bar_chart", exam_weight=3),
            nd("折线统计图", parent="数据统计初步", summary="用折线反映变化趋势。",
               qcategory="line_chart", exam_weight=3),
            nd("扇形统计图", parent="数据统计初步", summary="用扇形面积表示占比。",
               qcategory="pie_chart", exam_weight=4, important=True, errors=["圆心角公式错"]),
            nd("频数", parent="数据统计初步", summary="数据中出现的次数。",
               qcategory="frequency", exam_weight=3),
            nd("频率", parent="数据统计初步", summary="频数/总数。",
               qcategory="frequency", exam_weight=4, errors=["与频数混淆"]),
            # 数学思想方法（枢纽节点）
            nd("数学思想方法", type="chapter", summary="贯穿中小学数学的核心思想方法。"),
            nd("方程思想", parent="数学思想方法", type="idea",
               summary="将未知转化为方程，用等量关系求解。",
               relations=["解一元一次方程", "一元一次方程应用", "工程问题", "行程问题",
                          "配方法", "公式法", "因式分解法", "分式方程", "二元一次方程组应用"]),
            nd("函数思想", parent="数学思想方法", type="idea",
               summary="用变量间的对应关系刻画变化规律。",
               relations=["变量与函数", "正比例函数", "一次函数", "二次函数", "反比例函数", "函数值"]),
            nd("数形结合思想", parent="数学思想方法", type="idea",
               summary="以形助数、以数解形，沟通代数与几何。",
               relations=["函数图像", "一次函数性质", "图像与性质", "顶点坐标",
                          "圆周角", "坐标系", "平面直角坐标系概念", "解直角三角形"]),
            nd("坐标系", parent="数学思想方法", type="idea",
               summary="用有序数对定位平面上的点。",
               relations=["点的坐标", "坐标与象限", "轴对称与坐标", "平面直角坐标系概念"]),
            nd("化归思想", parent="数学思想方法", type="idea",
               summary="将未知化归为已知，复杂化归为简单。",
               relations=["分式方程", "二次根式运算", "因式分解法", "配方法", "移项"]),
            nd("分类讨论思想", parent="数学思想方法", type="idea",
               summary="按参数或情况分门别类讨论。",
               relations=["绝对值", "含参一元一次方程", "三角形三边关系", "根的判别式"]),
        ],
    }


# ===========================================================================
# 八年级（苏科版）
# ===========================================================================
def grade8() -> dict:
    return {
        "subject": "数学", "grade": "八年级", "version": VERSION,
        "nodes": [
            # 二元一次方程组
            nd("二元一次方程组", type="chapter", summary="含两个未知数且次数为1的方程组。"),
            nd("二元一次方程组概念", parent="二元一次方程组", summary="两个一次方程组成的方程组。",
               qcategory="system_linear", exam_weight=3),
            nd("代入消元法", parent="二元一次方程组", summary="用一个未知数表示另一个后代入。",
               qcategory="system_linear", exam_weight=4, important=True, errors=["代入出错"]),
            nd("加减消元法", parent="二元一次方程组", summary="两式相加减消去一个未知数。",
               qcategory="system_linear", exam_weight=4, important=True, errors=["符号处理错"]),
            nd("二元一次方程组应用", parent="二元一次方程组", summary="设两个未知数列方程组求解。",
               qcategory="system_word", exam_weight=5, important=True,
               errors=["等量关系列错", "忽略隐藏条件"]),
            # 不等式与不等式组
            nd("不等式与不等式组", type="chapter", summary="用不等号表示数量关系。"),
            nd("不等式概念", parent="不等式与不等式组", summary="用<、>、≤、≥表示关系。",
               qcategory="inequality_solve", exam_weight=3),
            nd("不等式性质", parent="不等式与不等式组", summary="两边乘除负数时不等号方向改变。",
               qcategory="inequality_solve", exam_weight=4, important=True,
               errors=["乘负数未变号"]),
            nd("解一元一次不等式", parent="不等式与不等式组", summary="类似解方程，注意变号。",
               qcategory="inequality_solve", exam_weight=4, errors=["移项不变号"]),
            nd("一元一次不等式组", parent="不等式与不等式组", summary="多个不等式解集的公共部分。",
               qcategory="inequality_sys", exam_weight=4, errors=["取错公共部分"]),
            nd("不等式应用", parent="不等式与不等式组", summary="用不等式建模实际约束。",
               qcategory="inequality_app", exam_weight=4, errors=["等量关系列错"]),
            # 实数
            nd("实数", type="chapter", summary="有理数与无理数的统称。"),
            nd("平方根", parent="实数", summary="x²=a 则 x 是 a 的平方根。",
               qcategory="surd_simplify", exam_weight=4, important=True, errors=["漏写±", "与算术平方根混淆"]),
            nd("算术平方根", parent="实数", summary="非负平方根；√a≥0。",
               qcategory="surd_simplify", exam_weight=4, important=True, errors=["忽略非负性"]),
            nd("立方根", parent="实数", summary="x³=a 则 x 是 a 的立方根。",
               qcategory="surd_simplify", exam_weight=3),
            nd("无理数", parent="实数", summary="无限不循环小数（如π、√2）。",
               qcategory="real_number", exam_weight=3, errors=["误认无限小数为有理数"]),
            nd("实数运算", parent="实数", summary="实数范围内的四则运算。",
               qcategory="real_compare", exam_weight=3),
            nd("实数估算", parent="实数", summary="估计√a 介于哪两个相邻整数。",
               qcategory="real_estimate", exam_weight=3, errors=["估算区间错"]),
            # 平面直角坐标系
            nd("平面直角坐标系", type="chapter", summary="用有序数对表示平面内点的位置。"),
            nd("平面直角坐标系概念", parent="平面直角坐标系", summary="互相垂直的数轴构成坐标系。",
               qcategory="coord_plane", exam_weight=3),
            nd("点的坐标", parent="平面直角坐标系", summary="(x,y) 表示点的位置。",
               qcategory="coord_plane", exam_weight=4, important=True, errors=["横纵坐标为序错"]),
            nd("坐标与象限", parent="平面直角坐标系", summary="四个象限内坐标符号规律。",
               qcategory="coord_quadrant", exam_weight=4, errors=["象限符号错"]),
            nd("点到坐标轴距离", parent="平面直角坐标系", summary="点(x,y)到轴的距离为|x|或|y|。",
               qcategory="coord_distance", exam_weight=3),
            nd("轴对称与坐标", parent="平面直角坐标系", summary="关于坐标轴对称的点坐标规律。",
               qcategory="coord_sym", exam_weight=3, errors=["对称点坐标错"]),
            nd("平移与坐标", parent="平面直角坐标系", summary="平移改变坐标的加减规律。",
               qcategory="coord_distance", exam_weight=3),
            # 三角形
            nd("三角形", type="chapter", summary="由三条线段围成的图形。"),
            nd("三角形概念", parent="三角形", summary="三条线段首尾顺次相接。",
               qcategory="triangle_classify", exam_weight=2),
            nd("三角形三边关系", parent="三角形", summary="两边和大于第三边，差小于第三边。",
               qcategory="triangle_basic", exam_weight=4, important=True,
               errors=["忽略三边关系", "分类讨论遗漏"]),
            nd("三角形内角和", parent="三角形", summary="三角形内角和为180°。",
               qcategory="angle_calc", exam_weight=4, important=True, errors=["内角和记错"]),
            nd("三角形外角", parent="三角形", summary="外角等于不相邻两内角和。",
               qcategory="angle_calc", exam_weight=3, errors=["外角定理记错"]),
            nd("三角形周长", parent="三角形", summary="三边长度之和。",
               qcategory="quad_perimeter", exam_weight=3),
            nd("多边形", parent="三角形", summary="由多条线段围成的封闭图形。",
               qcategory="polygon_angle", exam_weight=3),
            nd("多边形内角和", parent="三角形", summary="(n-2)×180°。",
               qcategory="polygon_angle", exam_weight=4, important=True, errors=["公式记错"]),
            # 全等三角形
            nd("全等三角形", type="chapter", summary="能够完全重合的两个三角形。"),
            nd("全等概念", parent="全等三角形", summary="形状大小完全相同，对应边角相等。",
               qcategory="congruent_app", exam_weight=3),
            nd("SSS判定", parent="全等三角形", summary="三边对应相等则全等。",
               qcategory="congruent_sss", exam_weight=4, important=True, errors=["判定条件记混"]),
            nd("SAS判定", parent="全等三角形", summary="两边及其夹角对应相等则全等。",
               qcategory="congruent_sas", exam_weight=4, important=True, errors=["夹角对应错"]),
            nd("ASA判定", parent="全等三角形", summary="两角及夹边对应相等则全等。",
               qcategory="congruent_sas", exam_weight=4, errors=["条件用错"]),
            nd("AAS判定", parent="全等三角形", summary="两角及一角的对边对应相等则全等。",
               qcategory="congruent_sas", exam_weight=3),
            nd("HL判定", parent="全等三角形", summary="直角三角形斜边直角边对应相等则全等。",
               qcategory="congruent_sss", exam_weight=4, errors=["仅用于直角"]),
            nd("角平分线性质", parent="全等三角形", summary="角平分线上的点到两边距离相等。",
               qcategory="congruent_app", exam_weight=4, important=True, errors=["性质逆用错"]),
            # 轴对称
            nd("轴对称", type="chapter", summary="沿对称轴折叠重合。"),
            nd("轴对称概念", parent="轴对称", summary="对应点连线被对称轴垂直平分。",
               qcategory="axisymmetry", exam_weight=2),
            nd("轴对称图形", parent="轴对称", summary="沿一条直线折叠能重合的图形。",
               qcategory="axisymmetry", exam_weight=3),
            nd("等腰三角形", parent="轴对称", summary="等边对等角；三线合一。",
               qcategory="axisymmetry", exam_weight=4, important=True, errors=["忽视三线合一条件"]),
            nd("等边三角形", parent="轴对称", summary="三边相等，三角均为60°。",
               qcategory="triangle_classify", exam_weight=4, errors=["性质混淆"]),
            nd("线段垂直平分线", parent="轴对称", summary="垂直平分线上的点到两端距离相等。",
               qcategory="circle_chord", exam_weight=3),
            # 整式乘除与因式分解
            nd("整式乘除与因式分解", type="chapter", summary="幂运算、乘法公式与因式分解。"),
            nd("同底数幂乘法", parent="整式乘除与因式分解", summary="aᵐ·aⁿ=aᵐ⁺ⁿ。",
               qcategory="monomial_pow", exam_weight=3, errors=["指数相加错"]),
            nd("幂的乘方", parent="整式乘除与因式分解", summary="(aᵐ)ⁿ=aᵐⁿ。",
               qcategory="monomial_pow", exam_weight=3, errors=["指数相乘错"]),
            nd("积的乘方", parent="整式乘除与因式分解", summary="(ab)ⁿ=aⁿbⁿ。",
               qcategory="monomial_pow", exam_weight=3, errors=["漏给每项乘方"]),
            nd("整式乘法", parent="整式乘除与因式分解", summary="单项式×多项式、多项式×多项式。",
               qcategory="poly_mult", exam_weight=4, important=True, errors=["漏乘", "符号错"]),
            nd("乘法公式", parent="整式乘除与因式分解", summary="平方差与完全平方。",
               qcategory="poly_mult", exam_weight=5, important=True,
               formula=["(a+b)(a-b)=a²-b²", "(a±b)²=a²±2ab+b²"],
               errors=["公式记错", "漏掉2ab项"]),
            nd("提公因式法", parent="整式乘除与因式分解", summary="提取各项公共因式。",
               qcategory="factor_common", exam_weight=4, errors=["公因式提取不全"]),
            nd("公式法因式分解", parent="整式乘除与因式分解", summary="用平方差/完全平方公式分解。",
               qcategory="factor_formula", exam_weight=4, important=True, errors=["公式用反"]),
            nd("十字相乘法", parent="整式乘除与因式分解", summary="x²+(p+q)x+pq分解。",
               qcategory="factor_cross", exam_weight=4, errors=["交叉项凑错"]),
            nd("分组分解法", parent="整式乘除与因式分解", summary="分组后提取公因式或公式。",
               qcategory="factor_group", exam_weight=3, errors=["分组不当"]),
            # 分式
            nd("分式", type="chapter", summary="形如 A/B（B含字母且B≠0）的式子。"),
            nd("分式概念", parent="分式", summary="分母含字母且不为0；值为0需分子0且分母非0。",
               qcategory="fraction", exam_weight=3, errors=["忽略分母不为0"]),
            nd("分式基本性质", parent="分式", summary="分子分母同乘(除)同一非零式，值不变。",
               qcategory="fraction", exam_weight=3),
            nd("分式乘除", parent="分式", summary="约分、乘除法法则。",
               qcategory="fraction_mult", exam_weight=4, important=True, errors=["约分遗漏", "未乘倒数"]),
            nd("分式加减", parent="分式", summary="通分后加减。",
               qcategory="fraction_div", exam_weight=4, errors=["通分找错公分母"]),
            nd("分式方程", parent="分式", summary="分母含未知数的方程，需验根。",
               qcategory="fraction", exam_weight=4, important=True, errors=["忘验增根", "忽略分母不为0"]),
            # 二次根式
            nd("二次根式", type="chapter", summary="形如 √a (a≥0) 的式子。"),
            nd("二次根式概念", parent="二次根式", summary="被开方数非负；√a≥0。",
               qcategory="surd_simplify", exam_weight=3, errors=["忽略 a≥0"]),
            nd("二次根式性质", parent="二次根式", summary="√(a²)=|a|；(√a)²=a。",
               qcategory="surd_mixed", exam_weight=4, important=True, errors=["忘记绝对值"]),
            nd("二次根式乘除", parent="二次根式", summary="√a·√b=√(ab)；√a/√b=√(a/b)。",
               qcategory="surd_op", exam_weight=4, errors=["忽略定义域"]),
            nd("二次根式加减", parent="二次根式", summary="化为最简后合并同类二次根式。",
               qcategory="surd_op", exam_weight=3, errors=["未化最简"]),
            nd("分母有理化", parent="二次根式", summary="分子分母同乘有理化因式。",
               qcategory="surd_rationalize", exam_weight=3, errors=["有理化因式错"]),
            # 勾股定理
            nd("勾股定理", type="chapter", summary="直角三角形三边关系：a²+b²=c²。",
               formula=["a² + b² = c²"], important=True, exam_weight=5,
               errors=["斜边直角边混淆"], qcategory="pythagoras"),
            nd("勾股定理逆定理", parent="勾股定理", summary="若 a²+b²=c² 则三角形为直角三角形。",
               qcategory="pythagoras", exam_weight=4, errors=["未先排序三边"]),
            nd("勾股定理应用", parent="勾股定理", summary="求边长、证明直角、实际问题。",
               qcategory="pythagoras", exam_weight=5, important=True, errors=["列方程错"]),
            # 一次函数
            nd("函数", type="chapter", summary="变量间单值对应关系；定义域与值域。"),
            nd("变量与函数", parent="函数", summary="一个x确定唯一y，则y是x的函数。",
               qcategory="linear_function_def", exam_weight=3),
            nd("函数值", parent="函数", summary="给定自变量求对应的函数值。",
               qcategory="function_value", exam_weight=3, errors=["代入计算错"]),
            nd("正比例函数", parent="函数", summary="形如 y=kx(k≠0) 的函数，过原点。",
               formula=["y = kx (k≠0)"], important=True, successor=["一次函数"],
               qcategory="linear_function_def", exam_weight=4,
               errors=["忽略 k≠0", "误认为必过一二象限"]),
            nd("一次函数", parent="函数", summary="形如 y=kx+b(k≠0) 的函数。",
               formula=["y = kx + b (k≠0)"], important=True,
               predecessor=["正比例函数"], successor=["二次函数"],
               exam_weight=5, errors=["忽略 k 符号", "不会判断增减性"],
               qcategory="linear_function_def"),
            nd("一次函数定义", parent="一次函数", summary="识别 y=kx+b(k≠0) 形式。",
               qcategory="linear_function_def", exam_weight=4, errors=["与正比例函数混淆"]),
            nd("函数图像", parent="一次函数",
               summary="一次函数图像是一条直线；k 决定增减性与倾斜，b 决定与 y 轴交点。",
               formula=["直线斜率 k", "截距 b"], important=True, exam_weight=5,
               errors=["混淆 k、b 对图像的影响", "象限判断错"], qcategory="linear_function_image"),
            nd("一次函数性质", parent="一次函数", summary="k>0 时 y 随 x 增大而增大；k<0 时减小。",
               qcategory="linear_function_prop", exam_weight=5, important=True, errors=["增减性符号反"]),
            nd("一次函数解析式求解", parent="一次函数", summary="由已知点或条件求 k、b。",
               qcategory="linear_function_solve", exam_weight=4, errors=["代入计算错", "方程组求解错"]),
            nd("一次函数图像平移", parent="一次函数", summary="平移不改变 k，仅改变 b（截距）。",
               qcategory="linear_function_translate", exam_weight=4, errors=["平移方向混淆", "截距变化算错"]),
            nd("一次函数两直线关系", parent="一次函数", summary="平行(k等b异)/垂直(k积-1)/相交。",
               qcategory="linear_function_twolines", exam_weight=4, errors=["垂直条件记错(k₁k₂=-1)"]),
            nd("一次函数实际应用", parent="一次函数", summary="方案决策、行程、计费等问题建模。",
               qcategory="linear_function_application", exam_weight=5, important=True,
               errors=["等量关系列错", "忽略隐藏条件(超出部分计费)"]),
            nd("一次函数综合", parent="一次函数", summary="与面积、坐标系综合的压轴题型。",
               qcategory="linear_function_composite", exam_weight=5, errors=["几何与代数结合错"]),
            nd("待定系数法", parent="一次函数", summary="设函数式，代入点求待定系数。",
               qcategory="linear_param", exam_weight=4, important=True, errors=["代入出错"]),
            # 四边形
            nd("四边形", type="chapter", summary="多边形；特殊四边形性质与判定。"),
            nd("平行四边形", parent="四边形", summary="对边平行且相等，对角线互相平分。",
               qcategory="quadrilateral", exam_weight=4, important=True, errors=["判定条件记混"]),
            nd("平行四边形性质", parent="四边形", summary="对边平行相等、对角相等、对角线平分。",
               qcategory="quadrilateral", exam_weight=4),
            nd("矩形", parent="四边形", summary="有一个直角的平行四边形；对角线相等。",
               qcategory="rect_prop", exam_weight=4, important=True, errors=["性质混淆"]),
            nd("菱形", parent="四边形", summary="邻边相等的平行四边形；对角线垂直平分。",
               qcategory="rhombus_prop", exam_weight=4, important=True, errors=["面积算错"]),
            nd("正方形", parent="四边形", summary="既是矩形又是菱形的四边形。",
               qcategory="square_prop", exam_weight=3, errors=["性质混淆"]),
            nd("梯形", parent="四边形", summary="一组对边平行另一组不平行的四边形。",
               qcategory="trap_area", exam_weight=2),
            nd("梯形面积", parent="四边形", summary="S=(a+b)h/2。",
               qcategory="trap_area", exam_weight=4, formula=["S = (a+b)h/2"], errors=["公式错"]),
            nd("三角形中位线", parent="四边形", summary="中位线平行第三边且等于一半。",
               qcategory="midpoint_conn", exam_weight=4, important=True, errors=["定理记错"]),
            # 数据的分析
            nd("数据的分析", type="chapter", summary="用统计量描述数据特征。"),
            nd("平均数", parent="数据的分析", summary="一组数据和除以个数。",
               qcategory="statistics", exam_weight=3),
            nd("加权平均数", parent="数据的分析", summary="各数据乘权后求和再除以权和。",
               qcategory="weighted_mean", exam_weight=4, important=True, errors=["权算错"]),
            nd("中位数", parent="数据的分析", summary="数据排序后中间位置的数。",
               qcategory="median_calc", exam_weight=3, errors=["未排序"]),
            nd("众数", parent="数据的分析", summary="出现次数最多的数据。",
               qcategory="mode_calc", exam_weight=3),
            nd("方差", parent="数据的分析", summary="衡量数据波动；越小越稳定。",
               qcategory="stat_variance", exam_weight=4, important=True, errors=["混淆方差与平均数意义"]),
            nd("频数分布表", parent="数据的分析", summary="列出各组频数。",
               qcategory="frequency", exam_weight=3),
            nd("频数分布直方图", parent="数据的分析", summary="用长方形高表示频数/组距。",
               qcategory="histogram", exam_weight=4, errors=["纵轴含义错"]),
        ],
    }


# ===========================================================================
# 九年级（苏科版）
# ===========================================================================
def grade9() -> dict:
    return {
        "subject": "数学", "grade": "九年级", "version": VERSION,
        "nodes": [
            # 一元二次方程
            nd("一元二次方程", type="chapter", summary="ax²+bx+c=0(a≠0)。"),
            nd("一元二次方程概念", parent="一元二次方程", summary="只含一个未知数且最高次为2。",
               qcategory="quadratic_equation", exam_weight=2),
            nd("直接开平方法", parent="一元二次方程", summary="x²=m 则 x=±√m。",
               qcategory="quadratic_equation", exam_weight=3),
            nd("配方法", parent="一元二次方程", summary="移项→配方→开平方。",
               qcategory="quadratic_equation", exam_weight=4),
            nd("公式法", parent="一元二次方程", summary="x=[-b±√(b²-4ac)]/(2a)。",
               formula=["x = (-b ± √(b²-4ac)) / (2a)"], important=True,
               qcategory="quadratic_equation", exam_weight=5, errors=["漏写 2a 分母", "判别式算错"]),
            nd("因式分解法", parent="一元二次方程", summary="化为 (x-p)(x-q)=0。",
               qcategory="quadratic_equation", exam_weight=4),
            nd("根的判别式", parent="一元二次方程", summary="Δ=b²-4ac 决定实根个数。",
               qcategory="quadratic_equation", exam_weight=4, important=True, errors=["符号写反"]),
            nd("根的判别式应用", parent="一元二次方程", summary="由Δ判断根的存在与个数。",
               qcategory="quad_word", exam_weight=4, errors=["Δ符号判断错"]),
            nd("韦达定理", parent="一元二次方程", summary="x₁+x₂=-b/a，x₁x₂=c/a。",
               formula=["x₁+x₂ = -b/a", "x₁x₂ = c/a"], important=True,
               qcategory="vieta", exam_weight=4, errors=["符号写反"]),
            nd("一元二次方程应用", parent="一元二次方程", summary="面积、传播、增长率等建模。",
               qcategory="quad_word", exam_weight=5, important=True, errors=["建模列错关系式"]),
            # 二次函数
            nd("二次函数", type="chapter", summary="y=ax²+bx+c(a≠0)。",
               predecessor=["一次函数"]),
            nd("二次函数概念", parent="二次函数", summary="最高次为2；图像是抛物线。",
               qcategory="quadratic_function", exam_weight=3),
            nd("图像与性质", parent="二次函数", summary="a>0 开口向上；对称轴 x=-b/2a。",
               qcategory="quadratic_function", exam_weight=5, important=True, errors=["a 符号与开口混淆"]),
            nd("顶点坐标", parent="二次函数", summary="顶点(-b/2a, (4ac-b²)/4a)。",
               formula=["x = -b/(2a)", "y = (4ac-b²)/(4a)"],
               qcategory="quadratic_function_vertex", exam_weight=5, errors=["坐标符号错"]),
            nd("对称轴", parent="二次函数", summary="直线 x=-b/2a。",
               qcategory="quadratic_function", exam_weight=4),
            nd("二次函数应用", parent="二次函数", summary="面积最值、抛物线建模等实际问题。",
               qcategory="quad_func_app", exam_weight=5, important=True, errors=["建模列错关系式"]),
            nd("二次函数与方程", parent="二次函数", summary="函数值定点对应方程根。",
               qcategory="quad_intersect", exam_weight=4, errors=["交点数判错"]),
            nd("二次函数与不等式", parent="二次函数", summary="由图像解 ax²+bx+c>0。",
               qcategory="func_comprehensive", exam_weight=4, errors=["符号区间错"]),
            # 旋转
            nd("旋转", type="chapter", summary="图形绕定点转动。"),
            nd("旋转概念", parent="旋转", summary="绕定点按方向转动一定角度。",
               qcategory="rotation_prop", exam_weight=3),
            nd("旋转性质", parent="旋转", summary="对应点到旋转中心距离相等、角等于转角。",
               qcategory="rotation_prop", exam_weight=4, important=True, errors=["性质记错"]),
            nd("中心对称", parent="旋转", summary="绕点旋转180°重合。",
               qcategory="symmetry_center", exam_weight=4, errors=["与轴对称混淆"]),
            nd("中心对称图形", parent="旋转", summary="绕对称中心旋转180°重合。",
               qcategory="symmetry_center", exam_weight=3),
            nd("平移变换", parent="旋转", summary="图形沿方向移动不改变形状大小。",
               qcategory="translation_geom", exam_weight=3, errors=["误以为改变大小"]),
            # 圆
            nd("圆", type="chapter", summary="到定点距离等于定长的点的集合。"),
            nd("圆的基本概念", parent="圆", summary="半径、直径、弦、弧、圆心角。",
               qcategory="circle", exam_weight=3),
            nd("圆周角", parent="圆", summary="圆周角等于所对圆心角的一半。",
               qcategory="circle_chord", exam_weight=4, important=True, errors=["定理记反"]),
            nd("弧长和扇形面积", parent="圆", summary="l=nπr/180；S=nπr²/360。",
               formula=["l = nπr/180", "S = nπr²/360"],
               qcategory="circle", exam_weight=4, errors=["角度与弧度混淆"]),
            nd("直线与圆位置关系", parent="圆", summary="相离、相切(d=r)、相交。",
               qcategory="circle_position", exam_weight=4, errors=["d 与 r 比较错"]),
            nd("切线", parent="圆", summary="切线垂直于过切点的半径；切线长定理。",
               qcategory="circle_tangent_prop", exam_weight=4, important=True, errors=["忽略垂直关系"]),
            nd("切线长定理", parent="圆", summary="从圆外一点引两条切线，切线长相等。",
               qcategory="circle_tangent_prop", exam_weight=4, errors=["定理误用"]),
            nd("内切圆", parent="圆", summary="与三角形三边都相切的圆。",
               qcategory="circle_inscribed", exam_weight=3, errors=["半径与边关系错"]),
            nd("外接圆", parent="圆", summary="过三角形三顶点的圆。",
               qcategory="circle_chord", exam_weight=3),
            # 概率初步
            nd("概率初步", type="chapter", summary="随机事件与概率。"),
            nd("随机事件", parent="概率初步", summary="必然、不可能、随机事件。",
               qcategory="probability", exam_weight=2),
            nd("概率", parent="概率初步", summary="P=有利结果数/总结果数。",
               formula=["P = m / n"], important=True,
               qcategory="probability", exam_weight=4, errors=["分母算错"]),
            nd("树状图", parent="概率初步", summary="列举两步及以上所有等可能结果。",
               qcategory="prob_tree", exam_weight=4, errors=["遗漏等可能结果"]),
            nd("概率加法", parent="概率初步", summary="互斥事件概率相加。",
               qcategory="prob_add", exam_weight=4, errors=["非互斥也相加"]),
            nd("不放回组合概率", parent="概率初步", summary="不放回抽样的概率计算。",
               qcategory="prob_combo", exam_weight=4, errors=["未乘倒数", "顺序错"]),
            nd("几何概型", parent="概率初步", summary="用面积比求概率。",
               qcategory="geometric_prob", exam_weight=4, errors=["模型列错"]),
            # 相似
            nd("相似图形", type="chapter", summary="形状相同大小不同的图形。"),
            nd("相似三角形", parent="相似图形", summary="对应角相等，对应边成比例。",
               qcategory="similar", exam_weight=5, important=True, errors=["对应边的比写反"]),
            nd("相似判定", parent="相似图形", summary="AA / SAS / SSS 三种判定。",
               qcategory="similar", exam_weight=5, important=True, errors=["判定条件用错"]),
            nd("相似性质", parent="相似图形", summary="周长比=相似比，面积比=相似比平方。",
               qcategory="similar_ratio_app", exam_weight=4, errors=["面积比记错"]),
            nd("相似应用", parent="相似图形", summary="测高、影子、实际比例问题。",
               qcategory="similarity_app", exam_weight=4, important=True, errors=["对应边比写反"]),
            nd("位似", parent="相似图形", summary="特殊相似，对应点连线过同一点。",
               qcategory="similar", exam_weight=2),
            # 锐角三角函数
            nd("锐角三角函数", type="chapter", summary="直角三角形中边角关系。"),
            nd("锐角三角函数概念", parent="锐角三角函数", summary="sin/cos/tan 的定义。",
               qcategory="trig_sin", exam_weight=4, important=True, errors=["邻边对边混淆"]),
            nd("特殊角三角函数", parent="锐角三角函数", summary="30°/45°/60° 的三角函数值。",
               formula=["sin30=1/2", "cos30=√3/2", "tan30=√3/3"],
               qcategory="trig_special", exam_weight=4, important=True, errors=["值记错"]),
            nd("解直角三角形", parent="锐角三角函数", summary="由已知边角求其余边角。",
               qcategory="trig_app", exam_weight=5, important=True, errors=["图形理解偏差", "模型列错"]),
            nd("仰角与俯角", parent="锐角三角函数", summary="视线与水平线的夹角。",
               qcategory="trig_app", exam_weight=4, errors=["仰俯角混淆"]),
            # 投影与视图
            nd("投影与视图", type="chapter", summary="平行投影与三视图。"),
            nd("平行投影", parent="投影与视图", summary="平行光线下物体的投影。",
               qcategory="projection_view", exam_weight=2),
            nd("中心投影", parent="投影与视图", summary="点光源下物体的投影。",
               qcategory="projection_view", exam_weight=2),
            nd("三视图", parent="投影与视图", summary="主视、俯视、左视表达几何体。",
               qcategory="projection_view", exam_weight=4, important=True, errors=["视图对应错"]),
            # 反比例函数
            nd("反比例函数", type="chapter", summary="y=k/x (k≠0)。"),
            nd("反比例函数概念", parent="反比例函数", summary="y=k/x(k≠0)，k≠0。",
               qcategory="inverse_var", exam_weight=4, important=True, errors=["忽略 k≠0", "忽略分母不为0"]),
            nd("反比例函数性质", parent="反比例函数", summary="k>0 在一三象限，k<0 在二四象限。",
               qcategory="inverse_var", exam_weight=4, errors=["象限判断错"]),
            nd("反比例函数应用", parent="反比例函数", summary="面积、行程等反比例建模。",
               qcategory="inverse_var_app", exam_weight=5, important=True, errors=["模型列错"]),
            # 综合与实践
            nd("综合与实践", type="chapter", summary="跨章节综合与数学活动。"),
            nd("规律探索", parent="综合与实践", summary="数列、图形规律归纳。",
               qcategory="pattern_explore", exam_weight=4, errors=["审题不清", "规律找错"]),
            nd("方案决策", parent="综合与实践", summary="用方程/函数比较方案优劣。",
               qcategory="system_word", exam_weight=5, important=True, errors=["模型列错"]),
            nd("年龄问题", parent="综合与实践", summary="用年龄差不变列方程组。",
               qcategory="equation_app_age", exam_weight=3, errors=["年龄差算错"]),
            nd("浓度问题", parent="综合与实践", summary="溶质/溶液/浓度关系建模。",
               qcategory="equation_app_mix", exam_weight=4, errors=["浓度公式错"]),
            nd("利润最值", parent="综合与实践", summary="用二次函数求最大利润。",
               qcategory="quad_func_app", exam_weight=4, errors=["建模列错"]),
            nd("命题与证明", parent="综合与实践", summary="判断命题真假与简单推理。",
               qcategory="logic_proof", exam_weight=3, errors=["真假判断错"]),
        ],
    }


# ===========================================================================
# 小学数学（一至六，基础层，不展开 fanout）
# ===========================================================================
def _primary_grade(grade: str, nodes: list) -> dict:
    return {"subject": "数学", "grade": grade, "version": "苏教版", "nodes": nodes}


def primary() -> dict:
    out = {}
    out["一年级"] = _primary_grade("一年级", [
        nd("认识数字0-10", type="chapter", summary="认、读、写 0-10。"),
        nd("比大小", parent="认识数字0-10", qcategory="arithmetic", exam_weight=2,
           summary="用 > < = 比较。", errors=["符号方向反"]),
        nd("5以内加减", parent="认识数字0-10", qcategory="arithmetic", exam_weight=3),
        nd("10以内加减", parent="认识数字0-10", qcategory="arithmetic", exam_weight=3),
        nd("认识钟表", type="chapter", summary="整点与半点。"),
        nd("认读整点", parent="认识钟表", qcategory="arithmetic", exam_weight=2),
    ])
    out["二年级"] = _primary_grade("二年级", [
        nd("100以内加减", type="chapter", summary="进退位加减法。"),
        nd("100以内进位加", parent="100以内加减", qcategory="integer_mult", exam_weight=3,
           errors=["进位漏加"]),
        nd("100以内退位减", parent="100以内加减", qcategory="integer_add_sub", exam_weight=3,
           errors=["退位漏减"]),
        nd("表内乘法", type="chapter", summary="乘法口诀。"),
        nd("2-5乘法口诀", parent="表内乘法", qcategory="arithmetic", exam_weight=4, important=True),
        nd("6-9乘法口诀", parent="表内乘法", qcategory="arithmetic", exam_weight=4, important=True,
           errors=["口诀记错"]),
        nd("表内除法", type="chapter", summary="平均分与包含除。"),
        nd("用乘法口诀求商", parent="表内除法", qcategory="integer_div", exam_weight=4),
    ])
    out["三年级"] = _primary_grade("三年级", [
        nd("万以内加减", type="chapter", summary="连续进退位。"),
        nd("万以内进位加", parent="万以内加减", qcategory="integer_add_sub", exam_weight=3),
        nd("万以内退位减", parent="万以内加减", qcategory="integer_add_sub", exam_weight=3),
        nd("倍的认识", type="chapter", summary="一个数是另一个的几倍。"),
        nd("求倍数", parent="倍的认识", qcategory="arithmetic", exam_weight=3, errors=["乘除混淆"]),
        nd("多位数乘一位数", type="chapter", summary="竖式计算。"),
        nd("笔算乘法", parent="多位数乘一位数", qcategory="integer_mult", exam_weight=4,
           errors=["进位忘加"]),
        nd("长方形正方形周长", type="chapter", summary="长方形周长=2(a+b)；正方形=4a。",
           formula=["C = 2(a+b)", "C = 4a"], qcategory="geometry_basic", exam_weight=4, important=True),
        nd("分数初步", type="chapter", summary="整体平均分成若干份取一份。"),
        nd("认识分数", parent="分数初步", qcategory="fraction_basic", exam_weight=3,
           errors=["分母分子意义反"]),
        nd("分数加减", parent="分数初步", qcategory="fraction_basic", exam_weight=3, errors=["未通分"]),
    ])
    out["四年级"] = _primary_grade("四年级", [
        nd("大数的认识", type="chapter", summary="万以上计数单位与读写。"),
        nd("亿以内读写", parent="大数的认识", qcategory="arithmetic", exam_weight=3),
        nd("三位数乘两位数", type="chapter", summary="竖式与估算。"),
        nd("笔算乘法", parent="三位数乘两位数", qcategory="integer_mult", exam_weight=4),
        nd("除数是两位数除法", type="chapter", summary="试商与调商。"),
        nd("笔算除法", parent="除数是两位数除法", qcategory="integer_div", exam_weight=4,
           errors=["试商偏大偏小"]),
        nd("运算定律", type="chapter", summary="加法/乘法交换律、结合律、分配律。"),
        nd("乘法分配律", parent="运算定律", qcategory="poly_mult", exam_weight=5, important=True,
           formula=["a(b+c)=ab+ac"], errors=["漏乘"]),
        nd("平行四边形梯形面积", type="chapter", summary="平行四边形 S=ah；梯形 S=(a+b)h/2。",
           formula=["S = ah", "S = (a+b)h/2"], qcategory="trap_area", exam_weight=5, important=True),
        nd("小数意义", type="chapter", summary="分母为10/100/1000的分数。"),
        nd("小数读写与比较", parent="小数意义", qcategory="decimal", exam_weight=3,
           errors=["小数大小比较错"]),
        nd("小数加减", parent="小数意义", qcategory="decimal", exam_weight=3),
    ])
    out["五年级"] = _primary_grade("五年级", [
        nd("小数乘除", type="chapter", summary="点小数点位置。"),
        nd("小数乘法", parent="小数乘除", qcategory="decimal_mult", exam_weight=4,
           errors=["小数点位数错"]),
        nd("小数除法", parent="小数乘除", qcategory="decimal_div", exam_weight=4),
        nd("简易方程", type="chapter", summary="用字母表示数与等量关系。"),
        nd("用字母表示数", parent="简易方程", qcategory="equation_basic", exam_weight=4, important=True),
        nd("解简易方程", parent="简易方程", qcategory="equation_basic", exam_weight=4, errors=["移项不变号"]),
        nd("多边形面积", type="chapter", summary="三角形 S=ah/2；组合图形分割。",
           formula=["S = ah/2"], qcategory="geometry_basic", exam_weight=5, important=True),
        nd("因数与倍数", type="chapter", summary="整除关系与质数合数。"),
        nd("质数合数", parent="因数与倍数", qcategory="factor_multiple", exam_weight=3, errors=["1不是质数"]),
        nd("分数乘除", type="chapter", summary="分子乘分子、分母乘分母；除以=乘倒数。"),
        nd("分数乘法", parent="分数乘除", qcategory="fraction_mult", exam_weight=4, errors=["约分遗漏"]),
        nd("分数除法", parent="分数乘除", qcategory="fraction_div", exam_weight=4, errors=["未乘倒数"]),
    ])
    out["六年级"] = _primary_grade("六年级", [
        nd("比和比例", type="chapter", summary="a:b 与比值；正比例与反比例。"),
        nd("正比例", parent="比和比例", qcategory="linear_function_prop", exam_weight=4, errors=["正反例混淆"]),
        nd("反比例", parent="比和比例", qcategory="linear_function_prop", exam_weight=4, errors=["正反例混淆"]),
        nd("比例应用", parent="比和比例", qcategory="ratio_prop", exam_weight=4, errors=["比例设错"]),
        nd("圆周长面积", type="chapter", summary="C=2πr；S=πr²。",
           formula=["C = 2πr", "S = πr²"], qcategory="geometry_basic", exam_weight=5, important=True),
        nd("百分数", type="chapter", summary="分母是100的分数；折扣、利率。"),
        nd("百分数应用", parent="百分数", qcategory="percent_app", exam_weight=4, errors=["单位1不清"]),
        nd("圆柱圆锥体积", type="chapter", summary="圆柱 V=πr²h；圆锥 V=1/3πr²h。",
           formula=["V柱 = πr²h", "V锥 = ⅓πr²h"], qcategory="geometry_volume", exam_weight=4,
           errors=["圆锥漏 1/3"]),
        nd("扇形统计", type="chapter", summary="扇形图表示占比。"),
        nd("读扇形图", parent="扇形统计", qcategory="pie_chart", exam_weight=3),
    ])
    return out


def _fanout(data: dict) -> dict:
    """受控粒度扩展：对叶子知识点（有 qcategory 且无子节点）追加面状子节点，
    提高知识图谱密度与掌握度追踪精度。子节点继承父 qcategory。
    仅对初中(middle)树展开，以把初中知识图谱推至 ~1200 节点。"""
    nodes = data["nodes"]
    has_child = {n["parent"] for n in nodes if "parent" in n}
    extra = []
    for n in nodes:
        if n.get("qcategory") and n["name"] not in has_child:
            for f in FACETS:
                extra.append(nd(
                    f"{n['name']}{f}", parent=n["name"],
                    summary=f"{n['name']}的{f[1:]}训练。",
                    qcategory=n.get("qcategory"),
                    exam_weight=n.get("exam_weight", 1),
                ))
    data["nodes"].extend(extra)
    return data


def main() -> None:
    root = cfg.PROJECT_ROOT / "resource" / "knowledge"
    (root / "middle_math").mkdir(parents=True, exist_ok=True)
    (root / "primary_math").mkdir(parents=True, exist_ok=True)

    middle = {"七年级": grade7(), "八年级": grade8(), "九年级": grade9()}
    for g, data in middle.items():
        data = _fanout(data)  # 初中做面状展开（5×）以提升图谱密度至 ~1200
        p = root / "middle_math" / f"grade{cfg.GRADE_LEVEL[g]}.json"
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        leaf = sum(1 for n in data["nodes"] if n.get("qcategory") and n["name"] not in has_child_of(data))
        print(f"write {p}  nodes={len(data['nodes'])}")

    for g, data in primary().items():
        p = root / "primary_math" / f"grade{cfg.GRADE_LEVEL[g]}.json"
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"write {p}  nodes={len(data['nodes'])}")


def has_child_of(data: dict) -> set:
    return {n["parent"] for n in data["nodes"] if "parent" in n}


if __name__ == "__main__":
    main()
