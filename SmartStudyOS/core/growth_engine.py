# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""RPG 成长引擎（Phase 2.6）。

将学习数据转化为可感知的成长反馈，不覆盖、不影响学习引擎。

五层架构：
1. XPManager          — 从真实学习行为授予经验值
2. LevelSystem        — RPG 曲线升级（required = 100 × level^1.5）
3. SkillTreeEngine    — 知识图谱 → 技能树映射 + 等级计算
4. AchievementEngine  — 成就定义 + 自动解锁检测
5. DailyQuestEngine   — 来自薄弱点的每日任务
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from database.manager import DataManager
from core.knowledge_engine import KnowledgeGraph
from core.learning_engine import LearningEngine

# 技能树映射：知识图谱分类 → 技能 ID/名称
SKILL_TREE: Dict[str, Dict[str, List[str]]] = {
    "数学": {
        "计算": ["有理数", "实数", "整式", "幂", "指数"],
        "代数": ["方程", "不等式", "因式分解", "分式", "二次根"],
        "函数": ["函数", "一次函数", "二次函数", "反比例"],
        "几何": ["三角形", "四边形", "圆", "勾股", "相似", "全等", "轴对称"],
        "统计概率": ["概率", "统计", "数据"],
    }
}

# XP 常量
XP_PER_QUESTION = 2
XP_CORRECT_BONUS = 3
XP_HARD_BONUS = 5      # difficulty >= 4
XP_SESSION_BONUS = 20
XP_WRONG_FIX = 10
XP_STREAK_DAY = 15
XP_BREAKTHROUGH = 50   # 薄弱点 mastery 从 <0.3 提升到 >0.6
XP_ACHIEVEMENT = 100

# 成就定义
ACHIEVEMENT_DEFS: List[Dict[str, Any]] = [
    # 学习习惯
    {"id": "streak_7", "name": "🔥 连续学习 7 天", "type": "habit",
     "condition": "streak>=7", "reward_xp": 100},
    {"id": "streak_30", "name": "🔥 连续学习 30 天", "type": "habit",
     "condition": "streak>=30", "reward_xp": 300},
    {"id": "hundred_quiz", "name": "📝 百题挑战", "type": "habit",
     "condition": "total_questions>=100", "reward_xp": 150},
    # 知识突破
    {"id": "func_master", "name": "📈 函数突破者", "type": "skill",
     "condition": "skill_func>=6", "reward_xp": 200},
    {"id": "geo_master", "name": "📐 几何突破者", "type": "skill",
     "condition": "skill_geo>=6", "reward_xp": 200},
    {"id": "calc_master", "name": "🧮 计算大师", "type": "skill",
     "condition": "skill_calc>=6", "reward_xp": 200},
    {"id": "algebra_master", "name": "✏️ 代数能手", "type": "skill",
     "condition": "skill_algebra>=6", "reward_xp": 200},
    # 挑战
    {"id": "first_hard", "name": "⭐ 初次攻坚", "type": "challenge",
     "condition": "hard_question>=1", "reward_xp": 50},
    {"id": "perfect_session", "name": "💯 满分 Session", "type": "challenge",
     "condition": "perfect_session>=1", "reward_xp": 100},
    {"id": "zero_wrong", "name": "✅ 错题清零", "type": "challenge",
     "condition": "wrong_resolved>=5", "reward_xp": 100},
    {"id": "level_5", "name": "🌟 等级 Lv.5", "type": "milestone",
     "condition": "level>=5", "reward_xp": 150},
    {"id": "level_10", "name": "🌟 等级 Lv.10", "type": "milestone",
     "condition": "level>=10", "reward_xp": 300},
    {"id": "level_20", "name": "🌟 等级 Lv.20", "type": "milestone",
     "condition": "level>=20", "reward_xp": 500},
]


def _xp_for_level(level: int) -> int:
    """RPG 曲线：升到下一级所需 XP。"""
    return int(100 * (level ** 1.5))


def _level_from_xp(total_xp: int) -> int:
    """从累计 XP 反算等级。"""
    level = 1
    while _xp_for_level(level) <= total_xp:
        total_xp -= _xp_for_level(level)
        level += 1
    return level


