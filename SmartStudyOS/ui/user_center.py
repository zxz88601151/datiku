# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""用户中心（Phase 2.4）。

展示用户资料、学习目标、当前能力概览。支持编辑基本信息和目标设置。
"""

from __future__ import annotations

import json
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QProgressBar,
    QPushButton, QScrollArea, QSpinBox, QVBoxLayout, QWidget,
)

from .app_context import AppContext
from core.user_profile import UserProfileManager, GoalEngine


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
            lbl.setStyleSheet("font-size:14px; font-weight:600; color:#24292f;")
            self.layout.addWidget(lbl)


class UserCenterView(QWidget):
    """用户中心视图。"""

    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self._profile_mgr = UserProfileManager(ctx.dm)
        self._goal_engine = GoalEngine(ctx.dm, ctx.kg, ctx.le)
        self._editing = False
        self._build()

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #f0f2f5; }")

        container = QWidget()
        self._root = QVBoxLayout(container)
        self._root.setContentsMargins(28, 20, 28, 20)
        self._root.setSpacing(14)

        # 标题
        title = QLabel("👤 用户中心")
        title.setStyleSheet("font-size:20px; font-weight:700; color:#24292f;")
        self._root.addWidget(title)

        # 头像/基本信息卡片
        self._profile_card = _Card()
        self._build_profile_section()
        self._root.addWidget(self._profile_card)

        # 学习目标卡片
        self._goal_card = _Card("🎯 学习目标")
        self._build_goal_section()
        self._root.addWidget(self._goal_card)

        # 能力概览卡片
        self._stats_card = _Card("📊 能力概览")
        self._root.addWidget(self._stats_card)

        self._root.addStretch(1)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _build_profile_section(self):
        """构建基本信息区域。"""
        self._profile_card.layout.addWidget(QLabel("基本信息"))
        row1 = QHBoxLayout()
        self.lbl_avatar = QLabel("👤")
        self.lbl_avatar.setStyleSheet("font-size:36px;")
        row1.addWidget(self.lbl_avatar)

        info = QVBoxLayout()
        self.lbl_name = QLabel("")
        self.lbl_name.setStyleSheet("font-size:18px; font-weight:700; color:#24292f;")
        info.addWidget(self.lbl_name)

        self.lbl_meta = QLabel("")
        self.lbl_meta.setStyleSheet("font-size:13px; color:#656d76;")
        info.addWidget(self.lbl_meta)
        row1.addLayout(info, 1)
        self._profile_card.layout.addLayout(row1)

        # 编辑按钮
        self.btn_edit = QPushButton("编辑资料")
        self.btn_edit.setFixedWidth(100)
        self.btn_edit.setStyleSheet("""
            QPushButton { background:#f3f5f9; border:1px solid #d0d7de;
                          border-radius:6px; padding:6px 12px; font-size:12px; }
            QPushButton:hover { background:#e1e7f0; }
        """)
        self.btn_edit.clicked.connect(self._toggle_edit)
        self._profile_card.layout.addWidget(self.btn_edit)

        # 编辑表单（默认隐藏）
        self._edit_widget = QWidget()
        ef = QVBoxLayout(self._edit_widget)
        ef.setSpacing(6)

        row_nn = QHBoxLayout()
        row_nn.addWidget(QLabel("昵称："))
        self.edit_nickname = QLineEdit()
        self.edit_nickname.setStyleSheet("border:1px solid #d0d7de; border-radius:4px; padding:4px 8px;")
        row_nn.addWidget(self.edit_nickname, 1)
        ef.addLayout(row_nn)

        row_gr = QHBoxLayout()
        row_gr.addWidget(QLabel("年级："))
        self.edit_grade = QComboBox()
        self.edit_grade.addItems(["七年级", "八年级", "九年级", "高一", "高二", "高三"])
        row_gr.addWidget(self.edit_grade, 1)
        ef.addLayout(row_gr)

        row_tg = QHBoxLayout()
        row_tg.addWidget(QLabel("目标："))
        self.edit_target = QComboBox()
        self.edit_target.addItems(["中考", "日常提升", "竞赛", "高考"])
        row_tg.addWidget(self.edit_target, 1)
        ef.addLayout(row_tg)

        btn_save = QPushButton("保存")
        btn_save.setStyleSheet("""
            QPushButton { background:#1f6feb; color:#fff; border:none;
                          border-radius:6px; padding:6px 16px; font-size:13px; }
            QPushButton:hover { background:#1857c4; }
        """)
        btn_save.clicked.connect(self._save_edit)
        ef.addWidget(btn_save)
        self._edit_widget.hide()
        self._profile_card.layout.addWidget(self._edit_widget)

    def _build_goal_section(self):
        """构建目标设置区域。"""
        row = QHBoxLayout()
        row.addWidget(QLabel("数学目标分："))
        self.goal_score = QSpinBox()
        self.goal_score.setRange(0, 150)
        self.goal_score.setValue(120)
        row.addWidget(self.goal_score)
        row.addWidget(QLabel("当前分："))
        self.current_score = QSpinBox()
        self.current_score.setRange(0, 150)
        self.current_score.setValue(82)
        row.addWidget(self.current_score)
        row.addStretch(1)
        self._goal_card.layout.addLayout(row)

        self.btn_set_goal = QPushButton("更新目标")
        self.btn_set_goal.setStyleSheet("""
            QPushButton { background:#1f6feb; color:#fff; border:none;
                          border-radius:6px; padding:6px 16px; font-size:12px;
                          max-width:100px; }
            QPushButton:hover { background:#1857c4; }
        """)
        self.btn_set_goal.clicked.connect(self._save_goal)
        self._goal_card.layout.addWidget(self.btn_set_goal)

        self.lbl_goal_gap = QLabel("")
        self.lbl_goal_gap.setStyleSheet("font-size:12px; color:#656d76;")
        self._goal_card.layout.addWidget(self.lbl_goal_gap)

    def refresh(self):
        """刷新用户资料。"""
        user = self._profile_mgr.get_user(self.ctx.student_id)
        if not user:
            self.lbl_name.setText("未找到用户")
            self.lbl_meta.setText("请创建一个用户账号。")
            return

        self.lbl_name.setText(user.get("nickname", "") or user.get("name", ""))
        meta_parts = [user.get("grade", "未设置年级")]
        if user.get("target"):
            meta_parts.append(f"目标：{user['target']}")
        self.lbl_meta.setText(" · ".join(meta_parts))

        # 编辑表单同步
        self.edit_nickname.setText(user.get("nickname", ""))
        grade_idx = self.edit_grade.findText(user.get("grade", ""))
        if grade_idx >= 0:
            self.edit_grade.setCurrentIndex(grade_idx)
        target_idx = self.edit_target.findText(user.get("target", ""))
        if target_idx >= 0:
            self.edit_target.setCurrentIndex(target_idx)

        # 目标
        goals = user.get("goals", [])
        if goals:
            g = goals[0]
            self.goal_score.setValue(g.get("target_score", 120))
            self.current_score.setValue(g.get("current_score", 0))
        self._update_goal_gap()

        # 能力概览
        self._refresh_stats()

    def _update_goal_gap(self):
        target = self.goal_score.value()
        current = self.current_score.value()
        gap = target - current
        if gap > 0:
            self.lbl_goal_gap.setText(f"差距：{gap} 分  ·  建议聚焦薄弱知识点针对性训练")
        else:
            self.lbl_goal_gap.setText("✅ 已达到目标分，继续保持！")

    def _refresh_stats(self):
        """刷新能力概览卡片。"""
        self._clear_card_stats()
        sid = self.ctx.student_id

        # 掌握度
        progress = self.ctx.le.subject_progress(sid)
        for subj, pct in sorted(progress.items(), key=lambda x: -x[1]):
            row = QHBoxLayout()
            lbl = QLabel(subj)
            lbl.setStyleSheet("font-size:13px; color:#24292f; min-width:50px;")
            row.addWidget(lbl)
            pb = QProgressBar()
            pb.setValue(int(pct * 100))
            pb.setFixedHeight(6)
            pb.setTextVisible(False)
            color = "#1a7f37" if pct >= 0.7 else "#d4a72c" if pct >= 0.4 else "#cf222e"
            pb.setStyleSheet(f"""
                QProgressBar {{ background:#eaeef2; border:none; border-radius:3px; }}
                QProgressBar::chunk {{ background:{color}; border-radius:3px; }}
            """)
            row.addWidget(pb, 1)
            row.addWidget(QLabel(f"{pct*100:.0f}%"))
            self._stats_card.layout.addLayout(row)

        # 薄弱点
        weak = self.ctx.le.weak_points(sid, top_n=5)
        if weak:
            wk_lbl = QLabel("薄弱知识点：")
            wk_lbl.setStyleSheet("font-size:12px; font-weight:600; color:#24292f; margin-top:4px;")
            self._stats_card.layout.addWidget(wk_lbl)
            for w in weak[:3]:
                kn = self.ctx.kg.get(w.get("knowledge_id"))
                name = kn.name if kn else "未知"
                ml = QLabel(f"  ·  {name}  (掌握度 {w.get('mastery', 0)*100:.0f}%)")
                ml.setStyleSheet("font-size:12px; color:#656d76;")
                self._stats_card.layout.addWidget(ml)

    def _clear_card_stats(self):
        while self._stats_card.layout.count():
            w = self._stats_card.layout.takeAt(0).widget()
            if w:
                w.deleteLater()

    # ---- 编辑交互 ----
    def _toggle_edit(self):
        self._editing = not self._editing
        self._edit_widget.setVisible(self._editing)
        self.btn_edit.setText("取消编辑" if self._editing else "编辑资料")

    def _save_edit(self):
        self._profile_mgr.update_user(
            self.ctx.student_id,
            nickname=self.edit_nickname.text().strip(),
            grade=self.edit_grade.currentText(),
            target=self.edit_target.currentText(),
        )
        self._editing = False
        self._edit_widget.hide()
        self.btn_edit.setText("编辑资料")
        self.refresh()

    def _save_goal(self):
        self._goal_engine.set_goal(
            self.ctx.student_id, "数学",
            target_score=self.goal_score.value(),
            current_score=self.current_score.value(),
        )
        self._update_goal_gap()
