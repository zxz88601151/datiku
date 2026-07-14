# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""成长系统（Phase 2.6 RPG Growth Engine）UI。

展示：
- 角色等级卡（等级、XP进度条、称号）
- 技能树（学科→技能等级+进度）
- 成就墙（已解锁/未解锁）
- 每日任务（进度+领取奖励）
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from .app_context import AppContext
from core.growth_engine import (
    XPManager, SkillTreeEngine, AchievementEngine,
    DailyQuestEngine, ACHIEVEMENT_DEFS,
)


class _Card(QFrame):
    def __init__(self, title: str = ""):
        super().__init__()
        self.setStyleSheet("_Card{background:#ffffff;border:1px solid #e1e4e8;border-radius:10px;}")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 12, 16, 12)
        self.layout.setSpacing(8)
        if title:
            lbl = QLabel(title)
            lbl.setStyleSheet("font-size:14px;font-weight:600;color:#24292f;")
            self.layout.addWidget(lbl)


class GrowthView(QWidget):
    """成长系统主视图。"""

    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self._xp = XPManager(ctx.dm)
        self._skills = SkillTreeEngine(ctx.dm, ctx.kg, ctx.le)
        self._ach = AchievementEngine(ctx.dm, ctx.kg, ctx.le)
        self._quests = DailyQuestEngine(ctx.dm, ctx.kg, ctx.le)
        self._build()

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:#f0f2f5;}")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(14)

        title = QLabel("🌱 成长系统")
        title.setStyleSheet("font-size:20px;font-weight:700;color:#24292f;")
        root.addWidget(title)

        # 等级卡
        self._level_card = _Card()
        self._build_level_section()
        root.addWidget(self._level_card)

        # 技能树
        skill_card = _Card("🛡️ 技能树")
        self._skill_area = QVBoxLayout()
        skill_card.layout.addLayout(self._skill_area)
        root.addWidget(skill_card)

        # 成就墙
        ach_card = _Card("🏆 成就墙")
        self._ach_grid = QGridLayout()
        self._ach_grid.setSpacing(8)
        ach_card.layout.addLayout(self._ach_grid)
        root.addWidget(ach_card)

        # 每日任务
        quest_card = _Card("📋 每日任务")
        self._quest_area = QVBoxLayout()
        quest_card.layout.addLayout(self._quest_area)
        root.addWidget(quest_card)

        root.addStretch(1)
        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _build_level_section(self):
        self._level_layout = QHBoxLayout()
        self.lbl_avatar = QLabel("👤")
        self.lbl_avatar.setStyleSheet("font-size:40px;")
        self._level_layout.addWidget(self.lbl_avatar)

        info = QVBoxLayout()
        self.lbl_name_level = QLabel("")
        self.lbl_name_level.setStyleSheet("font-size:18px;font-weight:700;color:#24292f;")
        info.addWidget(self.lbl_name_level)

        self.lbl_title = QLabel("")
        self.lbl_title.setStyleSheet("font-size:12px;color:#656d76;")
        info.addWidget(self.lbl_title)

        self.xp_bar = QProgressBar()
        self.xp_bar.setFixedHeight(8)
        self.xp_bar.setTextVisible(False)
        self.xp_bar.setStyleSheet("""
            QProgressBar{background:#eaeef2;border:none;border-radius:4px;}
            QProgressBar::chunk{background:#1f6feb;border-radius:4px;}
        """)
        info.addWidget(self.xp_bar)

        self.lbl_xp = QLabel("")
        self.lbl_xp.setStyleSheet("font-size:11px;color:#656d76;")
        info.addWidget(self.lbl_xp)
        self._level_layout.addLayout(info, 1)
        self._level_card.layout.addLayout(self._level_layout)

    def refresh(self):
        sid = self.ctx.student_id
        user = self.ctx.dm.query_one("SELECT nickname,name FROM user WHERE id=?", (sid,))
        name = (user.get("nickname") or user.get("name") or "同学") if user else "同学"

        # XP + 等级
        g = self._xp.get_state(sid)
        titles = ["初学者", "见习学者", "探索者", "进阶学者", "知识勇士",
                   "解题专家", "学科达人", "学霸", "学术大师", "传奇学者"]
        title_idx = min(len(titles) - 1, max(0, g["level"] - 1))
        self.lbl_name_level.setText(f"{name}  Lv.{g['level']}")
        self.lbl_title.setText(f"称号：{titles[title_idx]}")
        self.xp_bar.setMaximum(100)
        self.xp_bar.setValue(int(g["progress"] * 100))
        self.lbl_xp.setText(f"XP: {g['xp']} / {g['xp_for_next']}  (累计 {g['total_xp']} XP)")

        # 技能树
        self._refresh_skills(sid)

        # 成就
        self._refresh_achievements(sid)

        # 每日任务
        self._refresh_quests(sid)

    def _refresh_skills(self, sid: int):
        self._clear_area(self._skill_area)
        skills = self._skills.compute(sid)
        for s in skills:
            row = QHBoxLayout()
            row.setSpacing(8)
            lbl = QLabel(s["skill_name"])
            lbl.setStyleSheet("font-size:13px;color:#24292f;min-width:70px;")
            row.addWidget(lbl)

            lvl = QLabel(f"Lv.{s['level']}")
            lvl.setStyleSheet("font-size:12px;font-weight:600;color:#1f6feb;min-width:32px;")
            row.addWidget(lvl)

            pb = QProgressBar()
            pb.setFixedHeight(6)
            pb.setTextVisible(False)
            pb.setValue(int(s["progress"] * 100))
            color = "#1f6feb" if s["level"] < 8 else "#d4a72c" if s["level"] < 12 else "#1a7f37"
            pb.setStyleSheet(f"""
                QProgressBar{{background:#eaeef2;border:none;border-radius:3px;}}
                QProgressBar::chunk{{background:{color};border-radius:3px;}}
            """)
            row.addWidget(pb, 1)

            pct = QLabel(f"{s['mastery']*100:.0f}%")
            pct.setStyleSheet("font-size:11px;color:#656d76;min-width:32px;")
            row.addWidget(pct)
            self._skill_area.addLayout(row)

    def _refresh_achievements(self, sid: int):
        self._clear_grid(self._ach_grid)
        unlocked = {r["achievement_id"] for r in self._ach.get_unlocked(sid)}

        for i, ach in enumerate(ACHIEVEMENT_DEFS):
            is_unlocked = ach["id"] in unlocked
            card = QFrame()
            bg = "#ddf4ff" if is_unlocked else "#f6f8fa"
            border = "#1f6feb" if is_unlocked else "#e1e4e8"
            card.setStyleSheet(f"QFrame{{background:{bg};border:1px solid {border};border-radius:8px;padding:8px;}}")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(8, 6, 8, 6)
            cl.setSpacing(2)

            nm = QLabel(ach["name"])
            nm.setStyleSheet(f"font-size:12px;font-weight:600;color:#24292f;")
            cl.addWidget(nm)

            if is_unlocked:
                st = QLabel("✅ 已解锁")
                st.setStyleSheet("font-size:10px;color:#1a7f37;")
            else:
                st = QLabel(f"🔒 +{ach.get('reward_xp',0)} XP")
                st.setStyleSheet("font-size:10px;color:#afb8c1;")
            cl.addWidget(st)

            col = i % 3
            row = i // 3
            self._ach_grid.addWidget(card, row, col)

    def _refresh_quests(self, sid: int):
        self._clear_area(self._quest_area)
        tasks = self._quests.generate(sid, self._xp)
        for t in tasks:
            card = QFrame()
            card.setStyleSheet("QFrame{background:#f6f8fa;border-radius:8px;padding:8px;}")
            cl = QHBoxLayout(card)
            cl.setContentsMargins(10, 6, 10, 6)

            desc = QLabel(t.get("description", ""))
            desc.setStyleSheet("font-size:13px;color:#24292f;")
            cl.addWidget(desc, 1)

            prog = QLabel(f"{t.get('progress',0)}/{t.get('target',1)}")
            prog.setStyleSheet("font-size:12px;color:#656d76;")
            cl.addWidget(prog)

            pb = QProgressBar()
            pb.setFixedSize(60, 6)
            pb.setTextVisible(False)
            target = t.get("target", 1)
            pb.setValue(int((t.get("progress", 0) / max(1, target)) * 100))
            pb.setStyleSheet("""
                QProgressBar{background:#eaeef2;border:none;border-radius:3px;}
                QProgressBar::chunk{background:#1a7f37;border-radius:3px;}
            """)
            cl.addWidget(pb)

            status = t.get("status", "pending")
            if status == "pending":
                st_lbl = QLabel("进行中")
                st_lbl.setStyleSheet("font-size:11px;color:#d4a72c;")
            elif status == "completed":
                st_lbl = QPushButton("领取 +{} XP".format(t.get("reward_xp", 0)))
                st_lbl.setStyleSheet("""
                    QPushButton{background:#1a7f37;color:#fff;border:none;
                                border-radius:4px;padding:4px 10px;font-size:11px;}
                    QPushButton:hover{background:#14632c;}
                """)
                tid = t["id"]
                st_lbl.clicked.connect(lambda _checked=False, tid=tid: self._claim(sid, tid))
            else:
                st_lbl = QLabel("✅ 已领取")
                st_lbl.setStyleSheet("font-size:11px;color:#1a7f37;")
            cl.addWidget(st_lbl)

            self._quest_area.addWidget(card)

    def _claim(self, sid: int, task_id: int):
        self._quests.claim_reward(sid, task_id, self._xp)
        self.refresh()

    @staticmethod
    def _clear_area(layout):
        while layout.count():
            w = layout.takeAt(0).widget()
            if w:
                w.deleteLater()

    @staticmethod
    def _clear_grid(layout):
        while layout.count():
            w = layout.takeAt(0).widget()
            if w:
                w.deleteLater()
