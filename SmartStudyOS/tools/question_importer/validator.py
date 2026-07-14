# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""数据质量校验。

导入前必须拦截：空题、空答案、非法难度/题型、知识点缺失、选择题选项不全、
exam_weight 越界等。
错误(error)导致该行被跳过；警告(warning)仍可入库但记入报告。
"""

from __future__ import annotations

from typing import Dict, List, Any, Tuple

ALLOWED_TYPES = {"选择题", "填空题", "计算题", "证明题", "实验题", "作文题"}


def _safe_int(v: Any) -> Any:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _knowledge_text(knowledge: Any) -> str:
    """将 knowledge（str 或 list）归一为用于判空的文本。"""
    if isinstance(knowledge, list):
        return " ".join(str(k) for k in knowledge)
    return str(knowledge)


def validate_row(row: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    subject = str(row.get("subject", "")).strip()
    grade = str(row.get("grade", "")).strip()
    knowledge = row.get("knowledge", "")
    knowledge_str = _knowledge_text(knowledge).strip()
    qtype = str(row.get("type", "")).strip()
    content = str(row.get("content", "")).strip()
    answer = str(row.get("answer", "")).strip()
    difficulty = _safe_int(row.get("difficulty"))

    if not subject:
        errors.append("学科为空")
    if not grade:
        errors.append("年级为空")
    if not knowledge_str:
        errors.append("知识点为空（无法绑定知识图谱）")
    if not qtype:
        errors.append("题型为空")
    elif qtype not in ALLOWED_TYPES:
        errors.append(f"题型非法：{qtype}")
    if not content:
        errors.append("题目内容为空")
    if not answer:
        errors.append("答案为空")

    if difficulty is None:
        warnings.append("难度缺失，默认设为 3")
        row["difficulty"] = 3
    elif not (1 <= difficulty <= 5):
        errors.append(f"难度超出范围(1-5)：{row.get('difficulty')}")
    else:
        row["difficulty"] = difficulty

    # exam_weight 范围（1-5）
    ew = row.get("exam_weight", 1)
    ew_i = _safe_int(ew)
    if ew_i is None:
        warnings.append("exam_weight 缺失/非法，默认设为 1")
        row["exam_weight"] = 1
    elif not (1 <= ew_i <= 5):
        warnings.append(f"exam_weight 超出范围(1-5)，已截断：{ew}")
        row["exam_weight"] = max(1, min(5, ew_i))
    else:
        row["exam_weight"] = ew_i

    options = row.get("options") or []
    if qtype == "选择题":
        if len(options) < 2:
            errors.append("选择题选项不足 2 个")
        correct = [o for o in options if o.get("correct")]
        if not correct:
            errors.append("选择题未标记正确选项")
        elif len(correct) > 1:
            errors.append("选择题存在多个正确选项")
        elif answer and answer.upper() != str(correct[0].get("label", "")).upper():
            warnings.append(f"答案({answer})与标记正确选项({correct[0].get('label')})不一致")

    return errors, warnings
