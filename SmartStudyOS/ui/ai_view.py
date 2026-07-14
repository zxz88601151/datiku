# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""AI 老师 V1（Phase 2.5）—— 基于学习数据的智能导师界面。

非聊天机器人风格。展示结构化的教育反馈：
- 开场问候含学生状态总结
- 快速动作按钮：错因分析 / 今日计划 / 诊断报告
- 对话区：Markdown 风格消息气泡
- 输入框 + 发送按钮

后端由 core/ai_tutor.py 的 TutorOrchestrator 驱动，纯规则引擎，不依赖大模型。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextOption
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
    QTextBrowser, QVBoxLayout, QWidget,
)

from .app_context import AppContext
from core.ai_tutor import TutorOrchestrator


class _Card(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("_Card { background:#ffffff; border:1px solid #e1e4e8; border-radius:10px; }")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 10, 12, 10)


class AIView(QWidget):
    """AI 老师主视图。"""

    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self._tutor = TutorOrchestrator(ctx.dm, ctx.kg, ctx.le)
        self._messages: list = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(8)

        # 标题
        title = QLabel("🤖 AI 学习导师")
        title.setStyleSheet("font-size:18px; font-weight:700; color:#24292f;")
        root.addWidget(title)

        # 快捷动作按钮
        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        actions = [
            ("📊 错因分析", self._action_explain),
            ("📋 今日计划", self._action_plan),
            ("📑 诊断报告", self._action_diagnosis),
        ]
        for label, cb in actions:
            btn = QPushButton(label)
            btn.setFixedHeight(32)
            btn.setStyleSheet("""
                QPushButton { background:#f3f5f9; border:1px solid #d0d7de;
                              border-radius:6px; padding:4px 12px; font-size:12px; }
                QPushButton:hover { background:#e1e7f0; }
            """)
            btn.clicked.connect(cb)
            action_row.addWidget(btn)
        action_row.addStretch(1)
        root.addLayout(action_row)

        # 对话区
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setStyleSheet("QScrollArea { border:1px solid #e1e4e8; border-radius:8px; background:#f6f8fa; }")
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(12, 12, 12, 12)
        self.chat_layout.setSpacing(10)
        self.chat_layout.addStretch(1)
        self.chat_area.setWidget(self.chat_container)
        root.addWidget(self.chat_area, 1)

        # 输入区
        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入你的问题，例如「为什么错」「今天计划」「什么是函数」…")
        self.input_field.setStyleSheet("""
            QLineEdit { border:1px solid #d0d7de; border-radius:8px;
                        padding:10px 14px; font-size:13px; }
            QLineEdit:focus { border-color:#1f6feb; }
        """)
        self.input_field.returnPressed.connect(self._send)
        input_row.addWidget(self.input_field, 1)

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedSize(60, 36)
        self.send_btn.setStyleSheet("""
            QPushButton { background:#1f6feb; color:#fff; border:none;
                          border-radius:8px; font-size:13px; font-weight:600; }
            QPushButton:hover { background:#1857c4; }
        """)
        self.send_btn.clicked.connect(self._send)
        input_row.addWidget(self.send_btn)
        root.addLayout(input_row)

    def refresh(self):
        """切换到 AI 老师时自动问候。"""
        # 只在新会话时问候
        if not self._messages:
            greeting = self._tutor.greet(self.ctx.student_id)
            self._add_message(greeting, is_user=False)

    # ---- 消息管理 ----

    def _add_message(self, text: str, is_user: bool):
        """添加消息气泡。"""
        bubble = QFrame()
        if is_user:
            bubble.setStyleSheet("""
                QFrame { background:#1f6feb; border-radius:12px 12px 4px 12px;
                         padding:10px 14px; margin:0px 40px 0px 40px; }
            """)
        else:
            bubble.setStyleSheet("""
                QFrame { background:#ffffff; border:1px solid #e1e4e8;
                         border-radius:12px 12px 12px 4px;
                         padding:10px 14px; }
            """)
        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setStyleSheet(
            "color:#ffffff; font-size:13px;" if is_user
            else "color:#24292f; font-size:13px;"
        )
        layout.addWidget(label)

        # 对齐
        container = QWidget()
        outer = QHBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(0 if is_user else 1)
        outer.addWidget(bubble)
        outer.addStretch(1 if is_user else 0)

        # 插入到 stretch 之前
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, container)

        self._messages.append({"text": text, "is_user": is_user})

        # 滚动到底部
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )

    def _send(self):
        """发送消息。"""
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self._add_message(text, is_user=True)

        # AI 回复
        response = self._tutor.handle(self.ctx.student_id, text)
        self._add_message(response, is_user=False)

    # ---- 快捷动作 ----

    def _action_explain(self):
        self.input_field.setText("为什么错")
        self._send()

    def _action_plan(self):
        self.input_field.setText("今天计划")
        self._send()

    def _action_diagnosis(self):
        self.input_field.setText("最近诊断")
        self._send()

    def _action_clear(self):
        self._messages = []
        self._clear_layout()
        self.refresh()

    def _clear_layout(self):
        while self.chat_layout.count():
            w = self.chat_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
