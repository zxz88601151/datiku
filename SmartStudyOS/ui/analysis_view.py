# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""数据分析视图 —— 学习画像。

展示分学科掌握度（进度条）+ 弱项明细表（知识点/掌握度/错次/推荐指数）。
数据来自 Learning Engine，可扩展为雷达图 / 成长曲线（后续接入 PyQtGraph）。
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar, QGroupBox, QTableWidget,
    QTableWidgetItem, QHBoxLayout,
)

from .app_context import AppContext
from . import design as ds


class AnalysisView(QWidget):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)
        root.addWidget(QLabel("学习数据分析"))

        prog_box = QGroupBox("学科掌握度")
        pa = QVBoxLayout(prog_box)
        self.prog_area = QVBoxLayout()
        pa.addLayout(self.prog_area)
        root.addWidget(prog_box)

        weak_box = QGroupBox("薄弱点明细（按推荐指数排序）")
        wa = QVBoxLayout(weak_box)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["知识点", "学科/年级", "掌握度", "错次", "推荐指数"])
        self.table.setColumnWidth(0, 160)
        wa.addWidget(self.table)
        root.addWidget(weak_box, 1)

    def refresh(self):
        while self.prog_area.count():
            w = self.prog_area.takeAt(0).widget()
            if w:
                w.deleteLater()
        progress = self.ctx.le.subject_progress(self.ctx.student_id)
        for subj, m in progress.items():
            row = QHBoxLayout()
            row.addWidget(QLabel(subj))
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(int(m * 100))
            row.addWidget(bar, 1)
            row.addWidget(QLabel(f"{int(m * 100)}%"))
            self.prog_area.addLayout(row)

        weak = self.ctx.le.weak_points(self.ctx.student_id, top_n=20)
        self.table.setRowCount(len(weak))
        for i, w in enumerate(weak):
            self.table.setItem(i, 0, QTableWidgetItem(w["name"]))
            self.table.setItem(i, 1, QTableWidgetItem(f"{w['subject']} {w['grade']}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{int(w['mastery']*100)}%"))
            self.table.setItem(i, 3, QTableWidgetItem(str(w["wrong_count"])))
            self.table.setItem(i, 4, QTableWidgetItem(str(w["recommend_score"])))
