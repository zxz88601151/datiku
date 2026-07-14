# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""题目数据模型。

题目不直接属于「章节」，而是绑定到「知识点」（knowledge_relation），
从而可被 Learning Engine 的掌握度/推荐分驱动——这是智能刷题的关键链路：
题目 → 知识点 → 学习状态 → 推荐分 → 组卷。

Phase 1.5-B 新增字段：
- exam_weight：中考/高考权重 1-5（普通/常考/重点/高频/核心），供 AI 规划提升优先级。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Question:
    id: Optional[int] = None
    subject: str = ""
    grade: str = ""
    type: str = "选择题"          # 选择题/填空题/计算题/证明题/实验题/作文题
    difficulty: int = 1           # 1-5（基础识记/基础应用/综合应用/提升/竞赛拓展）
    exam_weight: int = 1          # 1-5（普通/常考/重点/高频/核心）
    content: str = ""
    answer: str = ""
    analysis: str = ""
    knowledge_relation: List[int] = field(default_factory=list)  # 绑定知识点 id
    error_tags: List[str] = field(default_factory=list)          # 错因标签（Phase 1.5-D）

    @property
    def is_choice(self) -> bool:
        return self.type == "选择题"

    def to_row(self) -> dict:
        from database.manager import DataManager
        return {
            "subject": self.subject,
            "grade": self.grade,
            "type": self.type,
            "difficulty": self.difficulty,
            "exam_weight": self.exam_weight,
            "content": self.content,
            "answer": self.answer,
            "analysis": self.analysis,
            "knowledge_relation": DataManager.dumps(self.knowledge_relation),
            "error_tags": DataManager.dumps(self.error_tags),
        }

    @classmethod
    def from_row(cls, row: dict) -> "Question":
        from database.manager import DataManager
        return cls(
            id=row.get("id"),
            subject=row.get("subject", ""),
            grade=row.get("grade", ""),
            type=row.get("type", "选择题"),
            difficulty=row.get("difficulty", 1),
            exam_weight=row.get("exam_weight", 1),
            content=row.get("content", ""),
            answer=row.get("answer", ""),
            analysis=row.get("analysis", ""),
            knowledge_relation=DataManager.loads(row.get("knowledge_relation")),
            error_tags=DataManager.loads(row.get("error_tags")),
        )


@dataclass
class Option:
    id: Optional[int] = None
    question_id: Optional[int] = None
    label: str = ""
    text: str = ""
    is_correct: bool = False
