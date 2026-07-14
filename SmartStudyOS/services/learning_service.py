# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""ExerciseService（Phase 3.1 稳定性重构）。

统一所有答题入口的核心服务层。职责：

- create_practice  → 创建学习会话
- submit_answer   → 提交答案 + 引擎更新 + XP 授予 + 每日任务进度
- complete_practice → 完成会话 + 自动诊断 + 成就检测

UI 层（ExerciseView / LearningFlow）不再直接操作引擎或数据库，
只通过此服务层与系统交互。
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.logger import get_logger
from database.manager import DataManager
from core.learning_session import LearningSession, AnswerRecord
from core.diagnosis_engine import DiagnosisEngine
from core.growth_engine import (
    XPManager, SkillTreeEngine, AchievementEngine, DailyQuestEngine,
    XP_PER_QUESTION, XP_CORRECT_BONUS, XP_HARD_BONUS, XP_SESSION_BONUS,
)

log = get_logger("exercise_service")


class ExerciseService:
    """练习服务：统一 ExerciseView 和 LearningFlow 的后端逻辑。"""

    def __init__(self, dm: DataManager, bank, le, kg):
        self.dm = dm
        self.bank = bank
        self.le = le
        self.kg = kg
        self._xp = XPManager(dm)
        self._skills = SkillTreeEngine(dm, kg, le)
        self._ach = AchievementEngine(dm, kg, le)
        self._quests = DailyQuestEngine(dm, kg, le)

    def create_practice(self, student_id: int, subject: str = "数学",
                        grade: str = "七年级", size: int = 10,
                        knowledge_ids: Optional[List[int]] = None) -> LearningSession:
        """创建一次练习会话，返回 LearningSession 实例。"""
        log.info(f"create_practice: student={student_id} subject={subject} grade={grade}")
        sess = LearningSession(self.bank, self.le, self.dm)
        sess.create(student_id, subject=subject, grade=grade,
                    size=size, knowledge_ids=knowledge_ids)
        if not sess.questions:
            log.warning(f"create_practice: no questions for subject={subject} grade={grade}")
        return sess

    def submit_answer(self, sess: LearningSession, entry_time: float,
                       answer: str) -> AnswerRecord:
        """提交答案，返回 AnswerRecord。自动处理 XP+任务进度。"""
        rec = sess.submit_answer(entry_time, answer)
        sid = sess.student_id

        # XP 授予
        try:
            self._xp.award(sid, XP_PER_QUESTION, source="question")
            if rec.correct:
                self._xp.award(sid, XP_CORRECT_BONUS, source="correct")
            if rec.difficulty >= 4:
                self._xp.award(sid, XP_HARD_BONUS, source="hard")
        except Exception as e:
            log.exception("xp award failed", exc_info=e)

        # 每日任务进度（薄弱点练习）
        try:
            self._quests.update_progress(sid, "weak_practice", 1)
        except Exception as e:
            log.exception("daily quest progress failed", exc_info=e)

        log.info(f"submit_answer: q={rec.question_id} correct={rec.correct} spent={rec.spent_sec}s")
        return rec

    def complete_practice(self, sess: LearningSession) -> Dict[str, Any]:
        """完成练习，运行诊断、授予会话 XP、检测成就。

        返回: {"session_report": dict, "diagnosis_report": DiagnosisReport}
        """
        report = sess.complete()
        sid = sess.student_id

        # 会话 XP
        try:
            self._xp.award(sid, XP_SESSION_BONUS, source="session")
        except Exception as e:
            log.exception("session xp award failed", exc_info=e)

        # 自动诊断
        d_report = None
        try:
            engine = DiagnosisEngine(self.dm, self.kg, self.le)
            session_results = []
            for rec in sess.records:
                session_results.append({
                    "question_id": rec.question_id,
                    "correct": rec.correct,
                    "error_tags": rec.error_tags,
                    "knowledge_id": rec.knowledge_id,
                })
            d_report = engine.run_full_diagnosis(sid, sess.session_id, session_results)
        except Exception as e:
            log.exception("diagnosis failed", exc_info=e)

        # 成就检测
        try:
            new_ach = self._ach.check_and_unlock(sid, self._xp, self._skills)
            if new_ach:
                log.info(f"new achievements unlocked: {[a['id'] for a in new_ach]}")
        except Exception as e:
            log.exception("achievement check failed", exc_info=e)

        # 每日任务：学习时长
        try:
            duration_min = report.get("total_duration_sec", 0) // 60
            self._quests.update_progress(sid, "study_time", delta=duration_min)
            # 错题修复（无对应答错时 count=0）
            wrong_count = report.get("wrong", 0)
            if wrong_count > 0:
                self._quests.update_progress(sid, "fix_wrong", delta=wrong_count)
        except Exception as e:
            log.exception("daily quest completion failed", exc_info=e)

        log.info(f"complete_practice: session={sess.session_id} "
                 f"correct={report['correct']}/{report['total']} "
                 f"accuracy={report['accuracy']:.0%}")

        return {
            "session_report": report,
            "diagnosis_report": d_report,
        }
