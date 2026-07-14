# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""知识节点数据模型。

知识点 = 知识世界的「节点」。节点之间通过 parent_id 形成层级树，
通过 relation 形成跨链接「边」。掌握度(mastery)在节点上做缓存，
真实掌握度来自 learning_state 表（由 Learning Engine 维护）。

Phase 1.5-B 富化字段（知识卡片标准）：
- summary / formula_list / examples / pitfalls / errors：知识卡片内容
- important：是否苏科版核心考点（驱动 importance 权重）
- predecessor / successor：先修 / 后继知识点（名称），构成学习路径
- node_type：knowledge / concept / example / error
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class KnowledgeNode:
    id: Optional[int] = None
    name: str = ""
    subject: str = ""
    grade: str = ""
    parent_id: Optional[int] = None
    difficulty: int = 1            # 1-5，难度
    mastery: float = 0.0           # 0-1，缓存值（来自学习状态）
    importance: float = 0.5        # 0-1，重要程度（推荐分用）
    relation: List[int] = field(default_factory=list)   # 关联节点 id（跨链接）
    content: str = ""              # 概念
    formula: str = ""              # 公式（文本）
    examples: str = ""             # 例题
    pitfalls: str = ""             # 易错点
    # ---- Phase 1.5-B 富化字段 ----
    summary: str = ""               # 概念摘要（知识卡片标题下正文）
    node_type: str = "knowledge"    # knowledge / concept / example / error
    important: bool = False         # 是否重点（苏科版核心考点）
    predecessor: List[str] = field(default_factory=list)  # 先修知识点（名称）
    successor: List[str] = field(default_factory=list)    # 后继知识点（名称）
    errors: List[str] = field(default_factory=list)       # 易错点清单
    formula_list: List[str] = field(default_factory=list) # 公式列表

    def to_row(self) -> dict:
        from database.manager import DataManager
        return {
            "name": self.name,
            "subject": self.subject,
            "grade": self.grade,
            "parent_id": self.parent_id,
            "difficulty": self.difficulty,
            "mastery": self.mastery,
            "importance": self.importance,
            "relation": DataManager.dumps(self.relation),
            "content": self.content,
            "formula": self.formula,
            "examples": self.examples,
            "pitfalls": self.pitfalls,
            "summary": self.summary,
            "node_type": self.node_type,
            "important": 1 if self.important else 0,
            "predecessor": DataManager.dumps(self.predecessor),
            "successor": DataManager.dumps(self.successor),
            "errors": DataManager.dumps(self.errors),
            "formula_list": DataManager.dumps(self.formula_list),
        }

    @classmethod
    def from_row(cls, row: dict) -> "KnowledgeNode":
        from database.manager import DataManager
        return cls(
            id=row.get("id"),
            name=row.get("name", ""),
            subject=row.get("subject", ""),
            grade=row.get("grade", ""),
            parent_id=row.get("parent_id"),
            difficulty=row.get("difficulty", 1),
            mastery=row.get("mastery", 0.0),
            importance=row.get("importance", 0.5),
            relation=DataManager.loads(row.get("relation")),
            content=row.get("content", ""),
            formula=row.get("formula", ""),
            examples=row.get("examples", ""),
            pitfalls=row.get("pitfalls", ""),
            summary=row.get("summary", ""),
            node_type=row.get("node_type", "knowledge"),
            important=bool(row.get("important", 0)),
            predecessor=DataManager.loads(row.get("predecessor")),
            successor=DataManager.loads(row.get("successor")),
            errors=DataManager.loads(row.get("errors")),
            formula_list=DataManager.loads(row.get("formula_list")),
        )
