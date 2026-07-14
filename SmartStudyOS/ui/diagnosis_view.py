# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""AI 错因诊断中心（Phase 2.3）。

展示最新的诊断报告：
- 报告摘要（总体发现 + 可信度）
- 各诊断发现逐项展开（错误模式、频次、根因、补救步骤）
- 待处理恢复任务（含「开始强化训练」按钮 → 调用 LearningFlow）

数据全部来自 DiagnosisEngine + diagnosis_report / recovery_task 表。
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from .app_context import AppContext
from core.diagnosis_engine import DiagnosisEngine


class _Card(QFrame):
    def __init__(self, title: str = ""):
        super().__init__()
        self.setStyleSheet("""
            _Card { background: #ffffff; border: 1px solid #e1e4e8;
                    border-radius: 10px; }
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 12, 16, 12)
        self.layout.setSpacing(8)
        if title:
            lbl = QLabel(title)
            lbl.setStyleSheet("font-size:13px; font-weight:600; color:#24292f;")
            self.layout.addWidget(lbl)


class DiagnosisView(QWidget):
    """AI 错因诊断中心视图。"""

    def __init__(self, ctx: AppContext, on_start_practice: callable):
        super().__init__()
        self.ctx = ctx
        self._on_start = on_start_practice
        self._engine = DiagnosisEngine(ctx.dm, ctx.kg, ctx.le)
        self._build()

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #f0f2f5; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        self._root = QVBoxLayout(container)
        self._root.setContentsMargins(28, 20, 28, 20)
        self._root.setSpacing(16)

        # 标题
        title = QLabel("🔍 AI 学习诊断")
        title.setStyleSheet("font-size:20px; font-weight:700; color:#24292f;")
        self._root.addWidget(title)

        self._subtitle = QLabel("最近一次学习诊断报告会在学习结束后自动生成。")
        self._subtitle.setStyleSheet("font-size:13px; color:#656d76;")
        self._root.addWidget(self._subtitle)

        # 报告区域
        self._report_area = QVBoxLayout()
        self._report_area.setSpacing(12)
        self._root.addLayout(self._report_area)

        # 恢复任务区域
        self._task_area = QVBoxLayout()
        self._task_area.setSpacing(8)
        self._root.addLayout(self._task_area)

        self._root.addStretch(1)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self):
        """刷新诊断数据。"""
        self._clear_area(self._report_area)
        self._clear_area(self._task_area)

        report = self._engine.get_recent_report(self.ctx.student_id)
        if not report:
            self._subtitle.setText("暂无诊断报告。完成一次学习后系统会自动生成诊断。")
            return

        self._subtitle.setText(f"诊断时间：{report.get('created_at', '')[:16]}")

        summary = report.get("summary") or {}
        findings = summary.get("findings", [])
        total_err = summary.get("total_errors", 0)
        conf = report.get("confidence", 0.0)

        # 总体概览卡片
        overview = _Card("📊 总体诊断概览")
        overview.layout.addWidget(QLabel(
            f"本轮发现 {len(findings)} 个错误模式  ·  "
            f"共 {total_err} 次错误  ·  诊断可信度 {conf*100:.0f}%"))
        pb = QProgressBar()
        pb.setValue(int(conf * 100))
        pb.setFixedHeight(6)
        pb.setTextVisible(False)
        pb.setStyleSheet("""
            QProgressBar { background:#eaeef2; border:none; border-radius:3px; }
            QProgressBar::chunk { background:#1f6feb; border-radius:3px; }
        """)
        overview.layout.addWidget(pb)
        self._report_area.addWidget(overview)

        # 逐项诊断发现
        for i, f in enumerate(findings):
            card = _Card(f"⚠️ 发现 {i+1}：{f.get('pattern_name', '未知错误')}")
            card.setStyleSheet("""
                _Card { background:#ffffff; border:1px solid #cf222e;
                        border-radius:10px; }
            """)

            # 频次 + 可信度
            meta = QLabel(
                f"关联知识点：{f.get('knowledge_name', '')}  ·  "
                f"错误次数：{f.get('frequency', 0)}  ·  "
                f"可信度：{f.get('confidence', 0)*100:.0f}%")
            meta.setStyleSheet("font-size:12px; color:#656d76;")
            card.layout.addWidget(meta)

            # 根因标记
            if f.get("is_root_cause"):
                root_lbl = QLabel("🔴 此问题源于基础知识缺陷")
                root_lbl.setStyleSheet("font-size:12px; font-weight:600; color:#cf222e;")
                card.layout.addWidget(root_lbl)

            # 补救步骤
            steps = f.get("recovery_steps", [])
            if steps:
                steps_lbl = QLabel("补救建议：")
                steps_lbl.setStyleSheet("font-size:12px; font-weight:600; color:#24292f; margin-top:4px;")
                card.layout.addWidget(steps_lbl)
                for j, step in enumerate(steps):
                    sl = QLabel(f"  {j+1}. {step}")
                    sl.setStyleSheet("font-size:12px; color:#656d76;")
                    card.layout.addWidget(sl)

            self._report_area.addWidget(card)

        # 待处理恢复任务
        tasks = self._engine.get_pending_tasks(self.ctx.student_id)
        if tasks:
            task_title = QLabel("📋 待完成恢复任务")
            task_title.setStyleSheet("font-size:15px; font-weight:600; color:#24292f; margin-top:8px;")
            self._task_area.addWidget(task_title)
            for t in tasks:
                t_card = _Card(f"🎯 {t.get('finding_name', '恢复任务')}")
                t_card.layout.addWidget(QLabel(
                    f"目标知识点 ID：{t.get('target_knowledge_ids', [])}  "
                    f"题目数：{len(t.get('question_ids', []))}"))
                btn = QPushButton("开始强化训练  →")
                btn.setCursor(Qt.PointingHandCursor)
                btn.setStyleSheet("""
                    QPushButton { background:#1f6feb; color:#fff; font-size:13px;
                                  font-weight:600; border:none; border-radius:6px;
                                  padding:8px 16px; }
                    QPushButton:hover { background:#1857c4; }
                """)
                tid = t["id"]
                qids = t.get("question_ids", [])
                btn.clicked.connect(lambda _checked=False,
                                    kids=t.get("target_knowledge_ids", []),
                                    task_id=tid: self._start_recovery(kids, task_id))
                t_card.layout.addWidget(btn)
                self._task_area.addWidget(t_card)
        else:
            no_task = QLabel("✅ 暂无待处理恢复任务")
            no_task.setStyleSheet("font-size:13px; color:#1a7f37;")
            self._task_area.addWidget(no_task)

    def _start_recovery(self, knowledge_ids, task_id):
        """点击恢复任务，启动强化练习。"""
        self._task_id = task_id
        self._recovery_kids = knowledge_ids
        # 调用外部回调启动 LearningFlow 带指定知识点
        if self._on_start:
            self._on_start(knowledge_ids=knowledge_ids, task_id=task_id)

    def mark_task_complete(self):
        """恢复训练完成后的回调。"""
        if hasattr(self, '_task_id') and self._task_id:
            self._engine.complete_task(self._task_id, post_mastery=0.5)
            self.refresh()

    @staticmethod
    def _clear_area(layout):
        while layout.count():
            w = layout.takeAt(0).widget()
            if w:
                w.deleteLater()
