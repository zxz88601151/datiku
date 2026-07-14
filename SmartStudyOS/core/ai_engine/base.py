# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""AI Tutor 抽象接口。

定义四大能力（冻结版架构 v1.0）：
- explain：解释知识点（概念 + 举例 + 易错点 + 关联）
- generate：根据错误/年龄/水平自动生成练习
- evaluate：批改 / 诊断
- plan：基于学习状态生成今日学习计划

所有实现必须满足：敏感密钥仅从环境变量读取，绝不硬编码；
默认本地模板模式，无需联网即可演示完整闭环。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TutorRequest:
    student_id: int
    text: str                                   # 用户提问 / 上下文
    knowledge_id: Optional[int] = None
    question_id: Optional[int] = None


@dataclass
class TutorReply:
    role: str = "ai"
    content: str = ""
    similar_question: Optional[str] = None      # 出一道类似题
    check_prompt: Optional[str] = None          # 检查理解的问题


class AITutor(ABC):
    @abstractmethod
    def explain(self, req: TutorRequest) -> TutorReply:
        ...

    @abstractmethod
    def generate(self, req: TutorRequest) -> TutorReply:
        ...

    @abstractmethod
    def evaluate(self, req: TutorRequest, correct: bool, reason: str = "") -> TutorReply:
        ...

    @abstractmethod
    def plan(self, req: TutorRequest) -> TutorReply:
        ...
