# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""AI 老师 V1（Phase 2.5）。

完全基于规则引擎 + 知识图谱 + 学习数据，不依赖大模型。
每一条建议都有数据依据。

五层架构：
1. TutorContextBuilder    — 聚合用户画像 + 学习数据 + 诊断结果 → 学生状态摘要
2. ExplanationEngine      — 错因解释 + 概念教学 + 分层次讲解
3. StudyPlanner           — 目标驱动每日计划
4. AnswerCoach            — 逐题辅导
5. TutorOrchestrator      — 路由请求 + 对话记忆管理
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from database.manager import DataManager
from core.knowledge_engine import KnowledgeGraph
from core.learning_engine import LearningEngine
from core.learning_snapshot import LearningSnapshot
from core.diagnosis_engine import DiagnosisEngine, ERROR_PATTERNS
from core.user_profile import UserProfileManager, GoalEngine


# ---------------------------------------------------------------------------
# 1. TutorContextBuilder — 构建学生全面画像
# ---------------------------------------------------------------------------
class TutorContextBuilder:
    """构建当前学生的完整上下文，供各引擎使用。"""

    def __init__(self, dm: DataManager, kg: KnowledgeGraph, le: LearningEngine):
        self.dm = dm
        self.kg = kg
        self.le = le

    def build(self, student_id: int) -> dict:
        """返回学生当前状态的完整摘要。"""
        user = self.dm.query_one(
            "SELECT nickname, name, grade, target FROM user WHERE id=?", (student_id,)
        )
        name = (user.get("nickname") or user.get("name") or "同学") if user else "同学"
        grade = user.get("grade", "未知") if user else "未知"
        target = user.get("target", "日常提升") if user else "日常提升"

        # 掌握度
        progress = self.le.subject_progress(student_id)
        mastery_summary = {k: round(v, 3) for k, v in progress.items()}

        # 薄弱点
        weak = self.le.weak_points(student_id, top_n=5)
        weak_info = []
        for w in weak:
            kn = self.kg.get(w.get("knowledge_id"))
            weak_info.append({
                "name": kn.name if kn else f"#{w['knowledge_id']}",
                "mastery": round(w.get("mastery", 0.0), 3),
                "wrong_count": w.get("wrong_count", 0),
            })

        # 近期错误标签聚合
        wrong_rows = self.dm.query(
            "SELECT wrong_reason, count FROM learn_wrong "
            "WHERE student_id=? AND resolved=0 ORDER BY count DESC LIMIT 10",
            (student_id,),
        )
        recent_errors = []
        for r in wrong_rows:
            reason = (r.get("wrong_reason") or "").strip()
            if reason and reason != "待归因":
                recent_errors.append({"error": reason, "count": r.get("count", 1)})

        # 最近诊断
        diag = self.dm.query_one(
            "SELECT summary, created_at FROM diagnosis_report "
            "WHERE student_id=? ORDER BY id DESC LIMIT 1",
            (student_id,),
        )
        diagnosis_summary = ""
        if diag:
            summary = self.dm.loads(diag.get("summary") or "{}")
            findings = summary.get("findings", [])
            if findings:
                diagnosis_summary = findings[0].get("pattern_name", "")

        # 今日快照
        snapshot = LearningSnapshot(self.dm, self.le, self.kg)
        snap = snapshot.ensure_latest_snapshot(student_id)
        today_mins = snap.get("study_minutes", 0) or 0

        # 学习目标
        goals = self.dm.query(
            "SELECT target_score, current_score FROM user_goal WHERE user_id=?",
            (student_id,),
        )
        goal_info = goals[0] if goals else {"target_score": 0, "current_score": 0}

        return {
            "name": name,
            "grade": grade,
            "target": target,
            "goal": goal_info,
            "mastery": mastery_summary,
            "weak_points": weak_info,
            "recent_errors": recent_errors,
            "diagnosis_summary": diagnosis_summary,
            "today_study_minutes": today_mins,
        }


