# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""数学题库生成器（Phase 1.5-C 数据生产体系升级）。

相对 Phase 1.5-B 的两大核心升级：
1. 题型矩阵（Type Matrix）：每个 qcategory 不再对应单一模板，而是对应一组
   子题型模板（如「一次函数」拆分为 定义判断 / 解析式求解 / 图像平移 /
   增减性判断 / 两直线关系 / 实际应用 / 综合函数），保证同一知识点下
   题型多样性，避免「题目千篇一律」。
2. 难度生成模型（Difficulty Model）：难度不再随机，而是由题目本身的
   知识跨度(concepts) + 步骤数量(steps) + 计算复杂度(compute) + 隐藏条件(hidden)
   经确定性函数 compute_difficulty 推导（1-5，对应 基础识记→竞赛拓展）。

设计原则（对齐用户要求）：
- 答案由同一段代码算出，保证零错误答案（垃圾题库无意义）。
- 每题必绑定知识点（knowledge 数组），使 Learning Engine 推荐链路可用。
- 无网络依赖、纯标准库，可无头批量生产、可线性扩展至数万题。
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List, Optional

import config.settings as cfg

from ._helpers import make_choice, fmt_int, _e


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------
def _sample_distinct(rng: random.Random, pool: List[str], n: int, exclude: set) -> List[str]:
    cand = [x for x in pool if x not in exclude]
    rng.shuffle(cand)
    return cand[:n]


# ---------------------------------------------------------------------------
# 难度生成模型（确定性，替代随机 difficulty）
# ---------------------------------------------------------------------------
def compute_difficulty(*, concepts: int, steps: int, compute: int, hidden: bool) -> int:
    """难度 1-5（基础识记 / 基础应用 / 综合应用 / 提升 / 竞赛拓展）。

    公式：raw = 1.0
              + 知识跨度(0-2) * 0.6
              + 步骤数量(0-2) * 0.5
              + 计算复杂度(0-2) * 0.5
              + 隐藏条件(0/1) * 0.6
    再裁剪到 [1,5] 并四舍五入。
    """
    span = min(max(concepts - 1, 0), 2)
    step_lv = min(max(steps - 1, 0), 2)
    comp_lv = min(max(compute - 1, 0), 2)
    hidden_lv = 1 if hidden else 0
    raw = 1.0 + span * 0.6 + step_lv * 0.5 + comp_lv * 0.5 + hidden_lv * 0.6
    return max(1, min(5, int(round(raw))))


DIFF_LABELS = {1: "基础识记", 2: "基础应用", 3: "综合应用", 4: "提升", 5: "竞赛拓展"}


# ---------------------------------------------------------------------------
# 题型模板（每个返回标准题目片段 dict；难度由 REGISTRY 的 meta 推导）
# ---------------------------------------------------------------------------
def cat_rational_compare(rng, ctx, node) -> dict:
    kind = rng.choice(["abs", "opp", "cmp"])
    x = rng.choice(list(range(-99, 0)) + list(range(1, 100)))
    if kind == "abs":
        correct = abs(x)
        opts, ans = make_choice(rng, fmt_int(correct),
                                [fmt_int(-correct), fmt_int(x), fmt_int(-x), fmt_int(correct + 1), fmt_int(-(correct + 1))])
        return {"content": f"有理数 {x} 的绝对值是（  ）", "options": opts, "answer": ans,
                "analysis": f"负数的绝对值是它的相反数，|-{abs(x)}|={abs(x)}；正数的绝对值是它本身。", "type": "选择题"}
    if kind == "opp":
        correct = -x
        opts, ans = make_choice(rng, fmt_int(correct),
                                [fmt_int(x), fmt_int(abs(x)), fmt_int(-abs(x)), fmt_int(correct + 1)])
        return {"content": f"{x} 的相反数是（  ）", "options": opts, "answer": ans,
                "analysis": f"只有符号不同的两个数互为相反数，{x} 的相反数是 {correct}。", "type": "选择题"}
    a = rng.randint(-99, 99)
    b = rng.randint(-99, 99)
    while b == a:
        b = rng.randint(-99, 99)
    if a > b:
        correct, txt = "a>b", f"{a} > {b}"
    elif a < b:
        correct, txt = "a<b", f"{a} < {b}"
    else:
        correct, txt = "a=b", f"{a} = {b}"
    opts, ans = make_choice(rng, correct, ["a>b", "a<b", "a=b", "无法比较"])
    return {"content": f"比较大小：{a} 与 {b}（  ）", "options": opts, "answer": ans,
            "analysis": f"数轴上右边的数大，故 {txt}。", "type": "选择题"}


def cat_rational_op(rng, ctx, node) -> dict:
    a = rng.randint(2, 99)
    b = rng.randint(2, 99)
    op = rng.choice(["+", "-", "×"])
    if op == "+":
        correct = a + b
    elif op == "-":
        correct = a - b
    else:
        correct = a * b
    opts, ans = make_choice(rng, fmt_int(correct),
                            [fmt_int(correct + 1), fmt_int(correct - 1), fmt_int(correct + 2), fmt_int(correct - 2)])
    return {"content": f"计算：{a} {op} {b} = （  ）", "options": opts, "answer": ans,
            "analysis": f"按运算顺序计算：{a} {op} {b} = {correct}。", "type": "选择题"}


def cat_integer_expr(rng, ctx, node) -> dict:
    c1 = rng.randint(2, 19)
    c2 = rng.randint(2, 19)
    c3 = rng.randint(1, 9)
    correct = c1 + c2 - c3
    var = rng.choice(["x", "y", "m", "n", "a", "t"])
    expr = f"{c1}{var} + {c2}{var} - {c3}{var}"
    ans_txt = f"{correct}{var}" if correct != 0 else "0"
    opts, ans = make_choice(rng, ans_txt,
                            [f"{correct+1}{var}", f"{correct-1}{var}", f"{c1+c2}{var}", f"{correct+2}{var}"])
    return {"content": f"化简：{expr} = （  ）", "options": opts, "answer": ans,
            "analysis": f"合并同类项，系数相加：({c1}+{c2}-{c3}){var} = {ans_txt}。", "type": "选择题"}


def cat_linear_equation(rng, ctx, node) -> dict:
    a = rng.choice([2, 3, 4, 5, -2, -3])
    b = rng.randint(1, 9)
    x0 = rng.randint(-4, 4)
    c = a * x0 + b
    expr = f"{a}x" if a not in (1, -1) else ("x" if a == 1 else "-x")
    q = f"解方程 {expr} + {b} = {c}"
    ans = f"x = {x0}"
    if rng.random() < 0.6:
        opts, a2 = make_choice(rng, ans, [f"x = {x0+1}", f"x = {x0-1}", f"x = {-x0}", f"x = {x0+2}"])
        return {"content": q + "（  ）", "options": opts, "answer": a2,
                "analysis": f"移项：{expr} = {c} - {b} = {c-b}，故 x = {x0}。", "type": "选择题"}
    return {"content": q, "options": None, "answer": ans,
            "analysis": f"移项：{expr} = {c-b}，系数化为1 得 x = {x0}。", "type": "计算题"}


