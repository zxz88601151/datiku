# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""学习事件日志（Phase 1.5-C）。

记录每一次有意义的学习行为，是 AI 老师、学习画像、成长曲线的核心数据来源：
- answer_correct / answer_wrong：一次答题结果（含掌握度 before/after）。
- session：一次练习/组卷的开始或结束。
- review：复习某知识点（通常源自先修链建议）。
- mastery_change：掌握度发生显著变化（由引擎在阈值触发时写入）。

所有写入均经 DataManager 参数化接口，杜绝 SQL 注入。
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import config.settings as cfg
from database.manager import DataManager


class LearningEventLog:
    def __init__(self, dm: DataManager):
        self.dm = dm

    def record(
        self,
        student_id: int,
        event_type: str,
        knowledge_id: Optional[int] = None,
        before: Optional[float] = None,
        after: Optional[float] = None,
        payload: Optional[dict] = None,
        timestamp: Optional[datetime] = None,
    ) -> int:
        ts = (timestamp or datetime.now()).isoformat(timespec="seconds")
        row = {
            "student_id": student_id,
            "event_type": event_type,
            "knowledge_id": knowledge_id,
            "before_score": before,
            "after_score": after,
            "payload": DataManager.dumps(payload or {}),
            "timestamp": ts,
        }
        return self.dm.insert("learning_event", row)

    def history(
        self, student_id: int, knowledge_id: Optional[int] = None, limit: int = 200
    ) -> List[dict]:
        if knowledge_id is not None:
            rows = self.dm.query(
                "SELECT * FROM learning_event WHERE student_id = ? AND knowledge_id = ? "
                "ORDER BY id DESC LIMIT ?",
                (student_id, knowledge_id, limit),
            )
        else:
            rows = self.dm.query(
                "SELECT * FROM learning_event WHERE student_id = ? ORDER BY id DESC LIMIT ?",
                (student_id, limit),
            )
        for r in rows:
            r["payload"] = DataManager.loads(r.get("payload"))
        return rows

    def count(self, student_id: Optional[int] = None, event_type: Optional[str] = None) -> int:
        if student_id is not None and event_type is not None:
            r = self.dm.query_one(
                "SELECT COUNT(*) n FROM learning_event WHERE student_id = ? AND event_type = ?",
                (student_id, event_type),
            )
        elif student_id is not None:
            r = self.dm.query_one(
                "SELECT COUNT(*) n FROM learning_event WHERE student_id = ?", (student_id,)
            )
        else:
            r = self.dm.query_one("SELECT COUNT(*) n FROM learning_event")
        return r["n"] if r else 0