# ---------------------------------------------------------------------------
# 2. ExplanationEngine — 错因讲解 + 概念教学
# ---------------------------------------------------------------------------
class ExplanationEngine:
    """基于数据生成解释和教学内容。"""

    def __init__(self, dm: DataManager, kg: KnowledgeGraph):
        self.dm = dm
        self.kg = kg

    def explain_error(self, context: dict, knowledge_name: str = "",
                       error_tag: str = "") -> str:
        """基于学生上下文生成错因讲解。"""
        weak = context.get("weak_points", [])
        recent = context.get("recent_errors", [])
        name = context.get("name", "同学")

        # 找到匹配的知识点
        target_weak = None
        for w in weak:
            if knowledge_name and knowledge_name in w.get("name", ""):
                target_weak = w
                break
        if not target_weak and weak:
            target_weak = weak[0]

        lines = [f"{name}，我来帮你分析这个问题。\n"]
        if target_weak:
            kn = self.kg.get(target_weak.get("name"))
            wname = target_weak["name"]
            mastery = target_weak["mastery"]
            wc = target_weak["wrong_count"]

            lines.append(f"📊 **数据分析**")
            lines.append(f"你在「{wname}」上的当前掌握度是 {mastery*100:.0f}%，")
            lines.append(f"最近已连续出现 {wc} 次错误。")

            # 匹配错误模式
            matched = None
            for p in ERROR_PATTERNS:
                if any(k in wname for k in p["knowledge"]):
                    matched = p
                    break
            if matched:
                lines.append(f"\n🔍 **错误模式识别**")
                lines.append(f"系统匹配到标准模式：{matched['name']}")
                if error_tag:
                    lines.append(f"本次错误标签：{error_tag}")

                lines.append(f"\n💡 **建议学习路径**")
                for i, step in enumerate(matched.get("recovery_steps", []), 1):
                    lines.append(f"  {i}. {step}")
            else:
                lines.append(f"\n💡 **建议**")
                lines.append(f"建议重点复习 {wname} 的基本概念和典型例题。")

            # 知识节点详情
            kid = None
            for w in weak:
                kid = w
                break
            if kid:
                kn_obj = self.kg.get(kid.get("knowledge_id"))
                if kn_obj and kn_obj.formula_list:
                    lines.append(f"\n📝 **相关公式**")
                    for fm in kn_obj.formula_list[:3]:
                        lines.append(f"  {fm}")
        else:
            lines.append("目前系统还没有记录到你在该知识点的学习数据。")
            lines.append("建议先完成几道相关练习，然后我再来帮你分析。")

        return "\n".join(lines)

    def explain_concept(self, concept_name: str, grade: str = "八年级") -> str:
        """概念教学：分层解释。"""
        lines = [f"📖 **{concept_name} 讲解**\n"]

        # 查找知识节点
        rows = self.dm.query(
            "SELECT name, summary, formula_list, grade FROM kg_node "
            "WHERE subject='数学' AND name LIKE ? LIMIT 1",
            (f"%{concept_name}%",),
        )
        if not rows:
            lines.append(f"抱歉，系统中未找到「{concept_name}」的知识条目。")
            return "\n".join(lines)

        node = rows[0]
        summary = node.get("summary", "") or ""
        formulas = self.dm.loads(node.get("formula_list") or "[]")
        node_grade = node.get("grade", "")

        if summary:
            lines.append(f"**定义：** {summary}")

        if formulas:
            lines.append(f"\n**公式：**")
            for f in formulas[:5]:
                lines.append(f"  ·  {f}")

        # 分层解释（按年级级别）
        lines.append(f"\n**分层理解：**")
        if node_grade in ("七年级", "六年级", "五年级"):
            lines.append(f"  🧒 **基础理解**：{self._simple_explain(concept_name)}")
            lines.append(f"  📐 **标准定义**：{summary or '参考教材定义'}")
        else:
            lines.append(f"  🧒 **直观理解**：{self._simple_explain(concept_name)}")
            lines.append(f"  📐 **正式定义**：{summary or '参考教材定义'}")
            lines.append(f"  🎯 **应用提示**：在{grade}阶段，重点掌握与相关知识的联系和综合运用。")

        return "\n".join(lines)

    @staticmethod
    def _simple_explain(concept: str) -> str:
        """简易理解版本。"""
        explains = {
            "一次函数": "可以想象成一条直线在坐标系中移动，k 决定倾斜方向和程度，b 决定上下位置。",
            "正比例函数": "就像一个比例关系，输入乘以固定倍数得到输出，图像是一条过原点的直线。",
            "二次函数": "像抛出去的球在空中划出的弧线，开口方向由 a 的正负决定。",
            "函数": "就像一个加工机器：输入一个数，按照规则处理，输出另一个数。",
            "三角形": "三条线段围成的封闭图形，是最稳定的几何形状。",
            "圆": "到一个固定点距离相等的所有点的集合，像车轮的形状。",
            "概率": "衡量一件事发生的可能性，范围从 0（不可能）到 1（必然发生）。",
        }
        return explains.get(concept, f"{concept}是{concept[:2]}领域的基础概念，建议从教材例题入手理解。")


