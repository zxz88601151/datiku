# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""生成器共享辅助函数（与 generator / templates_extra 解耦，避免循环导入）。

本模块不依赖本包内任何其他模块，故 generator 与 templates_extra 均从此处导入，
彻底打破「generator 在 __main__ 下被二次加载」导致的循环导入死锁。
"""
from __future__ import annotations

import random
from typing import List, Tuple


def make_choice(rng: random.Random, correct: str, distractors: List[str]) -> Tuple[List[dict], str]:
    """构造选择题选项，返回 (options, answer_label)。"""
    opts = [{"label": "A", "text": correct, "correct": True}]
    for i, d in enumerate(distractors[:3]):
        opts.append({"label": chr(ord("A") + 1 + i), "text": d, "correct": False})
    rng.shuffle(opts)
    answer = next(o["label"] for o in opts if o["correct"])
    return opts, answer


def fmt_int(x) -> str:
    return str(int(round(x))) if isinstance(x, float) else str(x)


def _e(fn, concepts, steps, compute, hidden, subtype, error_causes=None):
    """题型矩阵注册表入口构造器（与 generator 内原 _e 完全一致）。"""
    return {"fn": fn, "meta": {"concepts": concepts, "steps": steps,
                               "compute": compute, "hidden": hidden},
            "subtype": subtype, "error_causes": list(error_causes or [])}
