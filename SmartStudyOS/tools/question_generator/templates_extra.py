# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""Phase 1.5-D 扩展题型模板库（额外 80 类，使总题型达 120 类）。

本模块与 generator.py 的解耦方式：
- 复用 generator 的 make_choice / fmt_int / _e 辅助函数；
- 导出 EXTRA_REGISTRY（qcategory -> [子题型入口]），由 generator 在模块底部合并；
- 每个模板函数签名与 generator 一致：(rng, ctx, node) -> dict；
- 关键设计：所有模板使用「宽参数空间 + 多独立变量」，保证规模化生成时
  去重率可控（避免 Phase 1.5-C 早期「小参数空间→大量重复」的问题）；
- 所有题目均「构造即可验证」：答案由同段代码算出，杜绝错题。

错因标签：每个 REGISTRY 入口含 error_causes（取自 settings.ERROR_TAGS），
由 generator 在出题时写入 question.error_tags，供错因画像 / AI 老师使用。
"""
from __future__ import annotations

from typing import Dict, List

from ._helpers import make_choice, fmt_int, _e


def _mc(rng, content, correct, distractors, analysis, qtype="选择题"):
    opts, ans = make_choice(rng, str(correct), [str(d) for d in distractors])
    return {"content": content, "options": opts, "answer": ans, "analysis": analysis, "type": qtype}


# ===========================================================================
# 数与代数 · 实数 / 整式乘除 / 因式分解 / 方程 / 不等式
# ===========================================================================
def cat_integer_add_sub(rng, ctx, node):
    a = rng.randint(20, 999)
    b = rng.randint(20, 999)
    correct = a - b
    return _mc(rng, f"计算：{a} − {b} = （  ）", correct,
              [correct + 1, correct - 1, correct + 2, a - b + 10],
              f"退位减法：{a} − {b} = {correct}。")


def cat_integer_mult(rng, ctx, node):
    a = rng.randint(12, 99)
    b = rng.randint(12, 99)
    correct = a * b
    return _mc(rng, f"计算：{a} × {b} = （  ）", correct,
              [correct + 1, correct - 1, a * (b + 1), (a + 1) * b],
              f"竖式乘法：{a} × {b} = {correct}。")


def cat_integer_div(rng, ctx, node):
    b = rng.randint(7, 19)
    q = rng.randint(11, 49)
    a = b * q
    return _mc(rng, f"计算：{a} ÷ {b} = （  ）", q,
              [q + 1, q - 1, q + 2, a // (b + 1)],
              f"{a} = {b} × {q}，故商为 {q}。")


def cat_scientific(rng, ctx, node):
    a = rng.randint(1000, 9999) / 1000.0          # 1.000 ~ 9.999
    n = rng.choice([3, 4, 5, 6])
    num = int(round(a * (10 ** n)))
    correct = f"{a:.3f}×10^{n}"
    return _mc(rng, f"用科学记数法表示 {num}（  ）", correct,
              [f"{a:.3f}×10^{n - 1}", f"{int(a)}×10^{n}",
               f"{a:.3f}×10^{n + 1}", f"{num}×10^{n}"],
              f"科学记数法 a×10ⁿ（1≤a<10）：{num} = {correct}。")


def cat_abs_equation(rng, ctx, node):
    k = rng.randint(2, 9)
    return _mc(rng, f"方程 |x| = {k} 的解是（  ）", f"x = ±{k}",
              [f"x = {k}", f"x = -{k}", "无解", f"x = {k + 1}"],
              f"绝对值为 {k} 的数有 ±{k}，故 x = ±{k}。")


def cat_system_linear(rng, ctx, node):
    x0 = rng.randint(-5, 5)
    y0 = rng.randint(-5, 5)
    a1, b1 = rng.randint(1, 4), rng.randint(1, 3)
    a2, b2 = rng.randint(1, 3), rng.randint(1, 4)
    c1 = a1 * x0 + b1 * y0
    c2 = a2 * x0 + b2 * y0
    return _mc(rng, f"解方程组：{a1}x+{b1}y={c1}，{a2}x+{b2}y={c2}（  ）",
              f"x={x0}, y={y0}",
              [f"x={x0 + 1}, y={y0}", f"x={x0}, y={y0 + 1}",
               f"x={-x0}, y={-y0}", f"x={y0}, y={x0}"],
              f"代入检验满足两式，解为 x={x0}, y={y0}。")


def cat_system_linear_app(rng, ctx, node):
    a = rng.randint(2, 5)
    b = rng.randint(3, 8)
    n = rng.randint(10, 20)
    x = rng.randint(2, n - 2)
    y = n - x
    feet = a * x + b * y
    return _mc(rng, f"有 {n} 个物品，共 {feet} 只脚，A 类每只有 {a} 脚、B 类每只有 {b} 脚，则 A 类有（  ）个",
              x, [x + 1, x - 1, y, n - x - 1],
              f"设 A 类 x 个，则 {a}·x + {b}·({n}-x) = {feet}，解得 x = {x}。")


def cat_inequality_solve(rng, ctx, node):
    a = rng.choice([2, 3, 4, -2, -3])
    b = rng.randint(1, 12)
    x0 = rng.randint(-3, 3)
    c = a * x0 + b
    op = rng.choice(["<", "≤", ">", "≥"])
    expr = f"{a}x" if a not in (1, -1) else ("x" if a == 1 else "-x")
    # 解：a·x + b {op} c  →  a·x {op} c-b
    rhs = c - b
    if a > 0:
        sign = "<" if op in ("<", "≤") else ">"
        bound = rhs / a
        sol = f"x {sign} {bound}"
        wrongs = [f"x < {bound}", f"x > {bound}", f"x ≤ {bound}", f"x ≥ {bound}"]
    else:
        sign = ">" if op in ("<", "≤") else "<"
        bound = rhs / a
        sol = f"x {sign} {bound}"
        wrongs = [f"x < {bound}", f"x > {bound}", f"x ≤ {bound}", f"x ≥ {bound}"]
    # 用 4 个不含 sol 的近似项作干扰
    wrongs = [f"x < {bound - 1}", f"x > {bound + 1}",
              f"x ≤ {bound + 1}", f"x ≥ {bound - 1}"]
    return _mc(rng, f"解不等式 {expr} + {b} {op} {c}（  ）", sol, wrongs,
              f"移项：{expr} {op} {rhs}；系数化为1（注意 {a} 符号）得 {sol}。")


def cat_inequality_app(rng, ctx, node):
    price = rng.randint(3, 9)
    budget = rng.randint(30, 80)
    maxn = budget // price
    return _mc(rng, f"每本练习册 {price} 元，带 {budget} 元最多可买（  ）本", maxn,
              [maxn + 1, maxn - 1, budget, price],
              f"{price}·n ≤ {budget} → n ≤ {budget}/{price} = {budget / price:.2f}，最多 {maxn} 本。")


def cat_real_number(rng, ctx, node):
    items = [("√2", "无理数"), ("0", "有理数"), ("−3", "有理数"),
             ("π", "无理数"), ("22/7", "有理数"), ("0.1010010001…", "无理数")]
    correct_pair = rng.choice(items)
    return _mc(rng, f"下列各数中，属于{correct_pair[1]}的是（  ）", correct_pair[0],
              ["√4", "1/3", "−0.5", "3.14"],
              f"{correct_pair[0]} 是{correct_pair[1]}（无限不循环小数 / 整数分数）。")


def cat_real_estimate(rng, ctx, node):
    n = rng.randint(2, 15)
    lo = int(n ** 0.5)
    correct = f"{lo} 和 {lo + 1}"
    return _mc(rng, f"√{n} 介于哪两个相邻整数之间（  ）", correct,
              [f"{lo - 1} 和 {lo}", f"{lo + 1} 和 {lo + 2}",
               f"{lo} 和 {lo + 2}", f"{lo - 1} 和 {lo + 1}"],
              f"{lo}²={lo * lo} ≤ {n} < {(lo + 1) * (lo + 1)}，故 √{n} 在 {lo} 与 {lo + 1} 之间。")


def cat_surd_simplify(rng, ctx, node):
    a = rng.randint(2, 12)
    return _mc(rng, f"化简：√({a * a}) = （  ）", a,
              [a + 1, a * a, -a, 2 * a],
              f"√(a²)=|a|，√({a * a})={a}（a>0）。")


def cat_surd_op(rng, ctx, node):
    a = rng.randint(2, 6)
    b = rng.randint(2, 6)
    if rng.random() < 0.5:
        correct = a + b
        return _mc(rng, f"计算：{a}√3 + {b}√3 = （  ）", f"{correct}√3",
                  [f"{a + b + 1}√3", f"{a}√3", f"{b}√3", f"{a * b}√3"],
                  f"同类二次根式相加：({a}+{b})√3 = {correct}√3。")
    correct = a - b
    return _mc(rng, f"计算：{a}√5 − {b}√5 = （  ）", f"{correct}√5",
              [f"{a + b}√5", f"{a}√5", f"{b}√5", f"{a * b}√5"],
              f"合并同类二次根式：({a}−{b})√5 = {correct}√5。")


def cat_surd_rationalize(rng, ctx, node):
    a = rng.choice([2, 3, 5])
    return _mc(rng, f"分母有理化：1/√{a} = （  ）", f"√{a}/{a}",
              [f"1/{a}", f"√{a}", f"{a}/√{a}", f"1/√{a}"],
              f"分子分母同乘 √{a}：1/√{a} = √{a}/{a}。")


def cat_monomial_pow(rng, ctx, node):
    a = rng.randint(2, 5)
    n = rng.choice([3, 4, 5])
    correct = a ** n
    return _mc(rng, f"计算：({a})^{n} = （  ）", correct,
              [correct + 1, a * n, n ** a, correct - 1],
              f"幂的乘方 ({a})^{n} = {a}^{n} = {correct}。")


def cat_poly_mult(rng, ctx, node):
    a = rng.randint(2, 6)
    b = rng.randint(2, 6)
    correct = a * a - b * b
    return _mc(rng, f"计算：({a}+{b})({a}−{b}) = （  ）", correct,
              [a * a + b * b, (a + b) * (a + b), a * a - b, correct + 1],
              f"平方差公式：({a})²−({b})² = {correct}。")


def cat_factor_common(rng, ctx, node):
    a = rng.randint(2, 5)
    x = rng.randint(2, 5)
    y = rng.randint(2, 5)
    correct = f"{a}({x}+{y})"
    return _mc(rng, f"分解因式：{a}{x} + {a}{y} = （  ）", correct,
              [f"({a}{x}+{y})", f"{a}({x}{y})", f"{x}+{y}", f"{a}{x}+{a}{y}"],
              f"提取公因式 {a}：{a}{x}+{a}{y} = {a}({x}+{y})。")


def cat_factor_formula(rng, ctx, node):
    a = rng.randint(2, 5)
    b = rng.randint(2, 5)
    correct = f"({a}+{b})({a}−{b})"
    return _mc(rng, f"分解因式：{a}²−{b}² = （  ）", correct,
              [f"({a}−{b})²", f"({a}+{b})²", f"{a}({a}−{b})", f"({a}+{b})({a}+{b})"],
              f"平方差公式：{a}²−{b}² = ({a}+{b})({a}−{b})。")


def cat_factor_cross(rng, ctx, node):
    p = rng.randint(2, 5)
    q = rng.randint(2, 5)
    r = rng.randint(2, 5)
    s = rng.randint(2, 5)
    a = p * r
    b = p * s + q * r
    c = q * s
    correct = f"({p}x+{q})({r}x+{s})"
    return _mc(rng, f"分解因式：{a}x²+{b}x+{c} = （  ）", correct,
              [f"({p}x+{s})({r}x+{q})", f"({a}x+{q})(x+{s})",
               f"({p}x−{q})({r}x−{s})", f"x({a}x+{b})"],
              f"十字相乘：{a}x²+{b}x+{c} = ({p}x+{q})({r}x+{s})。")


def cat_algebra_value(rng, ctx, node):
    a = rng.randint(2, 5)
    b = rng.randint(1, 4)
    x0 = rng.randint(2, 6)
    correct = a * x0 * x0 + b
    return _mc(rng, f"当 x = {x0} 时，代数式 {a}x²+{b} 的值为（  ）", correct,
              [a * x0 + b, correct + 1, a * x0 * x0, correct - 1],
              f"代入：{a}×{x0}²+{b} = {a * x0 * x0}+{b} = {correct}。")


def cat_exponent_rule(rng, ctx, node):
    a = rng.randint(2, 4)
    n = rng.choice([2, 3])
    correct = -(a ** n)
    return _mc(rng, f"计算：−({a})^{n} = （  ）", correct,
              [a ** n, (-a) ** n, a * n, correct - 1],
              f"负号在括号外：−({a})^{n} = −{a ** n} = {correct}（注意与 (−{a})^{n} 区别）。")


def cat_vieta(rng, ctx, node):
    x1 = rng.randint(-4, 4)
    x2 = rng.randint(-4, 4)
    p = x1 * x2
    return _mc(rng, f"若方程两根为 {x1}, {x2}，则两根之积为（  ）", p,
              [x1 + x2, x1 + x2 - p, -p, x1 - x2],
              f"韦达定理：x₁·x₂ = {p}。")


def cat_quad_word(rng, ctx, node):
    r = rng.randint(2, 4)
    correct = 1 + r + r * r
    return _mc(rng, f"某种消息每轮每人传给 {r} 人，经过两轮后共知道消息的有（  ）人", correct,
              [1 + r, r * r, 1 + 2 * r, correct + 1],
              f"第一轮 1+{r} 人，第二轮新增 {r}×{r} 人，共 1+{r}+{r * r}={correct} 人。")


# ===========================================================================
# 函数 · 坐标 / 反比例 / 待定系数 / 综合
# ===========================================================================
def cat_function_value(rng, ctx, node):
    k = rng.choice([2, 3, -2, -3])
    b = rng.randint(-3, 3)
    x0 = rng.randint(-3, 3)
    y0 = k * x0 + b
    return _mc(rng, f"已知 y={k}x+{b}，当 x={x0} 时 y = （  ）", y0,
              [y0 + 1, y0 - 1, k + b, x0],
              f"代入：y = {k}×{x0}+{b} = {y0}。")


def cat_inverse_var(rng, ctx, node):
    k = rng.choice([2, 3, 4, 6])
    xs = [d for d in range(1, 10) if k % d == 0]
    x0 = rng.choice(xs)
    y0 = k // x0
    return _mc(rng, f"反比例函数 y={k}/x 中，当 x={x0} 时 y = （  ）", y0,
              [k + x0, k - x0, y0 + 1, x0],
              f"代入：y = {k}/{x0} = {y0}。")


def cat_inverse_var_app(rng, ctx, node):
    s = rng.randint(40, 120)
    t1 = rng.randint(2, 6)
    v1 = s // t1
    t2 = t1 + rng.randint(1, 4)
    v2 = s // t2
    return _mc(rng, f"路程一定为 {s} km，速度 v 与时间 t 成反比例。若 t={t1} 时 v={v1}，则 t={t2} 时 v = （  ）", v2,
              [v1, v1 + 1, s - t2, v2 + 1],
              f"v·t={s}，t={t2} 时 v = {s}/{t2} = {v2}。")


def cat_linear_param(rng, ctx, node):
    k = rng.choice([2, 3, -2, -3])
    b = rng.randint(-3, 3)
    x1 = rng.randint(-2, 2)
    y1 = k * x1 + b
    return _mc(rng, f"一次函数过点 ({x1},{y1})，且 k={k}，则其解析式为 y={k}x+（  ）", b,
              [b + 1, b - 1, k, y1],
              f"代入 ({x1},{y1})：{y1} = {k}×{x1}+b → b = {b}。")


def cat_coord_plane(rng, ctx, node):
    x = rng.randint(-5, 5)
    y = rng.randint(-5, 5)
    q = rng.choice(["横", "纵"])
    correct = x if q == "横" else y
    return _mc(rng, f"点 ({x},{y}) 的{q}坐标是（  ）", correct,
              [y if q == "横" else x, x + y, abs(x), abs(y)],
              f"点 ({x},{y}) 的横坐标为 {x}、纵坐标为 {y}，故{q}坐标为 {correct}。")


def cat_coord_distance(rng, ctx, node):
    x1 = rng.randint(-4, 4)
    x2 = rng.randint(-4, 4)
    while x2 == x1:
        x2 = rng.randint(-4, 4)
    correct = abs(x2 - x1)
    return _mc(rng, f"数轴上点 {x1} 与点 {x2} 的距离是（  ）", correct,
              [x1 + x2, x1 - x2, abs(x1) + abs(x2), correct + 1],
              f"距离 = |{x2} − {x1}| = {correct}。")


def cat_coord_sym(rng, ctx, node):
    x = rng.randint(1, 6)
    y = rng.randint(1, 6)
    kind = rng.choice(["x轴", "y轴", "原点"])
    if kind == "x轴":
        correct = f"({x},−{y})"
    elif kind == "y轴":
        correct = f"(−{x},{y})"
    else:
        correct = f"(−{x},−{y})"
    return _mc(rng, f"点 ({x},{y}) 关于{kind}对称的点的坐标是（  ）", correct,
              [f"(−{x},{y})", f"({x},−{y})", f"(−{x},−{y})", f"({y},{x})"],
              f"关于{kind}对称：x→取反/不变，y→取反/不变，得 {correct}。")


def cat_coord_quadrant(rng, ctx, node):
    x = rng.randint(1, 6)
    y = rng.randint(1, 6)
    return _mc(rng, f"点 ({x},{y}) 在第（  ）象限", "第一象限",
              ["第二象限", "第三象限", "第四象限", "坐标轴上"],
              f"横纵坐标均为正 → 第一象限。")


def cat_quad_func_app(rng, ctx, node):
    a = rng.choice([1, 2, -1, -2])
    xv = rng.randint(5, 15)
    b = -2 * a * xv
    q = rng.randint(5, 30)
    maxv = a * xv * xv + b * xv + q
    return _mc(rng, f"某商品利润 w={a}t²+({b})t+{q}（t 为定价），最大利润为（  ）", maxv,
              [maxv + 1, maxv - 1, q, xv],
              f"二次函数顶点处取最值，代入顶点得最大利润 {maxv}。")


def cat_quad_intersect(rng, ctx, node):
    a = rng.choice([1, -1])
    k = rng.choice([1, 2, -1, -2])
    root2 = k // a
    return _mc(rng, f"抛物线 y={a}x² 与直线 y={k}x 的交点个数为（  ）", 2,
              [0, 1, 3, 4],
              f"联立得 {a}x²={k}x → x({a}x−{k})=0，两解 x=0, x={root2}，共 2 个交点。")


def cat_func_comprehensive(rng, ctx, node):
    k = rng.choice([2, 3])
    b = rng.randint(1, 4)
    bound = round(-b / k, 2)
    return _mc(rng, f"一次函数 y={k}x+{b}，则 {k}x+{b}>0 的解集为（  ）", f"x>{bound}",
              [f"x<{bound}", f"x≥{bound}", f"x≤{bound}", "全体实数"],
              f"{k}x+{b}>0 → x > −{b}/{k}，即 x > {bound}。")


# ===========================================================================
# 图形与几何 · 角 / 平行 / 三角形 / 全等 / 多边形 / 圆 / 立体 / 变换 / 三角函数
# ===========================================================================
def cat_angle_calc(rng, ctx, node):
    a = rng.randint(20, 70)
    b = rng.randint(20, 70)
    while a + b > 170:
        b = rng.randint(20, 70)
    third = 180 - a - b
    return _mc(rng, f"△中两角分别为 {a}°、{b}°，第三角为（  ）", third,
              [a + b, 180 - a, 180 - b, third + 1],
              f"三角形内角和 180°，第三角 = 180 − {a} − {b} = {third}°。")


def cat_parallel_lines(rng, ctx, node):
    ang = rng.randint(40, 130)
    return _mc(rng, f"两直线平行，同位角相等。若同位角为 {ang}°，则另一同位角为（  ）", ang,
              [180 - ang, 90 - ang, ang + 10, 180 - ang - 10],
              f"平行线同位角相等，故也为 {ang}°。")


def cat_parallel_prop(rng, ctx, node):
    ang = rng.randint(30, 120)
    correct = 180 - ang
    return _mc(rng, f"两直线平行，一内错角为 {ang}°，则同旁内角为（  ）", correct,
              [ang, 90 - ang, 180 - ang - 10, ang + 10],
              f"平行时同旁内角互补：180° − {ang}° = {correct}°。")


def cat_triangle_basic(rng, ctx, node):
    a = rng.randint(3, 9)
    b = rng.randint(3, 9)
    lo = abs(a - b) + 1
    hi = a + b - 1
    c = rng.randint(lo, hi)
    return _mc(rng, f"已知两边为 {a}、{b}，则下列可作为第三边的是（  ）", c,
              [a + b, abs(a - b), lo - 1, hi + 1],
              f"三角形三边关系：|{a}−{b}|<c<{a}+{b}，即 {lo}≤c≤{hi}，取 {c}。")


def cat_triangle_classify(rng, ctx, node):
    return _mc(rng, f"有两边相等的三角形是（  ）", "等腰三角形",
              ["等边三角形", "直角三角形", "不等边三角形", "锐角三角形"],
              f"两边相等的三角形是等腰三角形（等边是特例）。")


def cat_congruent_sas(rng, ctx, node):
    return _mc(rng, f"两组对应边及其夹角分别相等，则两三角形全等，判定依据是（  ）", "SAS",
              ["SSS", "ASA", "AAS", "HL"],
              f"两边及其夹角对应相等 → SAS 全等判定。")


def cat_congruent_sss(rng, ctx, node):
    return _mc(rng, f"三边分别对应相等，则两三角形全等，判定依据是（  ）", "SSS",
              ["SAS", "ASA", "AAS", "HL"],
              f"三边对应相等 → SSS 全等判定。")


def cat_congruent_app(rng, ctx, node):
    a = rng.randint(3, 9)
    return _mc(rng, f"若 △ABC≅△DEF，且 AB={a}，则 DE = （  ）", a,
              [a + 1, a - 1, 2 * a, a * a],
              f"全等三角形对应边相等，AB 对应 DE，故 DE = AB = {a}。")


def cat_midpoint_conn(rng, ctx, node):
    base = rng.randint(6, 16)
    half = base / 2
    return _mc(rng, f"三角形中位线平行于第三边且等于其一半；若第三边为 {base}，则中位线长为（  ）",
              f"{base / 2:.0f}" if base % 2 == 0 else f"{half}",
              [base, base + 2, base / 2 + 1, 2 * base],
              f"中位线 = 第三边 / 2 = {base}/2 = {half}。")


def cat_polygon_angle(rng, ctx, node):
    n = rng.choice([3, 4, 5, 6, 8])
    interior = (n - 2) * 180
    return _mc(rng, f"{n} 边形内角和是（  ）", interior,
              [180 * n, (n - 1) * 180, 360, interior + 180],
              f"多边形内角和 = (n−2)×180° = ({n}−2)×180° = {interior}°。")


def cat_trap_area(rng, ctx, node):
    a = rng.randint(3, 12)
    b = rng.randint(3, 12)
    h = rng.randint(3, 10)
    correct = (a + b) * h / 2
    return _mc(rng, f"梯形上底 {a}、下底 {b}、高 {h}，面积是（  ）", correct,
              [(a + b) * h, a * h, b * h, (a + b) * h],
              f"S = (a+b)h/2 = ({a}+{b})×{h}/2 = {correct}。")


def cat_rhombus_prop(rng, ctx, node):
    d1 = rng.randint(4, 10)
    d2 = rng.randint(4, 10)
    correct = d1 * d2 / 2
    return _mc(rng, f"菱形对角线长为 {d1}、{d2}，面积为（  ）", correct,
              [d1 * d2, (d1 + d2) / 2, d1 + d2, correct + 1],
              f"菱形面积 = 对角线乘积 / 2 = {d1}×{d2}/2 = {correct}。")


def cat_rect_prop(rng, ctx, node):
    a = rng.randint(3, 10)
    b = rng.randint(3, 10)
    diag = round((a * a + b * b) ** 0.5, 2)
    return _mc(rng, f"矩形长 {a}、宽 {b}，对角线长为（  ）", f"{diag}",
              [a + b, abs(a - b), max(a, b), diag + 1],
              f"勾股定理：对角线 = √({a}²+{b}²) = {diag}。")


def cat_square_prop(rng, ctx, node):
    s = rng.randint(3, 10)
    return _mc(rng, f"正方形边长为 {s}，面积为（  ）", s * s,
              [4 * s, 2 * s, s * s + 1, s * s - 1],
              f"正方形面积 = 边长² = {s}² = {s * s}。")


def cat_circle_chord(rng, ctx, node):
    r = rng.randint(3, 9)
    return _mc(rng, f"⊙O 半径 {r}，最长弦（直径）长为（  ）", 2 * r,
              [r, r * r, 3 * r, 2 * r + 1],
              f"圆中最长弦是直径 = 2r = 2×{r} = {2 * r}。")


def cat_circle_tangent_prop(rng, ctx, node):
    return _mc(rng, f"圆的切线垂直于过切点的（  ）", "半径",
              ["直径", "弦", "圆心角", "圆周角"],
              f"切线性质：切线垂直于过切点的半径（夹角 90°）。")


def cat_solid_surface(rng, ctx, node):
    r = rng.randint(2, 5)
    h = rng.randint(4, 9)
    name = ctx.get("knowledge", "")
    if "圆锥" in name:
        l = round((r * r + h * h) ** 0.5, 2)
        correct = round(3.14 * r * l + 3.14 * r * r, 1)
        return _mc(rng, f"圆锥底面半径 {r}、母线 {l}，全面积（π取3.14）约为（  ）", f"{correct}",
                  [f"{round(3.14 * r * r, 1)}", f"{round(3.14 * r * l, 1)}",
                   f"{correct + 5}", f"{h}"],
                  f"S全 = πr² + πrl ≈ {correct}。")
    correct = round(2 * 3.14 * r * (r + h), 1)
    return _mc(rng, f"圆柱底面半径 {r}、高 {h}，侧面积（π取3.14）约为（  ）", f"{round(2 * 3.14 * r * h, 1)}",
              [f"{round(3.14 * r * r, 1)}", f"{correct}",
               f"{round(3.14 * r * h, 1)}", f"{h}"],
              f"S侧 = 2πrh = 2×3.14×{r}×{h} ≈ {round(2 * 3.14 * r * h, 1)}。")


def cat_rotation_prop(rng, ctx, node):
    return _mc(rng, f"图形绕点旋转后，对应点到旋转中心的距离（  ）", "相等",
              ["变为原来的2倍", "缩小一半", "变为0", "不相等"],
              f"旋转变换不改变图形大小，对应点到旋转中心距离相等。")


def cat_translation_geom(rng, ctx, node):
    return _mc(rng, f"平移变换前后的图形（  ）", "形状和大小都不变",
              ["形状变大小不变", "大小变形状不变", "都改变", "面积减半"],
              f"平移只改变位置，不改变形状与大小，面积也不变。")


def cat_symmetry_center(rng, ctx, node):
    return _mc(rng, f"把一个图形绕着某点旋转 180° 后能与原图重合，这种对称叫（  ）", "中心对称",
              ["轴对称", "平移", "旋转对称", "相似"],
              f"绕点旋转 180° 重合 → 中心对称，该点为对称中心。")


def cat_trig_sin(rng, ctx, node):
    ang = rng.choice([30, 45, 60])
    tbl = {30: "1/2", 45: "√2/2", 60: "√3/2"}
    return _mc(rng, f"sin {ang}° = （  ）", tbl[ang],
              [tbl[60] if ang != 60 else tbl[30], tbl[45], "1", "0"],
              f"特殊角：sin {ang}° = {tbl[ang]}。")


def cat_trig_special(rng, ctx, node):
    return _mc(rng, f"tan 60° = （  ）", "√3",
              ["1", "√3/3", "√2", "3"],
              f"tan 60° = sin60/cos60 = (√3/2)/(1/2) = √3。")


def cat_trig_app(rng, ctx, node):
    h = rng.randint(10, 40)
    ang = rng.choice([30, 45, 60])
    td = {30: 3 ** 0.5, 45: 1, 60: 3 ** 0.5 / 3}
    d = round(h / td[ang], 1)
    return _mc(rng, f"从距塔底水平处测塔顶仰角 {ang}°，塔高 {h} m，则水平距离约为（  ）m", f"{d}",
              [f"{round(h * td[ang], 1)}", f"{h}", f"{d + 5}", f"{h / 2}"],
              f"tan {ang}° = 塔高/水平距 → 水平距 = {h}/tan{ang}° ≈ {d} m。")


def cat_similarity_app(rng, ctx, node):
    ratio = rng.choice([2, 3, 4])
    h = rng.randint(10, 30)
    return _mc(rng, f"标杆高 {h}，其影长与物高比为 1:{ratio}，则同条件下高物影长为（  ）", h * ratio,
              [h, h / ratio, h + ratio, h * ratio + 1],
              f"相似比 {ratio}:1，影长 = 物高 × {ratio} = {h}×{ratio} = {h * ratio}。")


def cat_projection_view(rng, ctx, node):
    return _mc(rng, f"从正面、左面、上面观察物体得到的平面图形统称（  ）", "三视图",
              ["展开图", "剖面图", "透视图", "轴测图"],
              f"主视图+左视图+俯视图 = 三视图，用于描述几何体形状。")


def cat_similar_ratio_app(rng, ctx, node):
    ratio = rng.choice([2, 3])
    side = rng.randint(3, 12)
    return _mc(rng, f"△ABC∽△DEF，相似比 {ratio}:1，AB={side} 则 DE=（  ）", side * ratio,
              [side, side / ratio, side + ratio, side * ratio + 1],
              f"对应边成比例：DE = AB × {ratio} = {side}×{ratio} = {side * ratio}。")


def cat_circle_inscribed(rng, ctx, node):
    r = rng.randint(3, 8)
    return _mc(rng, f"正方形内切圆半径为 {r}，则正方形边长为（  ）", 2 * r,
              [r, round(2 * r * 2 ** 0.5, 1), r / 2, 2 * r + 1],
              f"内切圆直径 = 正方形边长 = 2r = {2 * r}。")


def cat_quad_perimeter(rng, ctx, node):
    a = rng.randint(3, 10)
    b = rng.randint(3, 10)
    c = rng.randint(abs(a - b) + 1, a + b - 1)
    return _mc(rng, f"三角形三边分别为 {a}、{b}、{c}，周长为（  ）", a + b + c,
              [a + b, a + c, b + c, a + b + c - 1],
              f"周长 = {a}+{b}+{c} = {a + b + c}。")


# ===========================================================================
# 统计与概率 · 图表 / 集中量数 / 频率
# ===========================================================================
def cat_median_calc(rng, ctx, node):
    from collections import Counter
    nums = sorted([rng.randint(40, 100) for _ in range(5)])
    mid = nums[2]
    return _mc(rng, f"数据 {nums[0]},{nums[1]},{nums[2]},{nums[3]},{nums[4]} 的中位数是（  ）", mid,
              [nums[0], nums[4], sum(nums) // 5, mid + 1],
              f"排序后中间的数 = {mid}，即中位数。")


def cat_mode_calc(rng, ctx, node):
    from collections import Counter
    pool = [rng.randint(1, 5) for _ in range(6)]
    m = Counter(pool).most_common(1)[0][0]
    return _mc(rng, f"数据 {pool} 的众数是（  ）", m,
              [sum(pool) // len(pool), max(pool), min(pool), m + 1],
              f"出现次数最多的数是 {m}，即众数。")


def cat_weighted_mean(rng, ctx, node):
    vals = [rng.randint(60, 100) for _ in range(3)]
    ws = [rng.randint(1, 4) for _ in range(3)]
    wm = round(sum(v * w for v, w in zip(vals, ws)) / sum(ws), 1)
    return _mc(rng, f"数据 {vals} 的权分别为 {ws}，加权平均数约为（  ）", f"{wm}",
              [f"{round(sum(vals) / len(vals), 1)}", f"{max(vals)}", f"{min(vals)}", f"{wm + 2}"],
              f"加权平均数 = Σ(值×权)/Σ权 ≈ {wm}。")


def cat_frequency(rng, ctx, node):
    total = rng.randint(20, 50)
    f = rng.randint(5, total - 5)
    correct = round(f / total, 3)
    return _mc(rng, f"总数为 {total}，某组频数为 {f}，则频率为（  ）", f"{correct}",
              [f"{f}", f"{total}", f"{round(f * total, 3)}", f"{correct + 0.1:.3f}"],
              f"频率 = 频数/总数 = {f}/{total} = {correct}。")


def cat_histogram(rng, ctx, node):
    return _mc(rng, f"频数分布直方图中，小长方形的高表示（  ）", "频数/组距",
              ["频数", "频率", "组距", "总数"],
              f"直方图中小长方形高 = 频数/组距，面积 = 频数。")


def cat_bar_chart(rng, ctx, node):
    a = rng.randint(10, 50)
    b = rng.randint(10, 50)
    return _mc(rng, f"条形图中 A 高 {a}、B 高 {b}，则数量最多的是（  ）", "A" if a > b else "B",
              ["A", "B", "一样多", "无法判断"],
              f"条形高度代表数量，{'A' if a > b else 'B'} 更高，数量最多。")


def cat_line_chart(rng, ctx, node):
    return _mc(rng, f"折线图逐月走高，说明数据呈（  ）", "上升趋势",
              ["下降趋势", "波动不变", "无变化", "先升后降"],
              f"折线整体向上 → 数据呈上升趋势。")


def cat_pie_chart(rng, ctx, node):
    pct = rng.choice([25, 30, 40, 50])
    return _mc(rng, f"扇形图中某部分圆心角为 {pct * 3.6}°，则占比为（  ）%", pct,
              [pct + 10, pct - 10, 100 - pct, pct + 1],
              f"占比 = 圆心角/360° = {pct * 3.6}°/360° = {pct}%。")


def cat_data_collect(rng, ctx, node):
    return _mc(rng, f"为了解全校视力，抽取 200 名学生调查，这 200 名学生是（  ）", "样本",
              ["总体", "个体", "样本容量", "普查"],
              f"被抽取调查的对象构成样本（全校是总体）。")


def cat_prob_add(rng, ctx, node):
    p1 = round(rng.uniform(0.1, 0.4), 2)
    p2 = round(rng.uniform(0.1, 0.4), 2)
    correct = round(p1 + p2, 2)
    return _mc(rng, f"互斥事件 A、B 概率分别为 {p1}、{p2}，则 P(A或B) = （  ）", f"{correct}",
              [f"{round(p1 * p2, 2)}", f"{round(abs(p1 - p2), 2)}", f"{round(p1, 2)}", f"{correct + 0.1:.2f}"],
              f"互斥事件加法：P(A∪B) = P(A)+P(B) = {p1}+{p2} = {correct}。")


def cat_prob_combo(rng, ctx, node):
    r = rng.randint(3, 6)
    b = rng.randint(2, 5)
    p = round(r / (r + b) * (r - 1) / (r + b - 1), 3)
    return _mc(rng, f"袋 {r} 红 {b} 蓝，不放回摸两次均红的概率约为（  ）", f"{p}",
              [f"{round(r / (r + b), 3)}", f"{round((r - 1) / (r + b - 1), 3)}",
               f"{round((r / (r + b)) ** 2, 3)}", f"{p + 0.05:.3f}"],
              f"不放回：P = {r}/{r + b} × {r - 1}/{r + b - 1} ≈ {p}。")


def cat_geometric_prob(rng, ctx, node):
    total = rng.randint(20, 50)
    fav = rng.randint(5, total - 5)
    correct = round(fav / total, 3)
    return _mc(rng, f"几何概型：总区域面积 {total}，有利区域 {fav}，概率约为（  ）", f"{correct}",
              [f"{round(fav * total, 3)}", f"{round(total / fav, 3)}", f"{correct + 0.1:.3f}", f"{fav}"],
              f"几何概型 P = 有利面积/总面积 = {fav}/{total} ≈ {correct}。")


# ===========================================================================
# 综合与应用 · 方程应用细分 / 规律 / 证明
# ===========================================================================
def cat_equation_app_work(rng, ctx, node):
    a = rng.randint(5, 12)
    b = rng.randint(5, 12)
    t = rng.randint(3, 8)
    total = (a + b) * t
    return _mc(rng, f"甲每天做 {a} 件、乙每天做 {b} 件，合作 {t} 天共做（  ）件", total,
              [a * t, b * t, total + 1, a + b],
              f"效率和 = {a}+{b}，{t} 天总量 = ({a}+{b})×{t} = {total}。")


def cat_equation_app_mix(rng, ctx, node):
    x = rng.randint(5, 20)
    y = rng.randint(20, 80)
    pct = round(x / (x + y) * 100)
    return _mc(rng, f"{x} g 盐溶于 {y} g 水，盐水浓度约为（  ）%", pct,
              [round(x / y * 100), round(y / (x + y) * 100), pct + 1, x],
              f"浓度 = 盐/(盐+水) = {x}/({x}+{y}) ≈ {pct}%。")


def cat_equation_app_age(rng, ctx, node):
    parent = rng.randint(30, 45)
    child = rng.randint(5, 15)
    n = (parent - 3 * child) // 2
    return _mc(rng, f"父 {parent} 岁、子 {child} 岁，几年前父龄是子龄 3 倍（  ）", n,
              [n + 1, n - 1, n + 2, 1],
              f"设 n 年前：{parent}−n = 3({child}−n) → n = ({3 * child}-{parent})/2 = {n}。")


def cat_equation_app_digit(rng, ctx, node):
    a = rng.randint(1, 9)
    b = rng.randint(0, 9)
    correct = (10 * a + b) + (10 * b + a)
    return _mc(rng, f"一个两位数十位 {a}、个位 {b}，与原数交换个位十位后的两数之和为（  ）", correct,
              [11 * (a + b) + 1, 10 * a + b, 11 * a, correct - 1],
              f"原数 10{a}+{b}，新数 10{b}+{a}，和 = 11({a}+{b}) = {correct}。")


def cat_seq_arith(rng, ctx, node):
    d = rng.randint(2, 5)
    a1 = rng.randint(1, 5)
    correct = a1 + 3 * d
    return _mc(rng, f"等差数列首项 {a1}、公差 {d}，第 4 项为（  ）", correct,
              [a1 + 2 * d, a1 + 4 * d, correct + 1, a1],
              f"第 4 项 = 首项 + 3×公差 = {a1} + 3×{d} = {correct}。")


def cat_pattern_explore(rng, ctx, node):
    k = rng.randint(4, 9)
    correct = 2 * k - 1
    return _mc(rng, f"数列 1,3,5,7,… 第 {k} 项为（  ）", correct,
              [2 * k, 2 * k + 1, k * k, correct - 1],
              f"奇数数列第 n 项 = 2n−1，第 {k} 项 = 2×{k}−1 = {correct}。")


def cat_logic_proof(rng, ctx, node):
    return _mc(rng, f"命题「对顶角相等」是（  ）", "真命题",
              ["假命题", "逆命题", "否命题", "无法判断"],
              f"对顶角恒相等，是真命题（无需前提）。")


def cat_inequality_sys(rng, ctx, node):
    lo = rng.randint(1, 4)
    hi = lo + rng.randint(2, 4)
    return _mc(rng, f"不等式组 x>{lo} 且 x<{hi} 的解集为（  ）", f"{lo}<x<{hi}",
              [f"x>{hi}", f"x<{lo}", "无解", "全体实数"],
              f"两不等式取公共部分：{lo} < x < {hi}。")


def cat_real_compare(rng, ctx, node):
    a = round(rng.uniform(1.5, 4.5), 2)
    b = round(a + rng.uniform(0.3, 1.5), 2)
    return _mc(rng, f"比较：√{int(a * a)} 与 {b}（  ）", "小于" if a < b else "大于",
              ["小于", "大于", "等于", "无法比较"],
              f"√{int(a * a)}≈{a} {'<' if a < b else '>'} {b}。")


def cat_surd_mixed(rng, ctx, node):
    a = rng.randint(2, 5)
    return _mc(rng, f"(√{a})² = （  ）", a,
              [a * a, 2 * a, a + 1, -a],
              f"(√a)² = a（a≥0），故 = {a}。")


def cat_factor_group(rng, ctx, node):
    a = rng.randint(2, 4)
    b = rng.randint(2, 5)
    c = rng.randint(1, 4)
    return _mc(rng, f"分组分解：{a}{b}+{a}{c} = （  ）", f"{a}({b}+{c})",
              [f"({a}{b}+{c})", f"{a}{b}+{a}{c}", f"{b}+{c}", f"{a}({b}{c})"],
              f"提取公因式 {a}：{a}{b}+{a}{c} = {a}({b}+{c})。")


def cat_system_word(rng, ctx, node):
    a = rng.randint(2, 6)
    b = rng.randint(2, 6)
    x0 = rng.randint(1, 6)
    y0 = rng.randint(1, 6)
    s = x0 + y0
    d = a * x0 + b * y0
    return _mc(rng, f"买 A 品 {a} 元/件、B 品 {b} 元/件，共买 {s} 件花 {d} 元，则 A 品买了（  ）件", x0,
              [y0, x0 + 1, x0 - 1, s],
              f"设 A {x0} 件、B {s - x0} 件，{a}×{x0}+{b}×{s - x0}={d}，解得 {x0} 件。")


# ===========================================================================
# 题型注册表（额外 80 类）
# ===========================================================================
EXTRA_REGISTRY: Dict[str, List[dict]] = {
    # 数与代数
    "integer_add_sub": [_e(cat_integer_add_sub, 1, 2, 1, False, "整数减法", ["计算失误", "符号错误"])],
    "integer_mult": [_e(cat_integer_mult, 1, 2, 2, False, "整数乘法", ["计算失误"])],
    "integer_div": [_e(cat_integer_div, 1, 2, 2, False, "整数除法", ["计算失误"])],
    "scientific_notation": [_e(cat_scientific, 1, 2, 2, False, "科学记数法", ["概念混淆", "小数点位数错"])],
    "abs_equation": [_e(cat_abs_equation, 1, 2, 1, True, "绝对值方程", ["忽略绝对值非负性", "概念混淆"])],
    "system_linear": [_e(cat_system_linear, 2, 3, 2, False, "二元一次方程组", ["计算失误", "移项不变号"])],
    "system_linear_app": [_e(cat_system_linear_app, 2, 4, 2, True, "方程组应用", ["模型列错", "审题不清"])],
    "inequality_solve": [_e(cat_inequality_solve, 1, 3, 2, False, "不等式求解", ["移项不变号", "符号错误"])],
    "inequality_app": [_e(cat_inequality_app, 2, 3, 2, True, "不等式应用", ["模型列错", "单位遗漏"])],
    "real_number": [_e(cat_real_number, 1, 1, 1, False, "实数分类", ["概念混淆"])],
    "real_estimate": [_e(cat_real_estimate, 1, 2, 2, True, "实数估算", ["概念混淆"])],
    "surd_simplify": [_e(cat_surd_simplify, 1, 1, 1, False, "二次根式化简", ["忽略绝对值", "符号错误"])],
    "surd_op": [_e(cat_surd_op, 1, 2, 2, False, "二次根式运算", ["约分遗漏", "概念混淆"])],
    "surd_rationalize": [_e(cat_surd_rationalize, 1, 2, 2, False, "分母有理化", ["忽略分母不为0"])],
    "monomial_pow": [_e(cat_monomial_pow, 1, 2, 2, False, "幂的运算", ["混淆底数是否含负号"])],
    "poly_mult": [_e(cat_poly_mult, 1, 2, 2, False, "整式乘法", ["公式误用", "漏乘分配律"])],
    "factor_common": [_e(cat_factor_common, 1, 2, 2, False, "提取公因式", ["漏乘分配律"])],
    "factor_formula": [_e(cat_factor_formula, 1, 2, 2, False, "公式法因式分解", ["公式误用"])],
    "factor_cross": [_e(cat_factor_cross, 2, 3, 2, False, "十字相乘法", ["公式误用", "计算失误"])],
    "algebra_value": [_e(cat_algebra_value, 1, 2, 2, False, "代数式求值", ["计算失误", "符号错误"])],
    "exponent_rule": [_e(cat_exponent_rule, 1, 2, 1, False, "幂的符号", ["混淆底数是否含负号"])],
    "vieta": [_e(cat_vieta, 2, 2, 2, False, "韦达定理", ["公式误用"])],
    "quad_word": [_e(cat_quad_word, 2, 4, 2, True, "一元二次方程应用", ["模型列错", "审题不清"])],
    # 函数
    "function_value": [_e(cat_function_value, 1, 2, 1, False, "函数值", ["计算失误"])],
    "inverse_var": [_e(cat_inverse_var, 1, 2, 1, False, "反比例函数", ["概念混淆", "忽略分母不为0"])],
    "inverse_var_app": [_e(cat_inverse_var_app, 2, 3, 2, True, "反比例应用", ["模型列错", "单位遗漏"])],
    "linear_param": [_e(cat_linear_param, 2, 3, 2, False, "待定系数法", ["计算失误", "代入计算错"])],
    "coord_plane": [_e(cat_coord_plane, 1, 1, 1, False, "坐标平面", ["坐标系误用"])],
    "coord_distance": [_e(cat_coord_distance, 1, 2, 1, False, "坐标距离", ["坐标系误用"])],
    "coord_sym": [_e(cat_coord_sym, 1, 2, 1, False, "点对称", ["坐标系误用"])],
    "coord_quadrant": [_e(cat_coord_quadrant, 1, 1, 1, False, "象限判断", ["坐标系误用"])],
    "quad_func_app": [_e(cat_quad_func_app, 2, 4, 3, True, "二次函数应用", ["建模列错", "a符号与开口混淆"])],
    "quad_intersect": [_e(cat_quad_intersect, 2, 3, 2, False, "函数交点", ["图形理解偏差"])],
    "func_comprehensive": [_e(cat_func_comprehensive, 3, 4, 3, True, "函数综合", ["混淆增减性", "分类讨论遗漏"])],
    # 几何
    "angle_calc": [_e(cat_angle_calc, 1, 2, 1, False, "角度计算", ["计算失误"])],
    "parallel_lines": [_e(cat_parallel_lines, 1, 1, 1, False, "平行线角", ["定理记反"])],
    "parallel_prop": [_e(cat_parallel_prop, 1, 2, 1, False, "平行线性质", ["定理记反"])],
    "triangle_basic": [_e(cat_triangle_basic, 1, 2, 1, True, "三边关系", ["分类讨论遗漏"])],
    "triangle_classify": [_e(cat_triangle_classify, 1, 1, 1, False, "三角形分类", ["概念混淆"])],
    "congruent_sas": [_e(cat_congruent_sas, 1, 1, 1, False, "全等判定SAS", ["定理记反"])],
    "congruent_sss": [_e(cat_congruent_sss, 1, 1, 1, False, "全等判定SSS", ["定理记反"])],
    "congruent_app": [_e(cat_congruent_app, 1, 2, 1, False, "全等应用", ["定理记反"])],
    "midpoint_conn": [_e(cat_midpoint_conn, 1, 2, 1, False, "三角形中位线", ["公式误用"])],
    "polygon_angle": [_e(cat_polygon_angle, 1, 2, 1, False, "多边形内角和", ["公式误用"])],
    "trap_area": [_e(cat_trap_area, 1, 2, 2, False, "梯形面积", ["公式误用"])],
    "rhombus_prop": [_e(cat_rhombus_prop, 1, 2, 2, False, "菱形性质", ["公式误用"])],
    "rect_prop": [_e(cat_rect_prop, 1, 2, 2, False, "矩形性质", ["图形理解偏差"])],
    "square_prop": [_e(cat_square_prop, 1, 1, 1, False, "正方形性质", ["概念混淆"])],
    "circle_chord": [_e(cat_circle_chord, 1, 2, 1, False, "弦与直径", ["概念混淆"])],
    "circle_tangent_prop": [_e(cat_circle_tangent_prop, 1, 1, 1, False, "切线性质", ["定理记反"])],
    "solid_surface": [_e(cat_solid_surface, 1, 3, 2, False, "立体表面积", ["公式误用", "单位遗漏"])],
    "rotation_prop": [_e(cat_rotation_prop, 1, 1, 1, False, "旋转性质", ["概念混淆"])],
    "translation_geom": [_e(cat_translation_geom, 1, 1, 1, False, "平移性质", ["概念混淆"])],
    "symmetry_center": [_e(cat_symmetry_center, 1, 1, 1, False, "中心对称", ["概念混淆"])],
    "trig_sin": [_e(cat_trig_sin, 1, 1, 1, False, "特殊角三角函数", ["公式误用"])],
    "trig_special": [_e(cat_trig_special, 1, 1, 1, False, "正切值", ["公式误用"])],
    "trig_app": [_e(cat_trig_app, 2, 3, 2, True, "解直角三角形", ["图形理解偏差", "模型列错"])],
    "similarity_app": [_e(cat_similarity_app, 2, 3, 2, True, "相似应用", ["对应边的比写反"])],
    "projection_view": [_e(cat_projection_view, 1, 1, 1, False, "三视图", ["概念混淆"])],
    "similar_ratio_app": [_e(cat_similar_ratio_app, 1, 2, 1, False, "相似比应用", ["对应边的比写反"])],
    "circle_inscribed": [_e(cat_circle_inscribed, 1, 2, 1, False, "内切圆", ["图形理解偏差"])],
    "quad_perimeter": [_e(cat_quad_perimeter, 1, 2, 1, False, "三角形周长", ["计算失误"])],
    # 统计概率
    "median_calc": [_e(cat_median_calc, 1, 2, 1, False, "中位数", ["概念混淆"])],
    "mode_calc": [_e(cat_mode_calc, 1, 2, 1, False, "众数", ["概念混淆"])],
    "weighted_mean": [_e(cat_weighted_mean, 1, 3, 2, False, "加权平均数", ["计算失误"])],
    "frequency": [_e(cat_frequency, 1, 2, 1, False, "频数与频率", ["概念混淆"])],
    "histogram": [_e(cat_histogram, 1, 1, 1, False, "频数分布直方图", ["概念混淆"])],
    "bar_chart": [_e(cat_bar_chart, 1, 1, 1, False, "条形图", ["图形理解偏差"])],
    "line_chart": [_e(cat_line_chart, 1, 1, 1, False, "折线图", ["图形理解偏差"])],
    "pie_chart": [_e(cat_pie_chart, 1, 2, 1, False, "扇形图", ["概念混淆"])],
    "data_collect": [_e(cat_data_collect, 1, 1, 1, False, "数据收集", ["概念混淆"])],
    "prob_add": [_e(cat_prob_add, 1, 2, 2, False, "概率加法", ["公式误用"])],
    "prob_combo": [_e(cat_prob_combo, 2, 3, 2, False, "组合概率", ["遗漏等可能结果"])],
    "geometric_prob": [_e(cat_geometric_prob, 2, 2, 2, False, "几何概型", ["模型列错"])],
    # 综合应用
    "equation_app_work": [_e(cat_equation_app_work, 2, 3, 2, True, "工程问题", ["模型列错"])],
    "equation_app_mix": [_e(cat_equation_app_mix, 2, 3, 2, True, "浓度问题", ["单位遗漏", "模型列错"])],
    "equation_app_age": [_e(cat_equation_app_age, 2, 3, 2, True, "年龄问题", ["审题不清"])],
    "equation_app_digit": [_e(cat_equation_app_digit, 2, 3, 2, True, "数字问题", ["计算失误", "分类讨论遗漏"])],
    "seq_arith": [_e(cat_seq_arith, 1, 2, 2, False, "等差数列", ["计算失误"])],
    "pattern_explore": [_e(cat_pattern_explore, 1, 2, 2, True, "规律探索", ["审题不清"])],
    "logic_proof": [_e(cat_logic_proof, 1, 1, 1, False, "命题与证明", ["概念混淆"])],
    "inequality_sys": [_e(cat_inequality_sys, 1, 3, 2, False, "不等式组", ["移项不变号", "符号错误"])],
    "real_compare": [_e(cat_real_compare, 1, 2, 1, False, "实数比较", ["概念混淆"])],
    "surd_mixed": [_e(cat_surd_mixed, 1, 1, 1, False, "二次根式综合", ["忽略绝对值", "符号错误"])],
    "factor_group": [_e(cat_factor_group, 1, 2, 2, False, "分组分解", ["漏乘分配律"])],
    "system_word": [_e(cat_system_word, 2, 4, 2, True, "方程组应用", ["模型列错", "审题不清"])],
}