# ---------------------------------------------------------------------------
# 3. StudyPlanner — 每日学习计划
# ---------------------------------------------------------------------------
class StudyPlanner:
    """基于目标 + 掌握度 + 薄弱点生成每日学习计划。"""

    def __init__(self, dm: DataManager, kg: KnowledgeGraph, le: LearningEngine):
        self.dm = dm
        self.kg = kg
        self.le = le

    def generate_plan(self, context: dict, minutes: int = 20) -> str:
        """生成今日学习计划。"""
        name = context.get("name", "同学")
        weak = context.get("weak_points", [])
        goal = context.get("goal", {})
        target_score = goal.get("target_score", 0)
        current_score = goal.get("current_score", 0)
        gap = max(0, target_score - current_score)

        lines = [f"📋 **{name} 的今日学习计划**\n"]
        lines.append(f"目标：{'中考' if target_score else '日常提升'}"
                     f"{f'（目标 {target_score} 分，差距 {gap} 分）' if gap else ''}")

        # 时间分配
        if not weak:
            lines.append("\n✅ 当前无明显薄弱点，建议进行综合复习训练。")
            lines.append(f"预计 {minutes} 分钟：\n  ① 随机组卷 10 题\n  ② 错题回顾 3 题")
            return "\n".join(lines)

        w = weak[0]
        wname = w.get("name", "")
        mastery = w.get("mastery", 0.0)
        wc = w.get("wrong_count", 0)

        review_min = max(3, int(minutes * 0.25))
        practice_count = max(5, min(12, int(minutes * 0.4)))
        review_count = max(2, min(5, wc))

        lines.append(f"\n🎯 **今日重点**")
        lines.append(f"优先突破：{wname}（当前掌握度 {mastery*100:.0f}%，"
                     f"累计错误 {wc} 次）")

        lines.append(f"\n⏱ **{minutes} 分钟计划**")
        lines.append(f"  ① {wname} 知识点复习  ~{review_min} 分钟")
        lines.append(f"  ② 基础训练 {practice_count} 题")
        lines.append(f"  ③ 错题回炉 {review_count} 题")

        # 如果有次要薄弱点
        if len(weak) > 1:
            w2 = weak[1]
            lines.append(f"\n📌 **额外建议**")
            lines.append(f"  如时间充裕，建议复习 {w2.get('name', '')}"
                         f"（掌握度 {w2.get('mastery', 0)*100:.0f}%）")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 4. AnswerCoach — 逐题辅导