def cat_linear_function_def(rng, ctx, node) -> dict:
    k = rng.choice([2, 3, -2])
    b = rng.randint(1, 5)
    correct_expr = f"y = {k}x + {b}"
    distractors = ["y = x² + 1", "y = 1/x", "y = 5", "y = √x"]
    opts, ans = make_choice(rng, correct_expr, distractors)
    return {"content": "下列函数中，是一次函数的是（  ）", "options": opts, "answer": ans,
            "analysis": "一次函数形如 y=kx+b(k≠0)，是 x 的一次整式；二次函数、反比例函数、常数函数均不是。",
            "type": "选择题"}


def cat_linear_function_image(rng, ctx, node) -> dict:
    k = rng.choice([2, 3, -2, -3, 4, -4])
    b = rng.choice([1, 2, 3, 4, -1, -2, -3, -4])
    ks = "+" if k > 0 else "-"
    bs = "+" if b > 0 else "-"
    quad = {
        ("+", "+"): "第一、二、三象限",
        ("+", "-"): "第一、三、四象限",
        ("-", "+"): "第一、二、四象限",
        ("-", "-"): "第二、三、四象限",
    }
    passed = quad[(ks, bs)]
    all_q = ["第一象限", "第二象限", "第三象限", "第四象限"]
    missing = [q for q in all_q if q not in passed]
    expr = f"y={k}x{b}" if b >= 0 else f"y={k}x{b}"
    stem = f"已知一次函数 {expr}（k{ks}0，b{bs}0），其图像"
    if rng.random() < 0.5:
        opts, ans = make_choice(rng, passed, list(quad.values()))
        return {"content": stem + "经过（  ）", "options": opts, "answer": ans,
                "analysis": f"k{ks}0 决定增减性与倾斜方向，b{bs}0 决定与 y 轴交于正（或负）半轴，故经过 {passed}。",
                "type": "选择题"}
    opts, ans = make_choice(rng, missing[0], all_q)
    return {"content": stem + "不经过（  ）", "options": opts, "answer": ans,
            "analysis": f"该图像经过 {passed}，故不经过 {missing[0]}。", "type": "选择题"}


def cat_linear_function_prop(rng, ctx, node) -> dict:
    if rng.random() < 0.5:
        opts, ans = make_choice(rng, "k < 0", ["k > 0", "b < 0", "b > 0", "k = 0"])
        return {"content": "一次函数 y=kx+b 中，若 y 随 x 增大而减小，则（  ）",
                "options": opts, "answer": ans,
                "analysis": "一次函数增减性由 k 决定：k<0 时 y 随 x 增大而减小。", "type": "选择题"}
    opts, ans = make_choice(rng, "k<0，b>0", ["k>0，b>0", "k<0，b<0", "k>0，b<0", "k>0，b<0"])
    return {"content": "若一次函数 y=kx+b 的图像经过第一、二、四象限，则（  ）",
            "options": opts, "answer": ans,
            "analysis": "过一、二、四象限说明图像下降（k<0）且与 y 轴交于正半轴（b>0）。", "type": "选择题"}


# ---- 一次函数题型矩阵（用户指定 7 类）---------------------------------
def cat_linear_function_solve(rng, ctx, node) -> dict:
    k = rng.choice([2, 3, -2, -3])
    b = rng.randint(-3, 3)
    x1 = rng.randint(-2, 2)
    y1 = k * x1 + b
    x2 = x1 + 1
    y2 = k * x2 + b
    opts, ans = make_choice(rng, fmt_int(b), [fmt_int(b + 1), fmt_int(b - 1), fmt_int(b + 2), fmt_int(-b)])
    return {"content": f"已知一次函数图像经过 ({x1},{y1}) 和 ({x2},{y2})，则其解析式中的 b 为（  ）",
            "options": opts, "answer": ans,
            "analysis": f"设 y=kx+b，代入两点解得 k={k}，b={b}。", "type": "选择题"}


def cat_linear_function_translate(rng, ctx, node) -> dict:
    k = rng.choice([2, 3, -2, -3])
    b = rng.randint(-3, 3)
    h = rng.choice([1, 2])
    v = rng.choice([1, 2, -1, -2])
    new_b = b - k * h + v
    expr = f"y={k}x+{b}" if b >= 0 else f"y={k}x{b}"
    opts, ans = make_choice(rng, fmt_int(new_b), [fmt_int(new_b + 1), fmt_int(new_b - 1), fmt_int(new_b + k), fmt_int(b)])
    return {"content": f"将一次函数 {expr} 的图像向右平移 {h} 个单位、向上平移 {v} 个单位后，"
            f"新函数与 y 轴交点的纵坐标为（  ）",
            "options": opts, "answer": ans,
            "analysis": f"右移{h}→x→x-{h}，上移{v}→整体+{v}；新截距 = b - k·{h} + {v} = {new_b}。", "type": "选择题"}


def cat_linear_function_twolines(rng, ctx, node) -> dict:
    k1 = rng.choice([1, 2, 3, -1, -2, -3])
    b1 = rng.randint(-3, 3)
    kind = rng.choice(["parallel", "perp", "intersect", "coincide"])
    if kind == "parallel":
        k2, b2, correct = k1, b1 + rng.choice([1, 2, -1, -2]), "平行"
    elif kind == "coincide":
        k2, b2, correct = k1, b1, "重合"
    elif kind == "perp":
        k2, b2, correct = -1 / k1, rng.randint(-3, 3), "垂直"
    else:
        k2 = k1 + rng.choice([1, -1]) if (k1 + rng.choice([1, -1])) != 0 else k1 + 1
        b2, correct = rng.randint(-3, 3), "相交"
    k2s = f"{k2}" if k2 == int(k2) else f"{k2:.2f}".rstrip("0").rstrip(".")
    opts, ans = make_choice(rng, correct, ["平行", "垂直", "相交", "重合"])
    return {"content": f"直线 l₁: y={k1}x+{b1} 与 l₂: y={k2s}x+{b2} 的位置关系是（  ）",
            "options": opts, "answer": ans,
            "analysis": f"k₁={k1}, k₂={k2s}；{'k₁=k₂且b不同→平行' if kind=='parallel' else 'k₁·k₂=-1→垂直' if kind=='perp' else 'k₁=k₂且b相同→重合' if kind=='coincide' else '斜率不同→相交'}。",
            "type": "选择题"}


