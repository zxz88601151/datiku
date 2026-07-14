# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""UI 与引擎的连接上下文（应用级单例）。

把四个引擎 + 当前学生封装在一起，供各视图共享，避免重复实例化。
UI 层不直接碰 SQL，只通过引擎 API 取数。
"""

from __future__ import annotations

from typing import Optional

from database.manager import DataManager
from core.knowledge_engine import KnowledgeGraph
from core.learning_engine import LearningEngine
from core.question_engine import QuestionBank
from core.ai_engine import build_tutor


class AppContext:
    def __init__(self, student_id: int = 1):
        self.dm = DataManager()
        self.kg = KnowledgeGraph(self.dm)
        self.le = LearningEngine(self.dm)
        self.bank = QuestionBank(self.dm, self.le)
        self.tutor = build_tutor(self.dm)
        self.student_id = student_id

    def close(self):
        self.dm.close()