# ---------------------------------------------------------------------------
class AnswerCoach:
    """基于知识图谱的题目辅导。"""

    def __init__(self, dm: DataManager, kg: KnowledgeGraph):
        self.dm = dm
        self.kg = kg

    def coach(self, context: dict, question_text: str = "",
               student_answer: str = "") -> str:
        """对特定问题提供辅导。"""
        name = context.get("name", "同学")
        lines = [f"🤔 {name}，让我看看这道题。\n"]

        if not question_text:
            lines.append("请告诉我题目内容和你写的答案，我来帮你分析。")
            return "\n".join(lines)

        # 尝试在题库中匹配题目
        q = self.dm.query_one(
            "SELECT id, content, answer, analysis, knowledge_relation, difficulty"
            " FROM q_question WHERE content LIKE ? LIMIT 1",
            (f"%{question_text[:20]}%",),
        )
        if q:
            lines.append(f"📝 **题目**（难度 {q.get('difficulty', 3)}/5）")
            lines.append(f"  {q.get('content', '')[:100]}")

            if student_answer:
                correct_answer = q.get("answer", "")
                lines.append(f"\n你的答案：{student_answer}")
                lines.append(f"正确答案：{correct_answer}")
                if student_answer.strip() == correct_answer.strip():
                    lines.append("\n✅ 完全正确！继续保持。")
                else:
                    lines.append("\n❌ 这里有些偏差，我们看看原因。")

            # 分析
            analysis = q.get("analysis", "") or ""
            if analysis:
                lines.append(f"\n💡 **解析**：{analysis[:200]}")

            # 关联知识点
            kids = self.dm.loads(q.get("knowledge_relation") or "[]")
            if kids:
                lines.append(f"\n📌 **关联知识点**")
                for kid in kids[:3]:
                    kn = self.kg.get(kid)
                    if kn:
                        lines.append(f"  ·  {kn.name}")
        else:
            lines.append("我暂时没有在题库中找到完全匹配的题目。")
            lines.append("你可以试试以下方式：")
            lines.append("  1. 告诉我题目的完整描述")
            lines.append("  2. 使用「错题本」功能查看详细解析")
            lines.append("  3. 描述你卡在哪一步")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 5. TutorOrchestrator — 总调度
