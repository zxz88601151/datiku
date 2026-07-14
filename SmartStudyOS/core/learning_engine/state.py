# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""学生知识点状态模型。

每个学生 × 每个知识点 一条状态记录：
- mastery：掌握度 0-1
- wrong_count：累计错题数
- last_time：最近一次练习时间
- learning_curve：掌握度随时间的变化序列（用于成长追踪 / 画像）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class StudentKnowledgeState:
    student_id: int
    knowledge_id: int
    mastery: float = 0.0
    wrong_count: int = 0
    last_time: Optional[str] = None
    learning_curve: List[Tuple[str, float]] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: dict) -> "StudentKnowledgeState":
        from database.manager import DataManager
        curve = DataManager.loads(row.get("learning_curve"))
        return cls(
            student_id=row["student_id"],
            knowledge_id=row["knowledge_id"],
            mastery=row.get("mastery", 0.0),
            wrong_count=row.get("wrong_count", 0),
            last_time=row.get("last_time"),
            learning_curve=[(t, m) for t, m in curve] if curve else [],
        )
