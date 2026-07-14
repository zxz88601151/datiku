# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""JSON 解析器（标准库实现，无外部依赖）。

支持两种顶层结构：
- 直接为题目数组；
- 对象 {"questions": [...], "meta": {...}}。
每题字段见 JSON_FORMAT.md；选择题 options 为 [{label,text,correct}] 数组。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def parse_json(path: str) -> List[Dict[str, Any]]:
    text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "questions" in data:
        return data["questions"]
    raise ValueError("JSON 顶层应为题目数组或含 questions 字段的对象")
