# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""题库引擎（Question Engine）。

提供题目的参数化 CRUD、按知识点检索，以及「智能刷题 session 生成」：
根据学生每个知识点的推荐分（来自 Learning Engine）加权抽取题目，
实现「薄弱点自动强化、其他知识点降权」的自适应训练。
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional

from database.manager import DataManager
from .question import Question, Option


class QuestionBank:
    def __init__(self, dm: DataManager, learning_engine=None):
        self.dm = dm
        self.le = learning_engine  # 可选注入，用于推荐分加权

    # ---- 写 -----------------------------------------------------------
    def add(self, q: Question, options: Optional[List[Option]] = None) -> int:
        qid = self.dm.insert("q_question", q.to_row())
        if options:
            for opt in options:
                opt.question_id = qid
                self.dm.insert("q_option", {
                    "question_id": opt.question_id,
                    "label": opt.label,
                    "text": opt.text,
                    "is_correct": 1 if opt.is_correct else 0,
                })
        return qid

    def update(self, q: Question) -> None:
        if q.id is None:
            raise ValueError("q.id 为空")
        self.dm.update("q_question", q.to_row(), "id = ?", (q.id,))

    def delete(self, qid: int) -> None:
        self.dm.execute("DELETE FROM q_question WHERE id = ?", (qid,))

    # ---- 读 -----------------------------------------------------------
    def get(self, qid: int) -> Optional[Question]:
        row = self.dm.query_one("SELECT * FROM q_question WHERE id = ?", (qid,))
        return Question.from_row(row) if row else None

    def get_options(self, qid: int) -> List[Option]:
        rows = self.dm.query(
            "SELECT * FROM q_option WHERE question_id = ? ORDER BY label", (qid,)
        )
        return [
            Option(
                id=r["id"], question_id=r["question_id"],
                label=r["label"], text=r["text"], is_correct=bool(r["is_correct"]),
            )
            for r in rows
        ]

    def get_by_knowledge(self, knowledge_id: int) -> List[Question]:
        rows = self.dm.query(
            "SELECT * FROM q_question WHERE knowledge_relation LIKE ?",
            (f'%{knowledge_id}%',),
        )
        return [Question.from_row(r) for r in rows]

    def get_by_subject_grade(self, subject: str, grade: str) -> List[Question]:
        rows = self.dm.query(
            "SELECT * FROM q_question WHERE subject = ? AND grade = ?", (subject, grade)
        )
        return [Question.from_row(r) for r in rows]

    # ---- 智能组卷（核心） --------------------------------------------
    def generate_session(
        self,
        student_id: int,
        subject: Optional[str] = None,
        grade: Optional[str] = None,
        size: int = 10,
        now=None,
        knowledge_ids: Optional[List[int]] = None,
        max_difficulty: Optional[int] = None,
    ) -> List[Question]:
        """按推荐分加权生成一套练习。

        逻辑：
        1. 收集候选题目（可按学科/年级过滤）。
        2. 对每题绑定的知识点，用 Learning Engine 计算推荐分，
           取该知识点当前最大推荐分作为题目权重。
        3. 按权重概率抽样，size 道题（不带替换）。
        薄弱知识点权重高 → 被抽中概率大 → 自然强化。
        """
        if subject and grade:
            pool = self.get_by_subject_grade(subject, grade)
        elif subject:
            pool = [Question.from_row(r) for r in
                    self.dm.query("SELECT * FROM q_question WHERE subject = ?", (subject,))]
        else:
            pool = [Question.from_row(r) for r in self.dm.query("SELECT * FROM q_question")]

        if knowledge_ids:
            kn_set = set(knowledge_ids)
            pool = [q for q in pool if set(q.knowledge_relation) & kn_set]
        if max_difficulty is not None:
            pool = [q for q in pool if q.difficulty <= max_difficulty]

        if not pool:
            return []

        import config.settings as cfg
        from core.knowledge_engine import KnowledgeGraph

        kg = KnowledgeGraph(self.dm)

        def weight(q: Question) -> float:
            if not self.le or not q.knowledge_relation:
                return 1.0
            scores = []
            for kid in q.knowledge_relation:
                st = self.le.get_state(student_id, kid)
                node = kg.get(kid)
                imp = node.importance if node else 0.5
                scores.append(self.le.recommend_score(st, imp, now))
            base = max(scores) if scores else 1.0
            ew = getattr(q, "exam_weight", 1) or 1
            return base * (0.7 + 0.06 * ew)

        weights = [weight(q) for q in pool]
        total = sum(weights)
        if total <= 0:
            return random.sample(pool, min(size, len(pool)))

        chosen: List[Question] = []
        remaining = list(pool)
        rem_w = list(weights)
        for _ in range(min(size, len(pool))):
            s = sum(rem_w)
            if s <= 0:
                break
            r = random.uniform(0, s)
            acc = 0.0
            for i, w in enumerate(rem_w):
                acc += w
                if r <= acc:
                    chosen.append(remaining.pop(i))
                    rem_w.pop(i)
                    break
        return chosen

    # ---- 批改（参数化比对，避免前端校验绕过） ------------------------
    def evaluate(self, q: Question, user_answer: str) -> bool:
        """后端权威批改。选择题比对选项 label，其他题型做归一化比对。"""
        if q.is_choice:
            correct = [o for o in self.get_options(q.id) if o.is_correct]
            return user_answer.strip() in {o.label for o in correct}
        # 非选择题：去除空白后相等即视为正确（生产可替换为 LLM 语义判分）
        return user_answer.strip() == (q.answer or "").strip()
