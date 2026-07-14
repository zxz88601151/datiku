# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""今日学习中心（Phase 2.1 新首页）。

展示：
- 时段问候（早上好/下午好/晚上好 + 学生昵称）
- 今日学习计划卡（基于 weak_points 推荐薄弱知识点）
- 快速掌握度概览
- "开始学习 →" 按钮 → 回调启动学习流
"""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget, QProgressBar,
)

from .app_context import AppContext


class _Card(QFrame):
    """圆角卡片容器（白色背景 + 灰色边框）。"""

    def __init__(self, title: str = ""):
        super().__init__()
        self.setStyleSheet("""
            _Card {
                background: #ffffff;
                border: 1px solid #e1e4e8;
                border-radius: 12px;
                padding: 4px;
            }
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 16, 20, 16)
        self._layout.setSpacing(8)
        if title:
            lbl = QLabel(title)
            lbl.setStyleSheet("font-size:15px; font-weight:600; color:#24292f;")
            self._layout.addWidget(lbl)


class LearningCenter(QWidget):
    """今日学习中心——学生打开软件首先看到的视图。"""

    def __init__(self, ctx: AppContext, on_start_learning: callable):
        super().__init__()
        self.ctx = ctx
        self._on_start = on_start_learning
        self._build()

    # ---- 构建 ---------------------------------------------------

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        # 固定宽度约束（居中），最大 600px
        center = QVBoxLayout()
        center.setSpacing(16)
        root.addLayout(center)

        # ----- 头部：问候语 -----
        self.greeting = QLabel()
        self.greeting.setStyleSheet("font-size:22px; font-weight:700; color:#24292f;")
        center.addWidget(self.greeting)

        self.date_lbl = QLabel()
        self.date_lbl.setStyleSheet("font-size:13px; color:#656d76;")
        center.addWidget(self.date_lbl)

        center.addSpacing(8)

        # ----- 今日学习计划卡片 -----
        plan_card = _Card("📋 今日学习计划")
        self.plan_subject = QLabel("数学")
        self.plan_subject.setStyleSheet("font-size:13px; color:#656d76;")
        plan_card._layout.addWidget(self.plan_subject)

        self.plan_focus = QLabel("加载中…")
        self.plan_focus.setStyleSheet("font-size:18px; font-weight:600; color:#24292f;")
        plan_card._layout.addWidget(self.plan_focus)

        # 题量 + 预计时间
        meta_row = QHBoxLayout()
        self.plan_count = QLabel("10 道题")
        self.plan_count.setStyleSheet("font-size:13px; color:#656d76;")
        meta_row.addWidget(self.plan_count)
        meta_row.addWidget(QLabel("·"))
        self.plan_time = QLabel("预计 15 分钟")
        self.plan_time.setStyleSheet("font-size:13px; color:#656d76;")
        meta_row.addWidget(self.plan_time)
        meta_row.addStretch(1)
        plan_card._layout.addLayout(meta_row)

        # 开始学习按钮
        start_btn = QPushButton("开始学习  →")
        start_btn.setCursor(Qt.PointingHandCursor)
        start_btn.setStyleSheet("""
            QPushButton {
                background: #1f6feb; color: #ffffff; font-size: 16px; font-weight: 600;
                border: none; border-radius: 8px; padding: 12px 0;
                min-height: 20px;
            }
            QPushButton:hover { background: #1857c4; }
        """)
        start_btn.clicked.connect(self._on_start)
        plan_card._layout.addWidget(start_btn)
        center.addWidget(plan_card)

        center.addSpacing(8)

        # ----- 学习概览卡片 -----
        stats_card = _Card("📊 学习概览")
        self.stats_widget = QWidget()
        self.stats_layout = QVBoxLayout(self.stats_widget)
        self.stats_layout.setContentsMargins(0, 0, 0, 0)
        self.stats_layout.setSpacing(6)
        stats_card._layout.addWidget(self.stats_widget)
        center.addWidget(stats_card)

        center.addStretch(1)

    # ---- 刷新 ---------------------------------------------------

    def refresh(self):
        """每次切换到该视图时刷新数据。"""
        # 学生昵称
        name = "小明"
        try:
            row = self.ctx.dm.query_one("SELECT name FROM user WHERE id=?", (self.ctx.student_id,))
            if row and row.get("name"):
                name = row["name"]
        except Exception as e:
            from utils.logger import log
            log.exception("learning_center refresh failed", exc_info=e)

        # 时段问候
        hour = datetime.now().hour
        if hour < 6:
            greet = "夜深了"
        elif hour < 12:
            greet = "早上好"
        elif hour < 14:
            greet = "中午好"
        elif hour < 18:
            greet = "下午好"
        else:
            greet = "晚上好"
        self.greeting.setText(f"{greet}，{name}")

        today = datetime.now().strftime("%Y 年 %m 月 %d 日   %A")
        self.date_lbl.setText(today)

        # 今日学习计划：取最薄弱的前 2 个知识点
        weak = self.ctx.le.weak_points(self.ctx.student_id, top_n=5)
        kg = self.ctx.kg

        if weak:
            top = weak[0]
            kn = kg.get(top["knowledge_id"])
            kname = kn.name if kn else "未知知识点"
            self.plan_focus.setText(f"🔥 {kname}")
            self.plan_count.setText(f"{top.get('count', 10)} 道题")

            # 计算预计时间：每次 60-120s
            qty = top.get("count", 10)
            est = max(5, qty * 90 // 60)
            self.plan_time.setText(f"预计 {est} 分钟")
        else:
            self.plan_focus.setText("🎉 暂无薄弱点")
            self.plan_count.setText("已完成全部知识点")
            self.plan_time.setText("")

        # 掌握度概览
        self._clear_layout(self.stats_layout)
        progress = self.ctx.le.subject_progress(self.ctx.student_id)
        for subj, pct in sorted(progress.items(), key=lambda x: x[1]):
            row_w = QWidget()
            rl = QHBoxLayout(row_w)
            rl.setContentsMargins(0, 2, 0, 2)
            lbl = QLabel(subj)
            lbl.setStyleSheet("font-size:13px; color:#24292f; min-width:40px;")
            rl.addWidget(lbl)
            pb = QProgressBar()
            pb.setValue(int(pct * 100))
            pb.setFixedHeight(8)
            pb.setTextVisible(False)
            pb.setStyleSheet("""
                QProgressBar { background: #eaeef2; border-radius: 4px; border: none; }
                QProgressBar::chunk { background: #1f6feb; border-radius: 4px; }
            """)
            rl.addWidget(pb, 1)
            pct_lbl = QLabel(f"{pct * 100:.0f}%")
            pct_lbl.setStyleSheet("font-size:12px; color:#656d76; min-width:36px;")
            rl.addWidget(pct_lbl)
            self.stats_layout.addWidget(row_w)

    # ---- 辅助 ---------------------------------------------------

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            w = layout.takeAt(0).widget()
            if w:
                w.deleteLater()
