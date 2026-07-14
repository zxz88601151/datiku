# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""学习会话状态机（Phase 2.1）。

管理一次完整的学习流生命周期：
- 创建 session（按推荐分组卷生成 10 道题）
- 逐题作答：后端批改 → 掌握度更新 → 事件日志 → 错题本 → 错因标签写入
- 会话级聚合分析：错因分布（分类计数）、薄弱诊断（高频出错知识点）、补救建议

生命周期：create() → 循环 submit_answer() + advance() → complete() → summary()
"""

from __future__ import annotations

import time
import uuid
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.learning_engine import LearningEngine
from core.question_engine import QuestionBank
from core.question_engine.question import Question
from database.manager import DataManager


class AnswerRecord:
    """单次作答记录（属性冻结，修改即新建）。"""

    __slots__ = (
        "question_id", "correct", "user_answer", "spent_sec",
        "difficulty", "error_tags", "knowledge_id", "exam_weight",
    )

    def __init__(
        self,
        question_id: int,
        correct: bool,
        user_answer: str,
        spent_sec: int,
        difficulty: int,
        error_tags: List[str],
        knowledge_id: Optional[int],
        exam_weight: int,
    ):
        self.question_id = question_id
        self.correct = correct
        self.user_answer = user_answer
        self.spent_sec = spent_sec
        self.difficulty = difficulty
        self.error_tags = list(error_tags or [])
        self.knowledge_id = knowledge_id
        self.exam_weight = exam_weight


class LearningSession:
    """一次完整的学习会话。

    用法::

        session = LearningSession(bank, le, dm)
        session.create(student_id=1, subject="数学", grade="七年级")
        while session.current_question:
            # 显示题目 → 获取用户答案
            rec = session.submit_answer(entry_time, user_answer)
            ok = session.advance()
        report = session.complete()
    """

    def __init__(self, bank: QuestionBank, le: LearningEngine, dm: DataManager):
        self.bank = bank
        self.le = le
        self.dm = dm
        self.reset()

    # ---- 生命周期 ------------------------------------------------

    def reset(self) -> None:
        self.session_id: Optional[str] = None
        self.student_id: Optional[int] = None
        self.subject: Optional[str] = None
        self.grade: Optional[str] = None
        self.questions: List[Question] = []
        self.records: List[AnswerRecord] = []
        self._start_ts: Optional[float] = None
        self._end_ts: Optional[float] = None
        self._current_idx: int = 0

    def create(
        self,
        student_id: int,
        subject: str = "数学",
        grade: str = "七年级",
        size: int = 10,
        knowledge_ids: Optional[List[int]] = None,
    ) -> "LearningSession":
        """生成新会话并记录 session_start 事件。"""
        self.reset()
        self.session_id = uuid.uuid4().hex[:8]
        self.student_id = student_id
        self.subject = subject
        self.grade = grade
        self.questions = self.bank.generate_session(
            student_id,
            subject=subject,
            grade=grade,
            size=size,
            knowledge_ids=knowledge_ids,
        )
        if self.questions:
            self._start_ts = time.time()
            self._log_event("session_start", {
                "session_id": self.session_id,
                "size": len(self.questions),
                "subject": subject,
            })
        return self

    @property
    def current_question(self) -> Optional[Question]:
        if self._current_idx < len(self.questions):
            return self.questions[self._current_idx]
        return None

    @property
    def progress(self) -> str:
        return f"第 {self._current_idx + 1} / {len(self.questions)} 题"

    @property
    def is_completed(self) -> bool:
        return self._end_ts is not None or len(self.records) >= len(self.questions)

    # ---- 答题 ---------------------------------------------------

    def submit_answer(self, entry_time: float, answer: str) -> AnswerRecord:
        """提交当前题的答案，返回 AnswerRecord（含批改结果与错因）。"""
        q = self.current_question
        if q is None:
            raise RuntimeError("无当前题目，请先调用 create()")

        spent_sec = max(1, int(time.time() - entry_time))
        correct = self.bank.evaluate(q, answer)

        # 掌握度更新（含错因标签写入事件 payload）
        kid = q.knowledge_relation[0] if q.knowledge_relation else None
        error_tags: List[str] = []
        if hasattr(q, "error_tags") and q.error_tags:
            error_tags = q.error_tags[:3]
        if kid:
            ec = error_tags if not correct else None
            self.le.record_practice(self.student_id, kid, correct, error_cause=ec)

        rec = AnswerRecord(
            question_id=q.id,
            correct=correct,
            user_answer=answer,
            spent_sec=spent_sec,
            difficulty=q.difficulty,
            error_tags=error_tags,
            knowledge_id=kid,
            exam_weight=getattr(q, "exam_weight", 3),
        )
        self.records.append(rec)
        self._write_db_records(rec, correct, q)
        self._log_event(
            "answer_correct" if correct else "answer_wrong",
            {
                "question_id": q.id,
                "knowledge_id": kid,
                "difficulty": q.difficulty,
                "spent_sec": spent_sec,
                "error_tags": error_tags if not correct else [],
            },
        )
        return rec

    def advance(self) -> bool:
        """前进到下一题。返回 True 表示还有更多题目。"""
        self._current_idx += 1
        return self._current_idx < len(self.questions)

    # ---- 完成与会话报告 -----------------------------------------

    def complete(self) -> Dict[str, Any]:
        """结束会话，生成分析报告并记录 session_end 事件。"""
        self._end_ts = time.time()
        total = len(self.records)
        correct_count = sum(1 for r in self.records if r.correct)
        wrong_count = total - correct_count
        duration = int(self._end_ts - (self._start_ts or self._end_ts))

        error_causes: Counter = Counter()
        weak_ids: set = set()
        difficulty_dist: Counter = Counter()
        for r in self.records:
            difficulty_dist[r.difficulty] += 1
            if not r.correct:
                for t in r.error_tags:
                    error_causes[t] += 1
                if r.knowledge_id:
                    weak_ids.add(r.knowledge_id)

        report = {
            "session_id": self.session_id,
            "student_id": self.student_id,
            "subject": self.subject,
            "grade": self.grade,
            "total": total,
            "correct": correct_count,
            "wrong": wrong_count,
            "accuracy": correct_count / max(1, total),
            "total_duration_sec": duration,
            "avg_spent_sec": duration / max(1, total),
            "error_causes": dict(error_causes.most_common(10)),
            "weak_knowledge_ids": list(weak_ids),
            "difficulty_distribution": dict(difficulty_dist),
        }

        self._log_event("session_end", {
            "total": total,
            "correct": correct_count,
            "wrong": wrong_count,
            "duration_sec": duration,
            "accuracy": round(report["accuracy"], 3),
            "error_causes": report["error_causes"],
        })
        return report

    # ---- 内部辅助 -----------------------------------------------

    def _write_db_records(self, rec: AnswerRecord, correct: bool, q: Question) -> None:
        """写入 learn_record + learn_wrong。"""
        ts = datetime.now().isoformat(timespec="seconds")
        self.dm.execute(
            "INSERT INTO learn_record (student_id, question_id, result, spent_sec, created_at)"
            " VALUES (?,?,?,?,?)",
            (self.student_id, q.id, "correct" if correct else "wrong", rec.spent_sec, ts),
        )
        if not correct:
            existing = self.dm.query_one(
                "SELECT id, count FROM learn_wrong WHERE student_id=? AND question_id=?",
                (self.student_id, q.id),
            )
            tags = "; ".join(rec.error_tags[:3]) if rec.error_tags else "待归因"
            if existing:
                self.dm.execute(
                    "UPDATE learn_wrong SET count=?, last_time=?, wrong_reason=? WHERE id=?",
                    (existing["count"] + 1, ts, tags, existing["id"]),
                )
            else:
                self.dm.execute(
                    "INSERT INTO learn_wrong (student_id, question_id, wrong_reason, count, mastery, resolved, last_time)"
                    " VALUES (?,?,?,?,?,?,?)",
                    (self.student_id, q.id, tags, 1, 0.0, 0, ts),
                )

    def _log_event(self, event_type: str, payload: dict) -> None:
        try:
            self.le.events.record(
                self.student_id,
                event_type,
                knowledge_id=None,
                payload={"session_id": self.session_id, **(payload or {})},
            )
        except Exception as e:
            from utils.logger import log
            log.exception("session event log failed", exc_info=e)