def _xp_in_level(total_xp: int) -> int:
    """当前等级内的 XP。"""
    level = _level_from_xp(total_xp)
    for l in range(1, level):
        total_xp -= _xp_for_level(l)
    return max(0, total_xp)


# ---------------------------------------------------------------------------
# 1. XPManager
# ---------------------------------------------------------------------------
class XPManager:
    """经验值管理。"""

    def __init__(self, dm: DataManager):
        self.dm = dm

    def _ensure(self, student_id: int):
        self.dm.execute(
            "INSERT OR IGNORE INTO user_growth (student_id, level, xp, total_xp, created_at) "
            "VALUES (?,1,0,0,?)",
            (student_id, datetime.now().isoformat(timespec="seconds")),
        )

    def award(self, student_id: int, amount: int, source: str = "") -> Dict[str, int]:
        """授予经验值，返回 {level, xp, total_xp, gained}。"""
        self._ensure(student_id)
        row = self.dm.query_one(
            "SELECT level, xp, total_xp FROM user_growth WHERE student_id=?",
            (student_id,),
        )
        old_level = row["level"]
        old_total = row["total_xp"] or 0

        new_total = old_total + amount
        new_level = _level_from_xp(new_total)
        new_xp = _xp_in_level(new_total)

        self.dm.execute(
            "UPDATE user_growth SET level=?, xp=?, total_xp=? WHERE student_id=?",
            (new_level, new_xp, new_total, student_id),
        )
        return {
            "level": new_level,
            "xp": new_xp,
            "total_xp": new_total,
            "gained": amount,
            "leveled_up": new_level > old_level,
        }

    def get_state(self, student_id: int) -> dict:
        """获取当前成长状态。"""
        self._ensure(student_id)
        row = self.dm.query_one(
            "SELECT level, xp, total_xp FROM user_growth WHERE student_id=?",
            (student_id,),
        )
        lv = row["level"]
        curr = row["xp"] or 0
        needed = _xp_for_level(lv)
        return {
            "level": lv,
            "xp": curr,
            "xp_for_next": needed,
            "progress": curr / needed if needed > 0 else 0,
            "total_xp": row["total_xp"] or 0,
        }


# ---------------------------------------------------------------------------
# 2. SkillTreeEngine
# ---------------------------------------------------------------------------
class SkillTreeEngine:
    """技能树：从知识图谱掌握度计算技能等级。"""

    def __init__(self, dm: DataManager, kg: KnowledgeGraph, le: LearningEngine):
        self.dm = dm
        self.kg = kg
        self.le = le

    def compute(self, student_id: int, subject: str = "数学") -> List[dict]:
        """计算某学科下所有技能的等级和进度。"""
        skills = SKILL_TREE.get(subject, {})
        results = []
        rows = self.dm.query(
            "SELECT ls.knowledge_id, ls.mastery, kn.name "
            "FROM learn_state ls JOIN kg_node kn ON kn.id=ls.knowledge_id "
            "WHERE ls.student_id=? AND kn.subject=?",
            (student_id, subject),
        )
        name_to_mastery = {r["name"]: r.get("mastery", 0.0) or 0.0 for r in rows}

        for skill_name, keywords in skills.items():
            related = []
            for kn_name, m in name_to_mastery.items():
                if any(k in kn_name for k in keywords):
                    related.append(m)
            avg = sum(related) / len(related) if related else 0.0
            level = max(1, min(30, int(avg * 10)))
            next_level_at = (level + 1) / 10.0
            progress = (avg - level / 10.0) / (next_level_at - level / 10.0) if avg > 0 else 0
            results.append({
                "skill_id": f"{subject}_{skill_name}",
                "skill_name": skill_name,
                "level": level,
                "mastery": round(avg, 3),
                "progress": round(max(0, min(1, progress)), 3),
            })

        return sorted(results, key=lambda x: -x["level"])

    def get_skill_level(self, student_id: int, skill_id: str) -> int:
        """获取单个技能等级。"""
        skills = self.compute(student_id)
        for s in skills:
            if s["skill_id"] == skill_id:
                return s["level"]
        return 1


