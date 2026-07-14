# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""学习状态引擎（Learning State Engine）—— 系统核心差异化模块。

普通刷题软件只记录「做对/做错」，本引擎维护每个学生的「知识世界状态」：
- 掌握度随练习结果动态更新（答对提升、答错下降，带置信度平滑）。
- 遗忘曲线（Ebbinghaus）量化「多久没复习 → 遗忘多少」。
- 薄弱点识别：掌握度低 + 错次高 + 临近遗忘 的节点。
- 推荐分：薄弱×40% + 遗忘×30% + 重要×20% + 探索×10%（冻结版公式）。

后续 AI 推荐、学习规划、学习画像全部依赖本引擎产出的状态。
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import List, Optional

import config.settings as cfg
from database.manager import DataManager
from .state import StudentKnowledgeState


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class LearningEngine:
    def __init__(self, dm: DataManager):
        self.dm = dm
        from .event_log import LearningEventLog
        self.events = LearningEventLog(dm)

    # ---- 状态读写 -----------------------------------------------------
    def get_state(self, student_id: int, knowledge_id: int) -> StudentKnowledgeState:
        row = self.dm.query_one(
            "SELECT * FROM learn_state WHERE student_id = ? AND knowledge_id = ?",
            (student_id, knowledge_id),
        )
        if row:
            return StudentKnowledgeState.from_row(row)
        return StudentKnowledgeState(student_id=student_id, knowledge_id=knowledge_id)

    def _save(self, st: StudentKnowledgeState) -> None:
        from database.manager import DataManager
        curve = DataManager.dumps([[t, m] for t, m in st.learning_curve])
        existing = self.dm.query_one(
            "SELECT 1 FROM learn_state WHERE student_id = ? AND knowledge_id = ?",
            (st.student_id, st.knowledge_id),
        )
        if existing:
            self.dm.execute(
                """UPDATE learn_state SET mastery=?, wrong_count=?, last_time=?, learning_curve=?
                   WHERE student_id=? AND knowledge_id=?""",
                (st.mastery, st.wrong_count, st.last_time, curve, st.student_id, st.knowledge_id),
            )
        else:
            self.dm.execute(
                """INSERT INTO learn_state
                   (student_id, knowledge_id, mastery, wrong_count, last_time, learning_curve)
                   VALUES (?,?,?,?,?,?)""",
                (st.student_id, st.knowledge_id, st.mastery, st.wrong_count, st.last_time, curve),
            )

    # ---- 掌握度更新（带平滑） ----------------------------------------
    def record_practice(
        self,
        student_id: int,
        knowledge_id: int,
        correct: bool,
        now: Optional[datetime] = None,
        error_cause: Optional[list] = None,
    ) -> StudentKnowledgeState:
        """练习一道绑定该知识点的题后更新状态。

        更新策略：
        - 答对：mastery += step * (1 - mastery)，越接近 1 提升越慢（边际递减）。
        - 答错：mastery -= step * mastery，且错次 +1。
        - 步长随错次自适应：错得越多，单次修正越保守，避免抖动。
        - error_cause（Phase 1.5-D）：答错时记录错因标签，写入学习事件 payload，
          供错因画像 / AI 老师归因分析使用。
        """
        now = now or datetime.now()
        st = self.get_state(student_id, knowledge_id)
        before = round(st.mastery, 4)
        step = 0.12 if st.wrong_count < 3 else 0.08
        if correct:
            st.mastery = min(1.0, st.mastery + step * (1 - st.mastery))
        else:
            st.mastery = max(0.0, st.mastery - step * max(st.mastery, 0.2))
            st.wrong_count += 1
        st.last_time = now.isoformat(timespec="seconds")
        st.learning_curve.append((st.last_time, round(st.mastery, 4)))
        st.learning_curve = st.learning_curve[-50:]  # 仅保留最近 50 点
        self._save(st)
        after = round(st.mastery, 4)
        # 写入学习事件日志（供 AI 老师 / 画像）
        payload = {"wrong_count": st.wrong_count, "step": round(step, 3)}
        if (not correct) and error_cause:
            # 仅保留已知标准错因标签，避免脏数据入库
            ec = [t for t in error_cause if t in cfg.ERROR_TAGS][:3]
            if ec:
                payload["error_cause"] = ec
        self.events.record(
            student_id, "answer_correct" if correct else "answer_wrong",
            knowledge_id=knowledge_id, before=before, after=after,
            payload=payload,
            timestamp=now,
        )
        # 掌握度发生显著变化（≥0.05）时额外记录一次 mastery_change 事件
        if abs(after - before) >= 0.05:
            self.events.record(
                student_id, "mastery_change", knowledge_id=knowledge_id,
                before=before, after=after,
                payload={"delta": round(after - before, 4)}, timestamp=now,
            )
        return st

    # ---- 遗忘曲线（Ebbinghaus） --------------------------------------
    @staticmethod
    def forget_degree(st: StudentKnowledgeState, now: Optional[datetime] = None) -> float:
        """返回遗忘程度 0-1。从未练习或掌握度为 0 → 1（完全遗忘）。"""
        now = now or datetime.now()
        if st.last_time is None or st.mastery <= 0:
            return 1.0
        try:
            last = datetime.fromisoformat(st.last_time)
        except ValueError:
            return 1.0
        days = max(0.0, (now - last).total_seconds() / 86400.0)
        tau = cfg.FORGET_TAU_DAYS
        retention = math.exp(-days / tau)
        return 1.0 - retention

    # ---- 推荐分（冻结版公式） ----------------------------------------
    def recommend_score(
        self,
        st: StudentKnowledgeState,
        node_importance: float,
        now: Optional[datetime] = None,
    ) -> float:
        w = cfg.RECOMMEND_WEIGHTS
        weak = 1.0 - st.mastery
        forget = self.forget_degree(st, now)
        importance = max(0.0, min(1.0, node_importance))
        explore = random.random()
        score = (
            weak * w["weak"]
            + forget * w["forget"]
            + importance * w["importance"]
            + explore * w["explore"]
        )
        return round(score, 4)

    # ---- 薄弱点识别 ---------------------------------------------------
    def weak_points(
        self, student_id: int, top_n: int = 5, now: Optional[datetime] = None
    ) -> List[dict]:
        """返回该学生掌握度最低 / 最该复习的知识点（含推荐分）。"""
        from core.knowledge_engine import KnowledgeGraph
        kg = KnowledgeGraph(self.dm)
        rows = self.dm.query(
            "SELECT * FROM learn_state WHERE student_id = ?", (student_id,)
        )
        scored = []
        for r in rows:
            st = StudentKnowledgeState.from_row(r)
            node = kg.get(st.knowledge_id)
            if not node:
                continue
            score = self.recommend_score(st, node.importance, now)
            scored.append({
                "knowledge_id": node.id,
                "name": node.name,
                "subject": node.subject,
                "grade": node.grade,
                "mastery": round(st.mastery, 3),
                "wrong_count": st.wrong_count,
                "recommend_score": score,
            })
        scored.sort(key=lambda x: x["recommend_score"], reverse=True)
        return scored[:top_n]

    def subject_progress(self, student_id: int) -> dict:
        """按学科聚合掌握度，供 Dashboard / 数据分析使用。"""
        from core.knowledge_engine import KnowledgeGraph
        kg = KnowledgeGraph(self.dm)
        rows = self.dm.query(
            "SELECT * FROM learn_state WHERE student_id = ?", (student_id,)
        )
        agg: dict = {}
        for r in rows:
            st = StudentKnowledgeState.from_row(r)
            node = kg.get(st.knowledge_id)
            if not node:
                continue
            subj = node.subject
            d = agg.setdefault(subj, {"sum": 0.0, "n": 0})
            d["sum"] += st.mastery
            d["n"] += 1
        return {k: round(v["sum"] / v["n"], 3) for k, v in agg.items()}
