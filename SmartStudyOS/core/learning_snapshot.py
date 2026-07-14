# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""学习快照与趋势分析（Phase 2.2）。

提供驾驶舱所需的数据聚合：
- 每日快照：记录学科整体掌握度、薄弱点分布、学习时长，避免趋势图每次重算 30 万历史事件。
- 趋势查询：按日返回最近 N 天快照序列，支持按趋势图渲染。
- 规则化建议：基于当前掌握度与错题次数，生成非 AI 的智能学习建议。
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from core.learning_engine import LearningEngine
from core.knowledge_engine import KnowledgeGraph
from database.manager import DataManager


class LearningSnapshot:
    """快照的创建与查询。"""

    def __init__(self, dm: DataManager, le: LearningEngine, kg: KnowledgeGraph):
        self.dm = dm
        self.le = le
        self.kg = kg

    # ---- 每日快照 ------------------------------------------------
    def create_snapshot(self, student_id: int, when: Optional[datetime] = None) -> dict:
        """计算当前掌握度快照并持久化到 learning_snapshot 表。

        返回快照字典（含整体掌握度、薄弱点、学习时长）。
        """
        now = when or datetime.now()
        d = now.strftime("%Y-%m-%d")

        # 1) 学科整体掌握度
        progress = self.le.subject_progress(student_id)
        overall = progress.get("数学", 0.0) or 0.0

        # 2) 薄弱点：掌握度 < 0.4 的知识点
        weak = self.le.weak_points(student_id, top_n=20)
        weak_points = {}
        for w in weak:
            weak_points[str(w["knowledge_id"])] = round(w.get("mastery", 0.0), 3)

        # 3) 今日学习分钟数
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(timespec="seconds")
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat(timespec="seconds")
        row = self.dm.query_one(
            "SELECT COALESCE(SUM(spent_sec), 0) s FROM learn_record "
            "WHERE student_id=? AND created_at>=? AND created_at<=?",
            (student_id, start_of_day, end_of_day),
        )
        study_minutes = (row["s"] // 60) if row else 0

        snapshot = {
            "student_id": student_id,
            "date": d,
            "subject": "数学",
            "overall_mastery": round(overall, 3),
            "weak_points": self.dm.dumps(weak_points),
            "study_minutes": study_minutes,
        }

        self.dm.execute(
            "INSERT OR REPLACE INTO learning_snapshot "
            "(student_id, date, subject, overall_mastery, weak_points, study_minutes) "
            "VALUES (?,?,?,?,?,?)",
            (student_id, d, "数学", round(overall, 3),
             self.dm.dumps(weak_points), study_minutes),
        )
        return snapshot

    def get_trend(self, student_id: int, days: int = 30) -> List[dict]:
        """返回最近 N 天的快照序列（按日期升序）。"""
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        rows = self.dm.query(
            "SELECT date, overall_mastery, weak_points, study_minutes "
            "FROM learning_snapshot WHERE student_id=? AND date>=? "
            "ORDER BY date ASC",
            (student_id, since),
        )
        for r in rows:
            r["weak_points"] = self.dm.loads(r.get("weak_points") or "{}")
            r["overall_mastery"] = r.get("overall_mastery", 0.0) or 0.0
        return rows

    def ensure_latest_snapshot(self, student_id: int) -> dict:
        """确保今天有快照，若无则创建。返回快照字典。"""
        today = datetime.now().strftime("%Y-%m-%d")
        existing = self.dm.query_one(
            "SELECT * FROM learning_snapshot WHERE student_id=? AND date=?",
            (student_id, today),
        )
        if existing:
            existing["weak_points"] = self.dm.loads(existing.get("weak_points") or "{}")
            existing["overall_mastery"] = existing.get("overall_mastery", 0.0) or 0.0
            return existing
        return self.create_snapshot(student_id)


class SuggestionEngine:
    """基于规则的智能学习建议（Phase 2.2，不依赖大模型）。"""

    def __init__(self, dm: DataManager, le: LearningEngine, kg: KnowledgeGraph):
        self.dm = dm
        self.le = le
        self.kg = kg

    def get_suggestions(self, student_id: int, top_n: int = 3) -> List[dict]:
        """返回前 N 条规则化学习建议。

        规则：
        1. 薄弱点强化：mastery < 0.4 且错题数 > 3 → 建议强化训练
        2. 高频错因：知识点在错题本中出现 > 5 次 → 建议专题复习
        3. 先修链回顾：薄弱节点的前驱节点掌握度 < 0.5 → 建议先修复习
        4. 进步停滞：近 7 天某知识点掌握度变化 < 0.01 → 建议交替训练
        """
        # 1) 薄弱点强化
        weak = self.le.weak_points(student_id, top_n=15)
        suggestions = []
        for w in weak:
            kid = w["knowledge_id"]
            kn = self.kg.get(kid)
            name = kn.name if kn else f"#{kid}"
            mastery = w.get("mastery", 0.0)
            wrong_count = w.get("wrong_count", 0)

            if mastery < 0.3 and wrong_count >= 3:
                suggestions.append({
                    "type": "weak_urgent",
                    "label": "🔴 急需强化",
                    "title": name,
                    "detail": f"当前掌握度 {mastery:.0%}，已连续答错 {wrong_count} 次",
                    "action": "recommend_practice",
                    "knowledge_id": kid,
                })
            elif mastery < 0.45 and wrong_count >= 2:
                suggestions.append({
                    "type": "weak_normal",
                    "label": "🟡 建议复习",
                    "title": name,
                    "detail": f"当前掌握度 {mastery:.0%}，建议 5 题巩固训练",
                    "action": "recommend_practice",
                    "knowledge_id": kid,
                })

        # 2) 高频错因
        wrong_rows = self.dm.query(
            "SELECT qw.wrong_reason, qw.question_id, qw.count, q.knowledge_relation "
            "FROM learn_wrong qw "
            "JOIN q_question q ON q.id = qw.question_id "
            "WHERE qw.student_id=? AND qw.resolved=0 ORDER BY qw.count DESC LIMIT 10",
            (student_id,),
        )
        seen_kids = set()
        for r in wrong_rows:
            reason = (r.get("wrong_reason") or "").strip()
            cnt = r.get("count", 0)
            if cnt >= 5 and reason and reason != "待归因":
                # 提取知识点
                kids = self.dm.loads(r.get("knowledge_relation") or "[]")
                for kid in kids:
                    if kid in seen_kids:
                        continue
                    seen_kids.add(kid)
                    kn = self.kg.get(kid)
                    name = kn.name if kn else f"#{kid}"
                    suggestions.append({
                        "type": "freq_error",
                        "label": "📌 高频错因",
                        "title": f"{name} — {reason}",
                        "detail": f"已错 {cnt} 次，建议专题纠错练习",
                        "action": "recommend_practice",
                        "knowledge_id": kid,
                    })
                    if len(suggestions) >= top_n * 2:
                        break
            if len(suggestions) >= top_n * 2:
                break

        # 去重：按 knowledge_id 去重
        seen = set()
        deduped = []
        for s in suggestions:
            kid = s.get("knowledge_id")
            if kid and kid in seen:
                continue
            if kid:
                seen.add(kid)
            deduped.append(s)
        return deduped[:top_n]