# ---------------------------------------------------------------------------
# 3. AchievementEngine
# ---------------------------------------------------------------------------
class AchievementEngine:
    """成就检测与解锁。"""

    def __init__(self, dm: DataManager, kg: KnowledgeGraph, le: LearningEngine):
        self.dm = dm
        self.kg = kg
        self.le = le

    def check_and_unlock(self, student_id: int, xp_mgr: XPManager,
                          skill_tree: SkillTreeEngine) -> List[dict]:
        """检测所有未解锁成就，满足条件则自动解锁。"""
        unlocked = {
            r["achievement_id"]
            for r in self.dm.query(
                "SELECT achievement_id FROM achievement_record WHERE student_id=?",
                (student_id,),
            )
        }
        growth = xp_mgr.get_state(student_id)
        skills = {s["skill_id"]: s for s in skill_tree.compute(student_id)}
        stats = self._get_stats(student_id)

        new_achievements = []
        for ach in ACHIEVEMENT_DEFS:
            if ach["id"] in unlocked:
                continue
            if self._check_condition(ach["condition"], growth, skills, stats):
                self.dm.execute(
                    "INSERT OR IGNORE INTO achievement_record "
                    "(student_id, achievement_id, achievement_name, unlock_time) VALUES (?,?,?,?)",
                    (student_id, ach["id"], ach["name"],
                     datetime.now().isoformat(timespec="seconds")),
                )
                if ach.get("reward_xp"):
                    xp_mgr.award(student_id, ach["reward_xp"], source=f"achievement:{ach['id']}")
                new_achievements.append(ach)
        return new_achievements

    def get_unlocked(self, student_id: int) -> List[dict]:
        """获取已解锁成就列表。"""
        return self.dm.query(
            "SELECT * FROM achievement_record WHERE student_id=? ORDER BY unlock_time",
            (student_id,),
        )

    def _get_stats(self, student_id: int) -> dict:
        """获取统计信息用于条件判断。"""
        total_q = (self.dm.query_one(
            "SELECT COUNT(*) n FROM learn_record WHERE student_id=?", (student_id,)) or {}).get("n", 0)
        hard = (self.dm.query_one(
            "SELECT COUNT(*) n FROM learn_record lr JOIN q_question q ON q.id=lr.question_id "
            "WHERE lr.student_id=? AND q.difficulty>=4", (student_id,)) or {}).get("n", 0)
        perfect = (self.dm.query_one(
            "SELECT COUNT(*) n FROM learning_event "
            "WHERE student_id=? AND event_type='session_end'", (student_id,)) or {}).get("n", 0)
        wrong_resolved = (self.dm.query_one(
            "SELECT COUNT(*) n FROM learn_wrong WHERE student_id=? AND resolved=1",
            (student_id,)) or {}).get("n", 0)
        # Streak estimation from learning_event
        return {
            "total_questions": total_q,
            "hard_question": hard,
            "perfect_session": perfect,
            "wrong_resolved": wrong_resolved,
        }

    @staticmethod
    def _check_condition(condition: str, growth: dict, skills: dict, stats: dict) -> bool:
        """检查成就解锁条件。"""
        try:
            # simple condition parser
            parts = condition.replace(">=", "|gte|").replace(">", "|gt|").replace("<=", "|lte|").replace("<", "|lt|").split("|")
            var_name = parts[0]
            op = parts[1] if len(parts) > 1 else "gte"
            val_str = parts[2] if len(parts) > 2 else "0"
            val = int(val_str)

            if var_name.startswith("skill_"):
                sid = var_name.replace("skill_", "数学_")
                actual = skills.get(sid, {}).get("level", 1)
            elif var_name == "level":
                actual = growth.get("level", 1)
            elif var_name == "total_questions":
                actual = stats.get("total_questions", 0)
            elif var_name == "hard_question":
                actual = stats.get("hard_question", 0)
            elif var_name == "perfect_session":
                actual = stats.get("perfect_session", 0)
            elif var_name == "wrong_resolved":
                actual = stats.get("wrong_resolved", 0)
            else:
                return False

            if op == "gte":
                return actual >= val
            elif op == "gt":
                return actual > val
            elif op == "lte":
                return actual <= val
            elif op == "lt":
                return actual < val
            return False
        except Exception:
            return False


