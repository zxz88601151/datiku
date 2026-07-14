# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""用户画像系统（Phase 2.4）。

三层结构：
1. UserProfileManager — 用户资料的 CRUD、批量创建、切换
2. GoalEngine — 学习目标 → 能力要求 → 每日任务映射
3. UserContext — 多用户上下文管理（可切换当前学生）

数据来源：user / user_goal / user_preference 表 + learn_state 实时聚合
"""

from __future__ import annotations

import json
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from database.manager import DataManager
from core.learning_engine import LearningEngine
from core.knowledge_engine import KnowledgeGraph


# ---- 默认画像 100 套（用于批量创建测试学生） ----
_SAMPLE_NAMES = [
    "小明", "小红", "小刚", "小丽", "小华", "小美", "小强", "小芳", "小龙", "小雪",
    "子轩", "雨涵", "浩然", "诗琪", "俊杰", "语彤", "明哲", "思远", "天佑", "欣怡",
]
_SAMPLE_GRADES = ["七年级", "八年级", "九年级"]
_SAMPLE_TARGETS = ["中考", "日常提升", "竞赛", "中考"]


def _random_profile(rng: random.Random, idx: int) -> dict:
    grade = rng.choice(_SAMPLE_GRADES)
    target = rng.choice(_SAMPLE_TARGETS)
    name = _SAMPLE_NAMES[idx % len(_SAMPLE_NAMES)]
    if idx >= len(_SAMPLE_NAMES):
        name = f"学生{idx}"
    return {
        "name": name,
        "nickname": name,
        "grade": grade,
        "school": "盐城实验中学",
        "target": target,
        "subjects": json.dumps(["数学"]),
        "guardian": "家长",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


class UserProfileManager:
    """用户资料管理。"""

    def __init__(self, dm: DataManager):
        self.dm = dm

    def create_user(self, name: str, grade: str = "七年级",
                    nickname: str = "", target: str = "日常提升",
                    subjects: Optional[List[str]] = None) -> int:
        """创建新用户，返回 user_id。"""
        row = {
            "name": name,
            "nickname": nickname or name,
            "grade": grade,
            "school": "盐城实验中学",
            "target": target,
            "subjects": self.dm.dumps(subjects or ["数学"]),
            "guardian": "家长",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        uid = self.dm.insert("user", row)
        # 默认偏好
        self.dm.execute(
            "INSERT OR IGNORE INTO user_preference (user_id) VALUES (?)", (uid,))
        return uid

    def update_user(self, user_id: int, **kwargs) -> None:
        """更新用户资料（仅传需要修改的字段）。"""
        allowed = {"nickname", "grade", "school", "target", "subjects", "guardian"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return
        set_clause = ", ".join(f"{k}=?" for k in updates)
        vals = list(updates.values()) + [user_id]
        self.dm.execute(f"UPDATE user SET {set_clause} WHERE id=?", vals)

    def get_user(self, user_id: int) -> Optional[dict]:
        """获取用户完整资料。"""
        row = self.dm.query_one("SELECT * FROM user WHERE id=?", (user_id,))
        if row:
            row["subjects"] = self.dm.loads(row.get("subjects") or "[]")
            row["goals"] = self.dm.query(
                "SELECT * FROM user_goal WHERE user_id=? ORDER BY priority", (user_id,))
            pref = self.dm.query_one(
                "SELECT * FROM user_preference WHERE user_id=?", (user_id,))
            row["preference"] = pref or {}
        return row

    def list_users(self) -> List[dict]:
        """列出所有用户（摘要）。"""
        return self.dm.query("SELECT id, name, nickname, grade, target FROM user ORDER BY id")

    def delete_user(self, user_id: int) -> None:
        self.dm.execute("DELETE FROM user WHERE id=?", (user_id,))

    # ---- 批量创建模拟学生 ----
    def seed_demo_users(self, count: int = 100) -> int:
        """创建 count 个模拟学生（不同年级/目标/能力覆盖）。"""
        existing = self.dm.query_one("SELECT COUNT(*) n FROM user")["n"]
        if existing >= count:
            return existing
        rng = random.Random(20260707)
        created = 0
        for i in range(existing, count):
            p = _random_profile(rng, i)
            uid = self.dm.insert("user", p)
            self.dm.execute(
                "INSERT OR IGNORE INTO user_preference (user_id) VALUES (?)", (uid,))
            created += 1
        return self.dm.query_one("SELECT COUNT(*) n FROM user")["n"]


class GoalEngine:
    """目标引擎：将学习目标转化为每日任务。"""

    def __init__(self, dm: DataManager, kg: KnowledgeGraph, le: LearningEngine):
        self.dm = dm
        self.kg = kg
        self.le = le

    def set_goal(self, user_id: int, subject: str, target_score: int,
                 current_score: int = 0, deadline: str = "") -> int:
        """设置或更新学科目标。"""
        existing = self.dm.query_one(
            "SELECT id FROM user_goal WHERE user_id=? AND subject=?",
            (user_id, subject),
        )
        if existing:
            self.dm.execute(
                "UPDATE user_goal SET target_score=?, current_score=?, deadline=? WHERE id=?",
                (target_score, current_score, deadline, existing["id"]),
            )
            return existing["id"]
        return self.dm.insert("user_goal", {
            "user_id": user_id, "subject": subject,
            "target_score": target_score, "current_score": current_score,
            "deadline": deadline, "priority": 1,
        })

    def gap_analysis(self, user_id: int, subject: str = "数学") -> dict:
        """分析目标差距，输出需要提升的维度。"""
        goals = self.dm.query(
            "SELECT * FROM user_goal WHERE user_id=? AND subject=?",
            (user_id, subject),
        )
        if not goals:
            return {"gap": 0, "needs": []}

        goal = goals[0]
        target = goal.get("target_score", 0) or 0
        current = goal.get("current_score", 0) or 0
        gap = max(0, target - current)

        # 基于当前掌握度估算薄弱领域
        weak = self.le.weak_points(user_id, top_n=5)
        needs = []
        for w in weak:
            kn = self.kg.get(w.get("knowledge_id"))
            needs.append({
                "knowledge_id": w["knowledge_id"],
                "name": kn.name if kn else f"#{w['knowledge_id']}",
                "mastery": round(w.get("mastery", 0.0), 3),
            })

        return {"gap": gap, "target": target, "current": current,
                "needs": needs, "priority_subjects": ["数学"]}

    def recommend_daily_task(self, user_id: int, subject: str = "数学",
                              max_questions: int = 10) -> dict:
        """基于目标生成每日推荐任务。"""
        gap = self.gap_analysis(user_id, subject)
        weak = self.le.weak_points(user_id, top_n=3)
        focus_knowledge = weak[0] if weak else None

        return {
            "subject": subject,
            "focus_knowledge_id": focus_knowledge["knowledge_id"] if focus_knowledge else None,
            "focus_name": self.kg.get(focus_knowledge["knowledge_id"]).name
                          if focus_knowledge and focus_knowledge.get("knowledge_id")
                          and self.kg.get(focus_knowledge["knowledge_id"]) else "综合复习",
            "recommended_count": min(max_questions, max(5, gap.get("gap", 20) // 10 + 5)),
            "gap": gap.get("gap", 0),
            "weak_knowledge": gap.get("needs", [])[:3],
        }
