# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""刷题视图（Phase 3.1 重构版）。

后端全部委托给 ExerciseService（services/learning_service.py），
UI 只负责渲染题目和获取答案。
"""

from __future__ import annotations

import time

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit,
    QRadioButton, QButtonGroup, QTextBrowser, QFrame,
)
from PySide6.QtGui import QFont

from .app_context import AppContext
from . import design as ds
from services.learning_service import ExerciseService
from utils.logger import get_logger

log = get_logger("exercise_view")


class ExerciseView(QWidget):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self._svc = ExerciseService(ctx.dm, ctx.bank, ctx.le, ctx.kg)
        self.sess = None
        self.idx = 0
        self.current = None
        self._entry_ts = 0.0
        self._feedback_showing = False
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("学科："))
        self.subject = QComboBox()
        self.subject.addItems(["数学", "英语", "语文"])
        bar.addWidget(self.subject)
        bar.addWidget(QLabel("年级："))
        self.grade = QComboBox()
        self.grade.addItems(["七年级", "八年级", "九年级",
                            "高一", "高二", "高三",
                            "一年级", "二年级", "三年级",
                            "四年级", "五年级", "六年级"])
        self.grade.setCurrentText("七年级")
        bar.addWidget(self.grade)
        start = QPushButton("开始练习")
        start.setStyleSheet(ds.btn_primary_css())
        start.clicked.connect(self._start)
        bar.addWidget(start)
        bar.addStretch(1)
        root.addLayout(bar)

        self.progress_lbl = QLabel("")
        self.progress_lbl.setStyleSheet(f"font-size:13px; color:{ds.COLOR['text_secondary']};")
        root.addWidget(self.progress_lbl)

        self.area = QVBoxLayout()
        root.addLayout(self.area, 1)

        self._show_placeholder()

    def _clear_area(self):
        while self.area.count():
            w = self.area.takeAt(0).widget()
            if w:
                w.deleteLater()

    def _show_placeholder(self):
        self._clear_area()
        lbl = QLabel("选择学科与年级后点击「开始练习」，系统会按你的薄弱点智能组卷。")
        lbl.setStyleSheet(f"color:{ds.COLOR['text_secondary']};")
        self.area.addWidget(lbl)

    def _start(self):
        subj = self.subject.currentText()
        grade = self.grade.currentText()
        self.sess = self._svc.create_practice(
            self.ctx.student_id, subject=subj, grade=grade, size=10
        )
        self.idx = 0
        if not self.sess or not self.sess.questions:
            self._clear_area()
            lbl = QLabel(f"「{subj} {grade}」暂无题目，请先导入题库种子数据。")
            lbl.setStyleSheet(f"color:{ds.COLOR['danger']};")
            self.area.addWidget(lbl)
            self.progress_lbl.setText("")
            log.warning(f"no questions for {subj} {grade}")
            return
        self._render_current()

    def _render_current(self):
        self._clear_area()
        self._feedback_showing = False
        if self.idx >= len(self.sess.questions):
            self.progress_lbl.setText("练习完成 🎉")
            lbl = QLabel("本轮练习完成！查看「成长」页面查看 XP 奖励。")
            lbl.setStyleSheet(f"color:{ds.COLOR['text_secondary']};")
            self.area.addWidget(lbl)
            return
        self.current = self.sess.questions[self.idx]
        q = self.current
        self.progress_lbl.setText(
            f"第 {self.idx + 1} / {len(self.sess.questions)} 题  ·  "
            f"{q.type} · 难度 {q.difficulty}/5"
        )

        # 题目内容
        content = QLabel(q.content)
        content.setWordWrap(True)
        content.setStyleSheet(f"font-size:14px; color:{ds.COLOR['text_primary']};"
                              f"background:{ds.COLOR['bg_subtle']};"
                              f"padding:12px; border-radius:8px;")
        self.area.addWidget(content)

        self.answer_group = QButtonGroup(self)
        if q.is_choice:
            for opt in self.ctx.bank.get_options(q.id):
                rb = QRadioButton(f"{opt.label}. {opt.text}")
                rb.setProperty("label", opt.label)
                rb.setStyleSheet(f"font-size:14px; padding:4px 0; color:{ds.COLOR['text_primary']};")
                self.answer_group.addButton(rb)
                self.area.addWidget(rb)
        else:
            self.text_input = QLineEdit()
            self.text_input.setPlaceholderText("在此输入答案…")
            self.text_input.setStyleSheet(
                f"border:1px solid {ds.COLOR['border']}; border-radius:6px;"
                f"padding:8px 12px; font-size:14px;")
            self.area.addWidget(self.text_input)

        submit = QPushButton("提交")
        submit.setStyleSheet(ds.btn_primary_css())
        submit.clicked.connect(self._submit)
        self.area.addWidget(submit)

        self.feedback = QLabel("")
        self.feedback.setStyleSheet(f"font-size:14px; padding:8px 0;")
        self.area.addWidget(self.feedback)

        self._entry_ts = time.time()

    def _submit(self):
        q = self.current
        if q.is_choice:
            checked = self.answer_group.checkedButton()
            if not checked:
                self.feedback.setText("请选择一个选项。")
                return
            ans = checked.property("label")
        else:
            ans = self.text_input.text().strip()
            if not ans:
                self.feedback.setText("请输入答案。")
                return

        rec = self._svc.submit_answer(self.sess, self._entry_ts, ans)
        correct = rec.correct
        self.feedback.setText("✅ 答对了！" if correct else "❌ 答错了。")
        self.feedback.setStyleSheet(
            f"color:{ds.COLOR['success']};" if correct else f"color:{ds.COLOR['danger']};"
        )

        if rec.error_tags:
            tags_str = "  ·  ".join(rec.error_tags[:3])
            self.feedback.setText(self.feedback.text() + f"\n错误类型：{tags_str}")

        nxt = QPushButton("下一题 →")
        nxt.setStyleSheet(ds.btn_primary_css())
        nxt.clicked.connect(self._next)
        self.area.addWidget(nxt)

    def _next(self):
        self.idx += 1
        if self.idx >= len(self.sess.questions):
            # 完成时触发完整后处理
            result = self._svc.complete_practice(self.sess)
            report = result["session_report"]
            d_report = result["diagnosis_report"]
            self._clear_area()
            self.progress_lbl.setText("练习完成 🎉")
            lines = [
                f"正确 {report['correct']} / {report['total']} 题",
                f"准确率 {report['accuracy']:.0%}",
                f"用时 {report['total_duration_sec'] // 60} 分 {report['total_duration_sec'] % 60} 秒",
            ]
            if d_report and hasattr(d_report, 'findings') and d_report.findings:
                lines.append(f"诊断发现 {len(d_report.findings)} 个错误模式")
            for line in lines:
                lbl = QLabel(line)
                lbl.setStyleSheet(f"font-size:14px; color:{ds.COLOR['text_secondary']};")
                self.area.addWidget(lbl)
        else:
            self._render_current()

    def refresh(self):
        if not self.sess:
            self._show_placeholder()
