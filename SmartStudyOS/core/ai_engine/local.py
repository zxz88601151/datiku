# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""本地模板 AI Tutor（无需联网 / 无需密钥）。

本地模式不调用任何外部模型，而是基于知识图谱内容 + 学习状态生成结构化讲解，
保证在没接 API 时也能演示「AI 老师」闭环。后续可平滑替换为 API 实现。
"""

from __future__ import annotations

from typing import Optional

import config.settings as cfg
from database.manager import DataManager
from core.knowledge_engine import KnowledgeGraph
from core.learning_engine import LearningEngine
from .base import AITutor, TutorRequest, TutorReply


class LocalTutor(AITutor):
    def __init__(self, dm: DataManager):
        self.dm = dm
        self.kg = KnowledgeGraph(dm)
        self.le = LearningEngine(dm)

    def explain(self, req: TutorRequest) -> TutorReply:
        node = self.kg.get(req.knowledge_id) if req.knowledge_id else None
        if not node:
            # 尝试按文本搜索
            hits = self.kg.search(req.text)
            node = hits[0] if hits else None
        if not node:
            return TutorReply(content=f"暂时没有找到「{req.text}」相关的知识点，换个说法试试？")

        mastery = self.le.get_state(req.student_id, node.id).mastery
        parts = [
            f"📘 知识点：{node.name}（{node.grade} · {node.subject}）",
            f"【概念】{node.content or '（待补充）'}",
        ]
        if node.formula:
            parts.append(f"【公式】{node.formula}")
        if node.examples:
            parts.append(f"【例题】{node.examples}")
        if node.pitfalls:
            parts.append(f"【易错点】{node.pitfalls}")
        related = self.kg.get_related(node.id)
        if related:
            parts.append("【关联知识】" + "、".join(n.name for n in related))
        parts.append(f"\n当前掌握度：{int(mastery * 100)}%。"
                     + ("建议多练习巩固。" if mastery < 0.6 else "继续保持！"))
        similar = self._pick_similar(node.id)
        return TutorReply(
            content="\n\n".join(parts),
            similar_question=similar,
            check_prompt=f"你能用自己的话解释一下「{node.name}」吗？",
        )

    def generate(self, req: TutorRequest) -> TutorReply:
        weak = self.le.weak_points(req.student_id, top_n=3)
        if not weak:
            return TutorReply(content="先去刷几道题，我才能知道你的薄弱点哦～")
        lines = ["根据你的学习状态，建议优先强化："]
        for w in weak:
            lines.append(f"· {w['name']}（掌握度 {int(w['mastery'] * 100)}%，推荐指数 {w['recommend_score']}）")
        return TutorReply(content="\n".join(lines))

    def evaluate(self, req: TutorRequest, correct: bool, reason: str = "") -> TutorReply:
        if correct:
            return TutorReply(content="✅ 答对了！保持节奏，这道题对应的知识点已强化。")
        msg = "❌ 答错了。"
        if reason:
            msg += f"\n归因：{reason}。"
        node = self.kg.get(req.knowledge_id) if req.knowledge_id else None
        if node:
            msg += f"\n建议回到「{node.name}」的概念与例题再巩固一次。"
        return TutorReply(content=msg)

    def plan(self, req: TutorRequest) -> TutorReply:
        weak = self.le.weak_points(req.student_id, top_n=3)
        if not weak:
            return TutorReply(content="今日暂无特别薄弱项，按计划复习即可。")
        lines = ["🗓️ 今日学习计划："]
        for i, w in enumerate(weak, 1):
            lines.append(f"{i}. 强化「{w['name']}」—— 做 10 道相关题，目标掌握度提升到 70%。")
        return TutorReply(content="\n".join(lines))

    # ---- 内部辅助 -----------------------------------------------------
    def _pick_similar(self, knowledge_id: int) -> Optional[str]:
        from core.question_engine import QuestionBank
        bank = QuestionBank(self.dm, self.le)
        qs = bank.get_by_knowledge(knowledge_id)
        if not qs:
            return None
        q = qs[0]
        return f"{q.content}\n（参考答案：{q.answer or '见解析'}）"