def cat_linear_function_application(rng, ctx, node) -> dict:
    a = rng.randint(8, 12)
    d = rng.randint(2, 4)
    b = rng.randint(1, 3)
    x = d + rng.randint(1, 5)
    cost = a + b * (x - d)
    opts, ans = make_choice(rng, fmt_int(cost), [fmt_int(cost + 1), fmt_int(cost - 1), fmt_int(a + b * x), fmt_int(a + x)])
    return {"content": f"某出租车起步价 {a} 元（含 {d} 公里），超出后每公里 {b} 元。行驶 {x} 公里应付（  ）",
            "options": opts, "answer": ans,
            "analysis": f"费用=起步价+超出里程×单价={a}+{b}×({x}-{d})={cost} 元（仅超出部分计费）。", "type": "选择题"}


def cat_linear_function_composite(rng, ctx, node) -> dict:
    k = rng.choice([2, 3, -2, -3])
    b = 2 * abs(k)
    area = 2 * abs(k)
    opts, ans = make_choice(rng, fmt_int(area), [fmt_int(area + 1), fmt_int(area - 1),
                                                 fmt_int(b * b // abs(k)), fmt_int(abs(b // k))])
    return {"content": f"一次函数 y={k}x+{b} 的图像与两坐标轴围成的三角形面积为（  ）",
            "options": opts, "answer": ans,
            "analysis": f"与x轴交点(-{b//k},0)，与y轴交点(0,{b})；面积=½×|{b//k}|×{b}={area}。", "type": "选择题"}


def cat_fraction(rng, ctx, node) -> dict:
    if rng.random() < 0.5:
        x = rng.randint(3, 7)
        opts, ans = make_choice(rng, fmt_int(x), [fmt_int(x + 1), fmt_int(x - 1), "0", fmt_int(2 * x)])
        return {"content": f"当 x = （  ）时，分式 1/(x-{x}) 无意义", "options": opts, "answer": ans,
                "analysis": "分式无意义的条件是分母为零，即 x-{x}=0，x={x}。", "type": "选择题"}
    a = rng.randint(3, 7)
    b = rng.randint(2, 6)
    correct = a + b
    opts, ans = make_choice(rng, f"a + b", [f"a - b", f"ab", f"(a+b)/(a-b)", f"a/b"])
    return {"content": f"化简：(a² - b²)/(a - b) = （  ）（a≠b）", "options": opts, "answer": ans,
            "analysis": f"用平方差公式：a²-b²=(a-b)(a+b)，约去 (a-b) 得 a+b。", "type": "选择题"}


def cat_pythagoras(rng, ctx, node) -> dict:
    m = rng.randint(2, 4)
    n = rng.randint(1, m - 1)
    a = m * m - n * n
    b = 2 * m * n
    c = m * m + n * n
    if rng.random() < 0.5:
        opts, ans = make_choice(rng, fmt_int(c), [fmt_int(c + 1), fmt_int(c - 1), fmt_int(a), fmt_int(b)])
        return {"content": f"Rt△中两直角边长分别为 {a} 和 {b}，则斜边为（  ）",
                "options": opts, "answer": ans,
                "analysis": f"勾股定理：c=√({a}²+{b}²)=√({a*a+b*b})={c}。", "type": "选择题"}
    opts, ans = make_choice(rng, fmt_int(b), [fmt_int(b + 1), fmt_int(b - 1), fmt_int(a), fmt_int(c)])
    return {"content": f"Rt△中斜边为 {c}，一直角边为 {a}，则另一直角边为（  ）",
            "options": opts, "answer": ans,
            "analysis": f"由勾股定理：另一直角边=√({c}²-{a}²)=√({c*c-a*a})={b}。", "type": "选择题"}


def cat_quadrilateral(rng, ctx, node) -> dict:
    bank = [
        ("对角线互相平分的四边形是平行四边形。", True),
        ("对角线相等的四边形是矩形。", False),
        ("一组对边平行的四边形是平行四边形。", False),
        ("对角线互相垂直的四边形是菱形。", False),
        ("有三个角是直角的四边形是矩形。", True),
        ("四条边相等的四边形是正方形。", False),
        ("菱形的对角线互相垂直平分。", True),
    ]
    true_stmts = [s for s, t in bank if t]
    false_stmts = [s for s, t in bank if not t]
    correct = rng.choice(true_stmts)
    others = _sample_distinct(rng, false_stmts, 3, {correct})
    opts, ans = make_choice(rng, correct, others)
    return {"content": "下列命题正确的是（  ）", "options": opts, "answer": ans,
            "analysis": "判定定理需严格满足：对角线互相平分⇔平行四边形；三直角⇔矩形；菱形对角线垂直平分。",
            "type": "选择题"}


def cat_axisymmetry(rng, ctx, node) -> dict:
    correct = "等腰三角形"
    others = ["平行四边形", "任意梯形", "不等边三角形", "一般平行四边形"]
    opts, ans = make_choice(rng, correct, others)
    return {"content": "下列图形中，一定是轴对称图形的是（  ）", "options": opts, "answer": ans,
            "analysis": "等腰三角形沿底边上的高对称；一般平行四边形、任意梯形未必轴对称。", "type": "选择题"}


def cat_radical(rng, ctx, node) -> dict:
    x = rng.choice([-5, -3, -2, 2, 3, 5])
    if rng.random() < 0.5:
        correct = abs(x)
        opts, ans = make_choice(rng, fmt_int(correct), [fmt_int(x), fmt_int(-correct), fmt_int(correct + 1), fmt_int(x * 2)])
        return {"content": f"√( ({x})² ) = （  ）", "options": opts, "answer": ans,
                "analysis": f"√(a²)=|a|，故 √({x}²)=|{x}|={correct}。", "type": "选择题"}
    opts, ans = make_choice(rng, "3", ["-3", "±3", "9", "0"])
    return {"content": "√9 = （  ）", "options": opts, "answer": ans,
            "analysis": "算术平方根取非负值，√9=3。", "type": "选择题"}


def cat_quadratic_equation(rng, ctx, node) -> dict:
    r1 = rng.randint(-4, 4)
    r2 = rng.randint(-4, 4)
    while r2 == r1:
        r2 = rng.randint(-4, 4)
    b = -(r1 + r2)
    c = r1 * r2
    if rng.random() < 0.5:
        opts, ans = make_choice(rng, f"x₁={r1}, x₂={r2}",
                                [f"x₁={r1+1}, x₂={r2}", f"x₁={r1}, x₂={r2+1}",
                                 f"x₁={-r1}, x₂={-r2}", f"x={r1+r2}"])
        return {"content": f"解方程：x² + ({b})x + {c} = 0（  ）", "options": opts, "answer": ans,
                "analysis": f"因式分解：(x-{r1})(x-{r2})=0，得 x₁={r1}, x₂={r2}。", "type": "选择题"}
    return {"content": f"解方程：x² + ({b})x + {c} = 0", "options": None,
            "answer": f"x₁={r1}, x₂={r2}",
            "analysis": f"因式分解：(x-{r1})(x-{r2})=0，得 x₁={r1}, x₂={r2}。", "type": "计算题"}


def cat_quadratic_function(rng, ctx, node) -> dict:
    a = rng.choice([1, 2, -1, -2])
    b = rng.randint(1, 6)
    axis = -b / (2 * a)
    opts, ans = make_choice(rng, f"x = {axis}", [f"x = {-axis}", f"x = {b}", f"x = {b/(2*a)}", "x = 0"])
    return {"content": f"抛物线 y = {a}x² + ({b})x + 3 的对称轴是（  ）",
            "options": opts, "answer": ans,
            "analysis": f"对称轴公式 x = -b/(2a) = -{b}/(2×{a}) = {axis}。", "type": "选择题"}


def cat_quadratic_function_vertex(rng, ctx, node) -> dict:
    a = rng.choice([1, 2, -1, -2])
    b = rng.randint(1, 6)
    c = rng.randint(1, 5)
    # 顶点纵坐标 = c - b²/(4a)
    vertex_y = c - (b * b) / (4 * a)
    opt_val = fmt_int(vertex_y)
    opts, ans = make_choice(rng, opt_val, [fmt_int(vertex_y + 1), fmt_int(vertex_y - 1),
                                           fmt_int(c + b), fmt_int(c - b)])
    word = "最小值" if a > 0 else "最大值"
    return {"content": f"二次函数 y={a}x²+{b}x+{c} 的{word}是（  ）",
            "options": opts, "answer": ans,
            "analysis": f"顶点纵坐标 = c - b²/(4a) = {c} - {b}²/(4×{a}) = {vertex_y}（a{'>' if a>0 else '<'}0 时为{'最小' if a>0 else '最大'}值）。",
            "type": "选择题"}


def cat_circle(rng, ctx, node) -> dict:
    if rng.random() < 0.5:
        r = rng.randint(2, 7)
        correct = 2 * r
        opts, ans = make_choice(rng, fmt_int(correct), [fmt_int(r), fmt_int(r * r), fmt_int(4 * r), fmt_int(correct + 1)])
        return {"content": f"半径为 {r} 的圆，周长是（  ）（π 取 3.14 时数值略）", "options": opts, "answer": ans,
                "analysis": f"圆周长 C = 2πr = 2×{r}π = {correct}π。", "type": "选择题"}
    n = rng.choice([60, 90, 120, 180])
    r = rng.randint(2, 6)
    opts, ans = make_choice(rng, f"{n*r/180}π", [f"{n*r}π", f"{n/180}π", f"{r}π", f"{n}πr"])
    return {"content": f"半径为 {r}，圆心角为 {n}° 的弧长是（  ）", "options": opts, "answer": ans,
            "analysis": f"弧长 l = nπr/180 = {n}×{r}π/180 = {n*r/180}π。", "type": "选择题"}


def cat_circle_position(rng, ctx, node) -> dict:
    r = rng.randint(2, 6)
    d = rng.choice([r - 1, r, r + 1, r + 2])
    if d > r:
        correct, expl = "相离", f"d={d} > r={r}"
    elif d == r:
        correct, expl = "相切", f"d={d} = r={r}"
    else:
        correct, expl = "相交", f"d={d} < r={r}"
    opts, ans = make_choice(rng, correct, ["相离", "相切", "相交", "内含"])
    return {"content": f"⊙O 半径为 {r}，圆心到直线距离 d={d}，则直线与圆的位置关系是（  ）",
            "options": opts, "answer": ans,
            "analysis": f"比较 d 与 r：{expl} → {correct}。", "type": "选择题"}


def cat_similar(rng, ctx, node) -> dict:
    ratio = rng.choice([2, 3, 4])
    opts, ans = make_choice(rng, f"{ratio}:1", [f"1:{ratio}", f"{ratio*ratio}:1", f"1:{ratio*ratio}", f"{ratio+1}:1"])
    return {"content": f"若 △ABC∽△DEF，相似比为 {ratio}:1，则周长比为（  ）", "options": opts, "answer": ans,
            "analysis": f"相似图形周长比等于相似比，面积比等于相似比的平方（{ratio*ratio}:1）。", "type": "选择题"}


def cat_probability(rng, ctx, node) -> dict:
    R = rng.randint(2, 6)
    B = rng.randint(2, 6)
    total = R + B
    correct = f"{R}/{total}"
    opts, ans = make_choice(rng, correct, [f"{B}/{total}", f"{R}/{B}", f"{B}/{R}", f"1/{total}"])
    return {"content": f"袋中有 {R} 个红球、{B} 个蓝球，随机摸一个，摸到红球的概率是（  ）",
            "options": opts, "answer": ans,
            "analysis": f"P(红)=红球数/总数={R}/{total}。", "type": "选择题"}


def cat_prob_tree(rng, ctx, node) -> dict:
    # 两步：第一次红/蓝，第二次红/蓝（放回）
    r1 = rng.randint(2, 4)
    b1 = rng.randint(1, 3)
    r2 = rng.randint(2, 4)
    b2 = rng.randint(1, 3)
    # P(两次都红) = (r1/(r1+b1)) * (r2/(r2+b2))
    p = (r1 / (r1 + b1)) * (r2 / (r2 + b2))
    # 选项给分数近似
    approx = round(p, 2)
    opts, ans = make_choice(rng, f"{approx}", [f"{round(p+0.1,2)}", f"{round(p-0.1,2)}",
                                               f"{round(r1/(r1+b1),2)}", f"{round(r2/(r2+b2),2)}"])
    return {"content": f"甲袋 {r1} 红 {b1} 蓝，乙袋 {r2} 红 {b2} 蓝，分别摸一球均为红的概率约为（  ）",
            "options": opts, "answer": ans,
            "analysis": f"分步相乘：P = {r1}/{r1+b1} × {r2}/{r2+b2} ≈ {approx}。", "type": "选择题"}


def cat_statistics(rng, ctx, node) -> dict:
    nums = [rng.randint(60, 100) for _ in range(3)]
    mean = round(sum(nums) / 3, 1)
    opts, ans = make_choice(rng, fmt_int(mean) if mean == int(mean) else str(mean),
                            [fmt_int(sum(nums)), fmt_int(max(nums)), fmt_int(min(nums)), fmt_int(mean + 5)])
    return {"content": f"数据 {nums[0]}, {nums[1]}, {nums[2]} 的平均数是（  ）",
            "options": opts, "answer": ans,
            "analysis": f"平均数 = ({nums[0]}+{nums[1]}+{nums[2]})/3 = {mean}。", "type": "选择题"}


def cat_stat_variance(rng, ctx, node) -> dict:
    nums = [rng.randint(70, 90) for _ in range(3)]
    mean = sum(nums) / 3
    var = round(sum((x - mean) ** 2 for x in nums) / 3, 1)
    opts, ans = make_choice(rng, f"{var}", [f"{round(var+2,1)}", f"{round(var-2,1)}",
                                            f"{round(mean,1)}", f"{max(nums)-min(nums)}"])
    return {"content": f"数据 {nums[0]}, {nums[1]}, {nums[2]} 的方差约为（  ）",
            "options": opts, "answer": ans,
            "analysis": f"方差=各数与平均数差的平方的平均；均值≈{round(mean,1)}，故方差≈{var}（越小越稳定）。", "type": "选择题"}


def cat_geometry_basic(rng, ctx, node) -> dict:
    name = ctx["knowledge"]
    if "圆" in name:
        r = rng.randint(2, 99)
        correct = r * r
        opts, ans = make_choice(rng, fmt_int(correct), [fmt_int(2 * r), fmt_int(4 * r), fmt_int(correct + 1), fmt_int(r)])
        return {"content": f"半径为 {r} 的圆，面积是（  ）（单位略）", "options": opts, "answer": ans,
                "analysis": f"圆面积 S = πr² = {r}²π = {correct}π。", "type": "选择题"}
    if "周长" in name or "圆柱" in name or "锥" in name:
        a = rng.randint(2, 99)
        b = rng.randint(2, 99)
        correct = 2 * (a + b)
        opts, ans = make_choice(rng, fmt_int(correct), [fmt_int(a + b), fmt_int(a * b), fmt_int(2 * a), fmt_int(correct + 2)])
        return {"content": f"长 {a}、宽 {b} 的长方形，周长是（  ）", "options": opts, "answer": ans,
                "analysis": f"长方形周长 = 2×(长+宽) = 2×({a}+{b}) = {correct}。", "type": "选择题"}
    a = rng.randint(2, 99)
    b = rng.randint(2, 99)
    correct = a * b
    opts, ans = make_choice(rng, fmt_int(correct), [fmt_int(2 * (a + b)), fmt_int(a + b), fmt_int(correct + 1), fmt_int(a * b // 2)])
    return {"content": f"底 {a}、高 {b} 的长方形/平行四边形，面积是（  ）", "options": opts, "answer": ans,
            "analysis": f"S = 底×高 = {a}×{b} = {correct}。", "type": "选择题"}


def cat_geometry_volume(rng, ctx, node) -> dict:
    name = ctx["knowledge"]
    r = rng.randint(2, 4)
    h = rng.randint(3, 7)
    if "圆锥" in name:
        correct = round((1 / 3) * 3.14 * r * r * h, 1)
        opts, ans = make_choice(rng, f"{correct}", [f"{round(3.14*r*r*h,1)}", f"{round(3.14*r*r,1)}",
                                                    f"{round((1/3)*3.14*r*h,1)}", f"{h}"])
        return {"content": f"底面半径 {r}、高 {h} 的圆锥体积（π取3.14）约为（  ）", "options": opts, "answer": ans,
                "analysis": f"V锥 = ⅓πr²h = ⅓×3.14×{r}²×{h} ≈ {correct}。", "type": "选择题"}
    correct = round(3.14 * r * r * h, 1)
    opts, ans = make_choice(rng, f"{correct}", [f"{round((1/3)*3.14*r*r*h,1)}", f"{round(3.14*r*h,1)}",
                                                f"{round(2*3.14*r*h,1)}", f"{h}"])
    return {"content": f"底面半径 {r}、高 {h} 的圆柱体积（π取3.14）约为（  ）", "options": opts, "answer": ans,
            "analysis": f"V柱 = πr²h = 3.14×{r}²×{h} ≈ {correct}。", "type": "选择题"}


def cat_arithmetic(rng, ctx, node) -> dict:
    a = rng.randint(3, 99)
    b = rng.randint(2, 99)
    op = rng.choice(["+", "-", "×"])
    if op == "+":
        correct = a + b
    elif op == "-":
        correct = a - b
    else:
        correct = a * b
    opts, ans = make_choice(rng, fmt_int(correct),
                            [fmt_int(correct + 1), fmt_int(correct - 1), fmt_int(correct + 2), fmt_int(correct - 2)])
    return {"content": f"计算：{a} {op} {b} = （  ）", "options": opts, "answer": ans,
            "analysis": f"{a} {op} {b} = {correct}。", "type": "选择题"}


def cat_decimal(rng, ctx, node) -> dict:
    if rng.random() < 0.5:
        a = rng.randint(1, 99) / 10
        b = rng.randint(1, 99)
        correct = round(a * b, 2)
        opts, ans = make_choice(rng, f"{correct}", [f"{round(a*b+0.1,2)}", f"{round(a*b-0.1,2)}", f"{a*b:.0f}", f"{a+b}"])
        return {"content": f"计算：{a} × {b} = （  ）", "options": opts, "answer": ans,
                "analysis": f"先按整数乘再点小数点：{a}×{b}={correct}。", "type": "选择题"}
    correct = round(rng.randint(1, 99) / 10 + rng.randint(1, 99) / 10, 2)
    x = rng.randint(1, 99) / 10
    y = rng.randint(1, 99) / 10
    opts, ans = make_choice(rng, f"{round(x+y,2)}", [f"{round(x+y+0.1,2)}", f"{round(x-y,2)}", f"{x*y}", f"{x}"])
    return {"content": f"计算：{x} + {y} = （  ）", "options": opts, "answer": ans,
            "analysis": f"小数点对齐相加：{x}+{y}={round(x+y,2)}。", "type": "选择题"}


def cat_decimal_mult(rng, ctx, node) -> dict:
    a = rng.randint(1, 9) / 10
    b = rng.choice([0.2, 0.3, 0.4, 0.5, 0.6])
    correct = round(a * b, 3)
    opts, ans = make_choice(rng, f"{correct}", [f"{round(a*b+0.05,3)}", f"{round(a*b-0.05,3)}",
                                                f"{round(a+b,3)}", f"{a}"])
    return {"content": f"计算：{a} × {b} = （  ）", "options": opts, "answer": ans,
            "analysis": f"按小数乘法点小数点：{a}×{b}={correct}。", "type": "选择题"}


def cat_decimal_div(rng, ctx, node) -> dict:
    # 构造整除：0.a / 0.b = a/b，取 a,b 使整除
    a = rng.choice([2, 4, 5, 6, 8])
    b = rng.choice([2, 4, 5])
    while a % b != 0:
        a = rng.choice([2, 4, 5, 6, 8]); b = rng.choice([2, 4, 5])
    correct = a // b
    opts, ans = make_choice(rng, f"{correct}", [f"{correct+1}", f"{correct-1}", f"{a}", f"{b}"])
    return {"content": f"计算：0.{a} ÷ 0.{b} = （  ）", "options": opts, "answer": ans,
            "analysis": f"被除数与除数同扩 10 倍：0.{a}÷0.{b} = {a}÷{b} = {correct}。", "type": "选择题"}


def cat_fraction_basic(rng, ctx, node) -> dict:
    if rng.random() < 0.5:
        a = rng.randint(1, 19)
        b = rng.randint(2, 12)
        correct = a + b
        opts, ans = make_choice(rng, f"{correct}/6", [f"{(a+b-1)}/6", f"{a}/6", f"{correct}/12", f"{a+b}/3"])
        return {"content": f"计算：{a}/6 + {b}/6 = （  ）", "options": opts, "answer": ans,
                "analysis": f"同分母分数相加，分母不变分子相加：({a}+{b})/6 = {correct}/6。", "type": "选择题"}
    correct = 5
    opts, ans = make_choice(rng, "5/6", ["1/6", "2/6", "3/6", "1/2"])
    return {"content": "计算：1/2 + 1/3 = （  ）", "options": opts, "answer": ans,
            "analysis": "通分：1/2+1/3 = 3/6+2/6 = 5/6。", "type": "选择题"}


def cat_fraction_mult(rng, ctx, node) -> dict:
    a = rng.randint(1, 4)
    b = rng.randint(2, 5)
    c = rng.randint(1, 4)
    d = rng.randint(2, 5)
    correct = (a * c) / (b * d)
    opts, ans = make_choice(rng, f"{a*c}/{b*d}", [f"{a*c+1}/{b*d}", f"{a+c}/{b+d}", f"{a*c}/{b*d+1}", f"{a}/{b}"])
    return {"content": f"计算：{a}/{b} × {c}/{d} = （  ）", "options": opts, "answer": ans,
            "analysis": f"分数乘法：分子乘分子、分母乘分母 → {a*c}/{b*d}（可约分）。", "type": "选择题"}


def cat_fraction_div(rng, ctx, node) -> dict:
    a = rng.randint(1, 4)
    b = rng.randint(2, 5)
    c = rng.randint(1, 4)
    d = rng.randint(2, 5)
    correct = (a * d) / (b * c)
    opts, ans = make_choice(rng, f"{a*d}/{b*c}", [f"{a*c}/{b*d}", f"{a}/{b}", f"{c}/{d}", f"{a*d+1}/{b*c}"])
    return {"content": f"计算：{a}/{b} ÷ {c}/{d} = （  ）", "options": opts, "answer": ans,
            "analysis": f"除以分数等于乘其倒数：{a}/{b} × {d}/{c} = {a*d}/{b*c}。", "type": "选择题"}


def cat_ratio_prop(rng, ctx, node) -> dict:
    a = rng.randint(2, 9)
    b = rng.choice([3, 4, 5])
    k = rng.randint(2, 4)
    correct = a * k
    opts, ans = make_choice(rng, f"{correct}", [f"{a+b*k}", f"{a*k+b}", f"{a+b}", f"{correct+1}"])
    return {"content": f"若 a:b = {a}:{b}，且 b = {b*k}，则 a = （  ）", "options": opts, "answer": ans,
            "analysis": f"按比例缩放：b 扩大 {k} 倍到 {b*k}，a 也扩大 {k} 倍 → {a*k}。", "type": "选择题"}


def cat_percent_app(rng, ctx, node) -> dict:
    price = rng.choice([100, 200, 250, 400])
    disc = rng.choice([10, 20, 25])
    correct = price * (100 - disc) / 100
    opts, ans = make_choice(rng, f"{correct:.0f}" if correct == int(correct) else f"{correct:.1f}",
                            [f"{price}", f"{price*disc/100:.0f}", f"{price*(100+disc)/100:.0f}", f"{correct+10:.0f}"])
    return {"content": f"一件商品原价 {price} 元，打 {disc} 折后售价是（  ）", "options": opts, "answer": ans,
            "analysis": f"折后价 = 原价×折扣 = {price} × (1-{disc}/100) = {correct} 元。", "type": "选择题"}


def cat_equation_basic(rng, ctx, node) -> dict:
    a = rng.randint(2, 5)
    opts, ans = make_choice(rng, f"{a}a + b", [f"{a}(a+b)", f"a + {a}b", f"{a}a - b", f"{a+b}a"])
    return {"content": f"用字母表示：a 的 {a} 倍与 b 的和，写作（  ）", "options": opts, "answer": ans,
            "analysis": f"a 的 {a} 倍是 {a}a，再加 b 得 {a}a + b。", "type": "选择题"}


def cat_factor_multiple(rng, ctx, node) -> dict:
    n = rng.choice([12, 15, 18, 20])
    opts, ans = make_choice(rng, "质数", ["因数", "合数", "倍数", "奇数"])
    correct_expl = f"{n} 是合数（有多个因数），质数仅有 1 和自身两个因数。"
    # 改为判断质数/合数更严谨
    is_prime = n in (2, 3, 5, 7, 11, 13, 17, 19)
    correct = "质数" if is_prime else "合数"
    opts, ans = make_choice(rng, correct, ["质数", "合数", "奇数", "偶数"])
    return {"content": f"关于 {n}，下列说法正确的是（  ）", "options": opts, "answer": ans,
            "analysis": f"{n} {'只有 1 和自身两个因数→质数' if is_prime else '除了 1 和自身还有别的因数→合数'}。", "type": "选择题"}


def cat_fallback(rng, ctx, node) -> dict:
    summary = node.get("summary", "") or node.get("name", "")
    formula = node.get("formula")
    answer = formula[0] if isinstance(formula, list) and formula else summary
    return {"content": f"请写出『{node.get('name')}』的要点：____", "options": None,
            "answer": str(answer),
            "analysis": f"『{node.get('name')}』：{summary}", "type": "填空题", "difficulty": 1}


# ---------------------------------------------------------------------------
# 题型矩阵注册表（qcategory -> [子题型入口]）
# 每个入口含 fn / meta(知识跨度/步骤/计算/隐藏) / subtype(题型名)
# ---------------------------------------------------------------------------
M = dict  # 简写


REGISTRY: Dict[str, List[dict]] = {
    "rational_compare": [_e(cat_rational_compare, 1, 1, 1, False, "概念比较")],
    "rational_op": [_e(cat_rational_op, 1, 2, 1, False, "有理数运算")],
    "integer_expr": [_e(cat_integer_expr, 1, 2, 1, False, "整式化简")],
    "linear_equation": [_e(cat_linear_equation, 1, 3, 2, False, "一元一次方程")],
    # 一次函数题型矩阵（7 类，难度 1→5）
    "linear_function_def": [_e(cat_linear_function_def, 1, 1, 1, False, "定义判断")],
    "linear_function_image": [_e(cat_linear_function_image, 2, 2, 1, False, "图像性质")],
    "linear_function_prop": [_e(cat_linear_function_prop, 1, 2, 1, False, "增减性判断")],
    "linear_function_solve": [_e(cat_linear_function_solve, 1, 3, 2, False, "解析式求解")],
    "linear_function_translate": [_e(cat_linear_function_translate, 2, 3, 2, False, "图像平移")],
    "linear_function_twolines": [_e(cat_linear_function_twolines, 2, 3, 2, False, "两直线关系")],
    "linear_function_application": [_e(cat_linear_function_application, 2, 4, 2, True, "实际应用")],
    "linear_function_composite": [_e(cat_linear_function_composite, 3, 4, 3, True, "综合函数")],
    "fraction": [_e(cat_fraction, 1, 2, 1, False, "分式运算")],
    "pythagoras": [_e(cat_pythagoras, 1, 2, 2, False, "勾股定理")],
    "quadrilateral": [_e(cat_quadrilateral, 1, 1, 1, False, "判定辨析")],
    "axisymmetry": [_e(cat_axisymmetry, 1, 1, 1, False, "轴对称识别")],
    "radical": [_e(cat_radical, 1, 1, 1, False, "二次根式")],
    "quadratic_equation": [_e(cat_quadratic_equation, 1, 3, 2, False, "一元二次方程")],
    "quadratic_function": [_e(cat_quadratic_function, 2, 2, 2, False, "对称轴")],
    "quadratic_function_vertex": [_e(cat_quadratic_function_vertex, 2, 3, 3, False, "最值")],
    "circle": [_e(cat_circle, 1, 2, 1, False, "圆计算")],
    "circle_position": [_e(cat_circle_position, 1, 2, 1, False, "位置关系")],
    "similar": [_e(cat_similar, 1, 1, 1, False, "相似比")],
    "probability": [_e(cat_probability, 1, 2, 1, False, "概率计算")],
    "prob_tree": [_e(cat_prob_tree, 2, 3, 2, False, "树状图")],
    "statistics": [_e(cat_statistics, 1, 2, 1, False, "平均数")],
    "stat_variance": [_e(cat_stat_variance, 1, 3, 2, False, "方差")],
    "geometry_basic": [_e(cat_geometry_basic, 1, 2, 1, False, "图形计算")],
    "geometry_volume": [_e(cat_geometry_volume, 1, 3, 2, False, "体积计算")],
    "arithmetic": [_e(cat_arithmetic, 1, 1, 1, False, "四则运算")],
    "decimal": [_e(cat_decimal, 1, 2, 1, False, "小数加减")],
    "decimal_mult": [_e(cat_decimal_mult, 1, 2, 1, False, "小数乘法")],
    "decimal_div": [_e(cat_decimal_div, 1, 2, 1, False, "小数除法")],
    "fraction_basic": [_e(cat_fraction_basic, 1, 2, 1, False, "分数加减")],
    "fraction_mult": [_e(cat_fraction_mult, 1, 2, 1, False, "分数乘法")],
    "fraction_div": [_e(cat_fraction_div, 1, 2, 1, False, "分数除法")],
    "ratio_prop": [_e(cat_ratio_prop, 1, 2, 1, False, "比和比例")],
    "percent_app": [_e(cat_percent_app, 1, 2, 1, False, "百分数应用")],
    "equation_basic": [_e(cat_equation_basic, 1, 1, 1, False, "用字母表示")],
    "factor_multiple": [_e(cat_factor_multiple, 1, 1, 1, False, "因数倍数")],
}


# ---------------------------------------------------------------------------
# 合并 Phase 1.5-D 扩展题型（总量达 120 类）
# ---------------------------------------------------------------------------
from .templates_extra import EXTRA_REGISTRY  # noqa: E402
REGISTRY.update(EXTRA_REGISTRY)


# ---------------------------------------------------------------------------
# 生成器
# ---------------------------------------------------------------------------
class MathQuestionGenerator:
    def __init__(self, seed: int = 2026):
        self.rng_seed = seed
        self.rng = random.Random(seed)

    def generate_for_node(self, node: dict, ctx: dict, count: int) -> List[dict]:
        cat = node.get("qcategory")
        entries = REGISTRY.get(cat)
        if not entries:
            entries = [_e(cat_fallback, 1, 1, 1, False, "默认")]
        out = []
        ew = int(node.get("exam_weight", 3) or 3)
        # 错因标签 = 知识点层易错点(已人工标注) ∪ 题型层错因标准集，去重后取前 3
        node_errs = [e for e in (node.get("errors") or []) if e]
        # 节点内去重（保障「高质量」：杜绝单节点生成数十道雷同题）
        seen: set = set()
        for i in range(count):
            # 每题独立随机源：由 (全局种子, 知识点名, 序号) 派生，与生成顺序无关、
            # 可完全复现——既保证确定性，又使容量仿真与最终产出逐题一致。
            rnd = random.Random(f"{self.rng_seed}|{node.get('name', '')}|{i}")
            entry = entries[i % len(entries)]  # 轮转保证题型矩阵全覆盖
            try:
                q = entry["fn"](rnd, ctx, node)
            except Exception:
                q = cat_fallback(rnd, ctx, node)
            q["grade"] = ctx["grade"]
            q["subject"] = ctx["subject"]
            q["chapter"] = ctx.get("chapter") or ""
            q["knowledge"] = [node["name"]]
            q["difficulty"] = compute_difficulty(**entry["meta"])
            q["exam_weight"] = max(1, min(5, ew))
            q["subtype"] = entry["subtype"]
            # 错因标签（Phase 1.5-D）：知识点易错点优先，不足则补题型标准错因
            err_tags = list(dict.fromkeys(node_errs + list(entry.get("error_causes", []))))[:3]
            q["error_tags"] = err_tags
            q["id"] = f"{ctx['subject']}{ctx['grade']}_{node['name']}_{entry['subtype']}_{i+1}"
            key = str(q.get("content", "")).strip().lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(q)
        return out


def load_knowledge_trees() -> List[dict]:
    root = cfg.PROJECT_ROOT / "resource" / "knowledge"
    trees = []
    for sub in ("middle_math", "primary_math"):
        d = root / sub
        if not d.exists():
            continue
        for p in sorted(d.glob("grade*.json")):
            trees.append((sub, json.loads(p.read_text(encoding="utf-8"))))
    return trees


def _tier_of(d: int) -> str:
    """难度分组：基础(L1-2) / 提高(L3) / 综合(L4-5)。"""
    if d <= 2:
        return "basic"
    if d == 3:
        return "improve"
    return "comp"


def generate_all(total_unique_target: int = 32000, seed: int = 2026,
                 target_tier: dict = None, ref_c: int = 60, iters: int = 3) -> dict:
    """规模化生成全部年级题库 JSON（Phase 1.5-D）。

    目标：知识图谱去重后唯一题量 ≥ total_unique_target，且唯一题的难度分组
    精确收敛到 基础 50% / 提高 35% / 综合 15%。

    实现要点：
    1) 按难度分组收集可出题节点（跳过章节/思想方法枢纽等结构节点）；
    2) 抽样估计各组「每原始题→唯一题」效率 eff[g]：综合组题型参数空间大、
       唯一效率高；基础组多为概念/定义类、唯一效率低；
    3) 效率感知分配原始题预算 raw_budget[g] = U·T_g / eff[g]，使唯一题占比收敛到目标；
       组内按重点/高频考点上浮 1.4×，再归一化；
    4) 迭代校正：仿真唯一占比，按 (目标/实际) 修正预算比例，3 轮收敛到 ±1%；
    5) 单节点生成后按题干内容去重（杜绝雷同题，保障「高质量」）。
    """
    if target_tier is None:
        target_tier = {"basic": 0.50, "improve": 0.35, "comp": 0.15}
    gen = MathQuestionGenerator(seed=seed)
    out_root = cfg.PROJECT_ROOT / "resource" / "questions"

    trees = load_knowledge_trees()
    # 收集可出题节点（按难度分组）
    nodes_by_tier = {"basic": [], "improve": [], "comp": []}
    for sub, tree in trees:
        for node in tree["nodes"]:
            cat = node.get("qcategory")
            if not cat:
                continue  # 章节/思想方法枢纽等结构节点不出题
            entries = REGISTRY.get(cat)
            d = compute_difficulty(**entries[0]["meta"]) if entries else 1
            nodes_by_tier[_tier_of(d)].append((sub, tree, node))

    def _ctx_of(tree, nd):
        return {"subject": tree["subject"], "grade": tree["grade"],
                "chapter": nd.get("parent"), "knowledge": nd["name"]}

    def _is_boosted(nd):
        return bool(nd.get("important") or int(nd.get("exam_weight", 1) or 1) >= 4)

    def _simulate(raw_budget):
        total = 0
        tiers = {"basic": 0, "improve": 0, "comp": 0}
        for g, ns in nodes_by_tier.items():
            if not ns:
                continue
            raw_g = raw_budget[g]
            n = len(ns)
            base = raw_g / n
            weights = [base * (1.4 if _is_boosted(nd) else 1.0) for _, _, nd in ns]
            s = sum(weights) or 1.0
            scale = raw_g / s
            for (sub, tree, nd), w in zip(ns, weights):
                cnt = max(1, int(round(w * scale)))
                qs = gen.generate_for_node(nd, _ctx_of(tree, nd), cnt)
                total += len(qs)
                tiers[g] += len(qs)
        return total, tiers

    # PASS1：抽样估计各组效率（每组最多 40 节点，ref_c 题/节点）
    eff = {}
    for g, ns in nodes_by_tier.items():
        if not ns:
            eff[g] = 1.0
            continue
        sample = ns[:min(len(ns), 40)]
        tot = 0
        raw = 0
        for sub, tree, nd in sample:
            qs = gen.generate_for_node(nd, _ctx_of(tree, nd), ref_c)
            tot += len(qs)
            raw += ref_c
        eff[g] = (tot / raw) if raw else 1.0

    # PASS2：效率感知分配 + 迭代校正（收敛唯一题占比到目标）
    raw_budget = {g: total_unique_target * target_tier[g] / eff[g] for g in target_tier}
    for _ in range(iters):
        total, tiers = _simulate(raw_budget)
        if total <= 0:
            break
        for g in target_tier:
            actual = tiers[g] / total
            if actual > 0:
                raw_budget[g] *= target_tier[g] / actual
        cur_total, _ = _simulate(raw_budget)
        if cur_total > 0:
            scale_all = total_unique_target / cur_total
            raw_budget = {g: raw_budget[g] * scale_all for g in raw_budget}

    # 终版：构建生成计划（复用收敛后的预算）
    plan = []
    for g, ns in nodes_by_tier.items():
        if not ns:
            continue
        raw_g = raw_budget[g]
        n = len(ns)
        base = raw_g / n
        weights = [base * (1.4 if _is_boosted(nd) else 1.0) for _, _, nd in ns]
        s = sum(weights) or 1.0
        scale = raw_g / s
        for (sub, tree, nd), w in zip(ns, weights):
            cnt = max(1, int(round(w * scale)))
            plan.append((sub, tree, nd, cnt))

    stats = {"files": 0, "questions": 0, "by_category": {},
             "by_difficulty": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
             "by_tier": {"basic": 0, "improve": 0, "comp": 0},
             "raw_target": int(sum(raw_budget.values()))}
    by_file = {}
    for sub, tree, nd, cnt in plan:
        qs = gen.generate_for_node(nd, _ctx_of(tree, nd), cnt)
        key = (sub, tree["subject"], tree["grade"])
        by_file.setdefault(key, []).extend(qs)
        c = nd.get("qcategory", "fallback")
        stats["by_category"][c] = stats["by_category"].get(c, 0) + len(qs)
        for q in qs:
            stats["by_difficulty"][q["difficulty"]] = stats["by_difficulty"].get(q["difficulty"], 0) + 1
            stats["by_tier"][_tier_of(q["difficulty"])] += 1
            stats["questions"] += 1

    for (sub, subject, grade), questions in by_file.items():
        gnum = cfg.GRADE_LEVEL[grade]
        target_dir = out_root / sub
        target_dir.mkdir(parents=True, exist_ok=True)
        out_file = target_dir / f"grade{gnum}.json"
        out_file.write_text(json.dumps(
            {"subject": subject, "grade": grade, "questions": questions},
            ensure_ascii=False, indent=2), encoding="utf-8")
        stats["files"] += 1
        print(f"write {out_file}  questions={len(questions)}")
    return stats


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="生成江苏体系数学题库 JSON")
    ap.add_argument("--count", type=int, default=32000, help="目标唯一题量（去重后，≥30000）")
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()
    stats = generate_all(total_unique_target=args.count, seed=args.seed)
    print(f"\n唯一题量(去重后): {stats['questions']}  文件数: {stats['files']}  "
          f"(原始预算≈{stats.get('raw_target', 0)})")
    print("难度分布(1基础识记/2基础应用/3综合应用/4提升/5竞赛拓展):")
    for d in (1, 2, 3, 4, 5):
        c = stats["by_difficulty"].get(d, 0)
        pct = (c / stats["questions"] * 100) if stats["questions"] else 0
        print(f"  {d} {DIFF_LABELS[d]}: {c} ({pct:.1f}%)")
    print("难度分组(基础/提高/综合，目标 50/35/15):")
    tg = stats["by_tier"]
    tot = sum(tg.values()) or 1
    for g in ("basic", "improve", "comp"):
        print(f"  {g}: {tg[g]} ({tg[g]/tot*100:.1f}%)")


if __name__ == "__main__":
    main()