# ---------------------------------------------------------------------------
# 4. DailyQuestEngine
# ---------------------------------------------------------------------------
class DailyQuestEngine:
    """每日任务：基于薄弱点和诊断结果生成。"""

    def __init__(self, dm: DataManager, kg: KnowledgeGraph, le: LearningEngine):
        self.dm = dm
        self.kg = kg
        self.le = le

    def generate(self, student_id: int, xp_mgr: XPManager) -> List[dict]:
        """生成今日任务。"""
        today = date.today().isoformat()
        # 检查是否已有今日任务
        existing = self.dm.query(
            "SELECT * FROM daily_task WHERE student_id=? AND task_date=?",
            (student_id, today),
        )
        if existing:
            return existing

        weak = self.le.weak_points(student_id, top_n=3)
        tasks = []

        # 任务 1: 薄弱知识点训练
        if weak:
            wname = ""
            kn = self.kg.get(weak[0].get("knowledge_id"))
            if kn:
                wname = kn.name
            tasks.append({
                "student_id": student_id,
                "task_date": today,
                "task_type": "weak_practice",
                "description": f"完成「{wname}」相关练习 8 题" if wname else "完成薄弱点练习 8 题",
                "target": 8,
                "reward_xp": 30,
            })

        # 任务 2: 错题修复
        wrong_count = (self.dm.query_one(
            "SELECT COUNT(*) n FROM learn_wrong WHERE student_id=? AND resolved=0",
            (student_id,),
        ) or {}).get("n", 0)
        if wrong_count > 0:
            tasks.append({
                "student_id": student_id,
                "task_date": today,
                "task_type": "fix_wrong",
                "description": f"修复 {min(3, wrong_count)} 道错题",
                "target": min(3, wrong_count),
                "reward_xp": 20,
            })

        # 任务 3: 学习时长
        tasks.append({
            "student_id": student_id,
            "task_date": today,
            "task_type": "study_time",
            "description": "学习 20 分钟",
            "target": 20,
            "reward_xp": 15,
        })

        for t in tasks:
            self.dm.execute(
                "INSERT OR IGNORE INTO daily_task "
                "(student_id, task_date, task_type, description, target, reward_xp, status) "
                "VALUES (?,?,?,?,?,?,'pending')",
                (t["student_id"], t["task_date"], t["task_type"],
                 t["description"], t["target"], t["reward_xp"]),
            )

        return self.dm.query(
            "SELECT * FROM daily_task WHERE student_id=? AND task_date=?",
            (student_id, today),
        )

    def update_progress(self, student_id: int, task_type: str, delta: int = 1):
        """更新任务进度。"""
        today = date.today().isoformat()
        row = self.dm.query_one(
            "SELECT id, progress, target, reward_xp, status FROM daily_task "
            "WHERE student_id=? AND task_date=? AND task_type=?",
            (student_id, today, task_type),
        )
        if row and row["status"] != "claimed":
            new_progress = min(row["target"], (row["progress"] or 0) + delta)
            status = "completed" if new_progress >= row["target"] else "pending"
            self.dm.execute(
                "UPDATE daily_task SET progress=?, status=? WHERE id=?",
                (new_progress, status, row["id"]),
            )

    def claim_reward(self, student_id: int, task_id: int, xp_mgr: XPManager) -> Optional[dict]:
        """领取任务奖励。"""
        row = self.dm.query_one(
            "SELECT * FROM daily_task WHERE id=? AND student_id=?",
            (task_id, student_id),
        )
        if row and row["status"] == "completed":
            result = xp_mgr.award(student_id, row["reward_xp"], source=f"daily:{row['task_type']}")
            self.dm.execute("UPDATE daily_task SET status='claimed' WHERE id=?", (task_id,))
            return result
        return None