# ---------------------------------------------------------------------------
class TutorOrchestrator:
    """AI 老师总控制器：路由请求 + 对话记忆。"""

    def __init__(self, dm: DataManager, kg: KnowledgeGraph, le: LearningEngine):
        self.dm = dm
        self.kg = kg
        self.le = le
        self._context_builder = TutorContextBuilder(dm, kg, le)
        self._explainer = ExplanationEngine(dm, kg)
        self._planner = StudyPlanner(dm, kg, le)
        self._coach = AnswerCoach(dm, kg)

    def handle(self, student_id: int, message: str) -> str:
        """处理学生输入，返回 AI 老师回复。"""
        context = self._context_builder.build(student_id)
        msg_lower = message.lower().strip()

        # 意图识别（规则触发）
        if any(k in msg_lower for k in ["计划", "今天学", "今天练", "安排"]):
            response = self._planner.generate_plan(context)
            qtype = "plan"
        elif any(k in msg_lower for k in ["为什么错", "错在哪", "讲解", "解释"]):
            # 提取知识点名称
            kn_name = ""
            for wp in context.get("weak_points", []):
                if wp.get("name", "").lower() in msg_lower:
                    kn_name = wp["name"]
                    break
            response = self._explainer.explain_error(context, knowledge_name=kn_name)
            qtype = "explain_error"
        elif any(k in msg_lower for k in ["什么是", "什么叫", "讲解", "概念", "原理"]):
            concept = message.replace("什么是", "").replace("什么叫", "").replace("讲解", "").replace("?", "").strip()
            response = self._explainer.explain_concept(concept, context.get("grade", "八年级"))
            qtype = "explain_concept"
        elif any(k in msg_lower for k in ["复习", "建议", "提升"]):
            response = self._planner.generate_plan(context, minutes=25)
            qtype = "plan"
        elif any(k in msg_lower for k in ["诊断", "报告", "最近"]):
            diag = self.dm.query_one(
                "SELECT summary, created_at FROM diagnosis_report "
                "WHERE student_id=? ORDER BY id DESC LIMIT 1",
                (student_id,),
            )
            if diag:
                summary = self.dm.loads(diag.get("summary") or "{}")
                findings = summary.get("findings", [])
                if findings:
                    lines = [f"📋 **最近诊断报告**（{diag.get('created_at','')[:10]}）\n"]
                    for f in findings[:3]:
                        lines.append(f"  ⚠️ {f.get('pattern_name','')}  "
                                     f"(频率 {f.get('frequency',0)} 次, "
                                     f"可信度 {f.get('confidence',0)*100:.0f}%)")
                    lines.append(f"\n你可以进入「诊断中心」查看详细报告和恢复任务。")
                    response = "\n".join(lines)
                else:
                    response = "最近一次诊断未发现明显错误模式，继续保持！"
            else:
                response = "暂未生成诊断报告。完成一次学习后系统会自动分析。"
            qtype = "diagnosis"
        else:
            # 通用对话：尝试知识点理解或题目辅导
            if any(k in msg_lower for k in ["题", "做", "答案", "怎么解"]):
                response = self._coach.coach(context, question_text=message)
                qtype = "coach"
            else:
                # 问候/闲聊
                name = context.get("name", "同学")
                weak_info = context.get("weak_points", [])
                if weak_info:
                    top = weak_info[0]
                    response = (
                        f"你好，{name}！\n\n"
                        f"我注意到你最近在「{top.get('name','')}」上可以继续提升"
                        f"（当前掌握度 {top.get('mastery',0)*100:.0f}%）。\n\n"
                        f"你可以问我：\n"
                        f"  · 「为什么错」— 分析最近错误\n"
                        f"  · 「今天计划」— 生成学习计划\n"
                        f"  · 「什么是函数」— 概念讲解\n"
                        f"  · 「这道题怎么做」— 题目辅导"
                    )
                else:
                    response = f"你好，{name}！有什么学习上的问题需要我帮忙吗？"
                qtype = "greeting"

        # 保存对话记忆
        self._log_chat(student_id, qtype, message, response, context)
        return response

    def greet(self, student_id: int) -> str:
        """返回 AI 老师的开场问候（不含对话记录）。"""
        context = self._context_builder.build(student_id)
        return self.handle(student_id, "hello")

    def _log_chat(self, student_id: int, qtype: str, question: str,
                   response: str, context: dict):
        """持久化聊天记录。"""
        try:
            # 保存上下文快照摘要（避免存储过多数据）
            snapshot = {
                k: context.get(k) for k in ("mastery", "weak_points", "diagnosis_summary")
                if context.get(k)
            }
            self.dm.execute(
                "INSERT INTO tutor_chat_log "
                "(student_id, question_type, question, response, context_snapshot, created_at) "
                "VALUES (?,?,?,?,?,?)",
                (student_id, qtype, question[:500], response[:1000],
                 json.dumps(snapshot, ensure_ascii=False),
                 datetime.now().isoformat(timespec="seconds")),
            )
            # 更新辅导记忆摘要
            if qtype in ("explain_error", "plan", "diagnosis"):
                topic = qtype
                summary = response[:200]
                self.dm.execute(
                    "INSERT INTO tutor_memory (student_id, topic, summary, created_at) "
                    "VALUES (?,?,?,?)",
                    (student_id, topic, summary,
                     datetime.now().isoformat(timespec="seconds")),
                )
        except Exception as e:
            from utils.logger import log
            log.exception("tutor_memory write failed", exc_info=e)
