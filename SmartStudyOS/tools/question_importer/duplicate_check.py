# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""重复检测。

归一化键 = (学科, 年级, 题型, 题目内容去空白小写)。
- 库内去重：查询已存在题目；
- 批次内去重：维护本批已见键集合，避免同文件重复导入。
"""

from __future__ import annotations

from typing import Any, Dict, List

from database.manager import DataManager


def _knowledge_text(row: Dict[str, Any]) -> str:
    k = row.get("knowledge")
    if isinstance(k, (list, tuple)):
        return "·".join(str(x).strip().lower() for x in k)
    return str(k or "").strip().lower()


def norm_key(row: Dict[str, Any]) -> str:
    subject = str(row.get("subject", "")).strip().lower()
    grade = str(row.get("grade", "")).strip().lower()
    qtype = str(row.get("type", "")).strip().lower()
    content = str(row.get("content", "")).strip().lower()
    knowledge = _knowledge_text(row)
    # 知识点纳入去重键：同一题干若归属不同子知识点（如 绝对值·概念理解 vs
    # 绝对值·基础运算），代表不同训练目标，应视为不同题目而非重复。
    return "||".join([subject, grade, qtype, knowledge, content])


class DuplicateChecker:
    def __init__(self, dm: DataManager):
        self.dm = dm
        self._seen: set = set()

    def exists_in_db(self, key: str) -> bool:
        # 归一化键含知识点：相同题干若归属不同子知识点视为不同题目。
        subject, grade, qtype, knowledge, content = key.split("||")
        row = self.dm.query_one(
            "SELECT id FROM q_question WHERE subject=? AND grade=? AND type=? AND ktext=? AND content=?",
            (subject, grade, qtype, knowledge, content),
        )
        return row is not None

    def seen(self, key: str) -> bool:
        return key in self._seen

    def mark(self, key: str) -> None:
        self._seen.add(key)

    def is_duplicate(self, key: str) -> bool:
        if self.seen(key):
            return True
        if self.exists_in_db(key):
            # 同步进批次集合，避免后续再次命中
            self._seen.add(key)
            return True
        return False
