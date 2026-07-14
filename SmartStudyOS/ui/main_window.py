# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""SmartStudy OS 主窗口（Phase 2.1）。

顶部导航 + QStackedWidget 内容区。
首页已升级为「今日学习中心」，导航保留全部视图，学习流为非导航全屏视图。
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame, QComboBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .app_context import AppContext
from . import design as ds
from .dashboard import Dashboard
from .learning_center import LearningCenter
from .knowledge_view import KnowledgeView
from .exercise_view import ExerciseView
from .wrongbook_view import WrongBookView
from .ai_view import AIView
from .analysis_view import AnalysisView
from .learning_flow import LearningFlow
from .diagnosis_view import DiagnosisView
from .user_center import UserCenterView
from .growth_view import GrowthView

NAV_ITEMS = [
    ("首页", "learning_center"),
    ("知识库", "knowledge"),
    ("刷题", "exercise"),
    ("错题", "wrongbook"),
    ("诊断", "diagnosis"),
    ("成长", "growth"),
    ("用户", "user_center"),
    ("AI老师", "ai"),
    ("数据分析", "analysis"),
]


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle("SmartStudy OS · 智慧学习知识库系统")
        self.resize(1100, 720)
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                                    font-size: 13px; }}
            QScrollBar:vertical {{ background: {ds.COLOR["bg_page"]}; width: 8px; }}
            QScrollBar::handle:vertical {{ background: #c0c8d0; border-radius: 4px;
                                            min-height: 30px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- 顶部标题栏 ----
        title_bar = QFrame()
        title_bar.setObjectName("titleBar")
        title_bar.setStyleSheet(
            "QFrame#titleBar{background:#1f6feb;color:white;}"
        )
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(16, 10, 16, 10)
        title = QLabel("SmartStudy OS")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        sub = QLabel("智慧学习知识库系统 · 江苏盐城教材体系")
        sub.setFont(QFont("Microsoft YaHei", 9))
        sub.setStyleSheet("color:#cfe0ff;")
        tb_layout.addWidget(title)
        tb_layout.addSpacing(12)
        tb_layout.addWidget(sub)
        tb_layout.addStretch(1)

        # 用户切换器
        self.user_switcher = QComboBox()
        self.user_switcher.setStyleSheet("""
            QComboBox { background:rgba(255,255,255,0.15); color:white; border:none;
                        border-radius:4px; padding:4px 10px; font-size:12px; }
            QComboBox::drop-down { border:none; }
            QComboBox:hover { background:rgba(255,255,255,0.25); }
            QComboBox QAbstractItemView { background:#ffffff; color:#24292f;
                                          selection-background:#ddf4ff; }
        """)
        self.user_switcher.currentIndexChanged.connect(self._on_user_switch)
        tb_layout.addWidget(self.user_switcher)

        root.addWidget(title_bar)

        # ---- 导航条 ----
        nav = QFrame()
        nav.setStyleSheet("background:#f3f5f9;")
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(8, 4, 8, 4)
        nav_layout.setSpacing(4)
        self.nav_buttons = {}
        for label, key in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet(self._nav_style(False))
            btn.clicked.connect(lambda _checked, k=key: self._switch(k))
            self.nav_buttons[key] = btn
            nav_layout.addWidget(btn)
        nav_layout.addStretch(1)
        self._nav_bar = nav  # 保存引用，学习流时隐藏
        root.addWidget(nav)

        # ---- 内容区 ----
        self.stack = QStackedWidget()

        # 首页 → 学习驾驶舱（Phase 2.2）
        self._dashboard = Dashboard(ctx, on_start_learning=self._start_learning_flow)
        self.stack.addWidget(self._dashboard)

        # 其他导航视图
        self.views = {}
        self.views["knowledge"] = KnowledgeView(ctx)
        self.views["exercise"] = ExerciseView(ctx)
        self.views["wrongbook"] = WrongBookView(ctx)
        self.views["diagnosis"] = DiagnosisView(ctx, on_start_practice=self._start_recovery_flow)
        self.views["growth"] = GrowthView(ctx)
        self.views["user_center"] = UserCenterView(ctx)
        self.views["ai"] = AIView(ctx)
        self.views["analysis"] = AnalysisView(ctx)
        for v in self.views.values():
            self.stack.addWidget(v)

        # 学习流视图（不在导航栏中，由首页「开始学习」进入）
        self._learning_flow = LearningFlow(ctx, on_go_home=self._go_home,
                                           on_show_diagnosis=self._show_diagnosis)
        self.stack.addWidget(self._learning_flow)

        root.addWidget(self.stack, 1)

        # 种子用户（首次启动自动创建演示账号）
        self._seed_users()
        self._refresh_user_switcher()
        self._switch("learning_center")

    def _seed_users(self):
        """首次启动时播种 100 个演示用户。"""
        from core.user_profile import UserProfileManager
        mgr = UserProfileManager(self.ctx.dm)
        count = mgr.seed_demo_users(100)
        # 确保当前学生存在
        r = self.ctx.dm.query_one("SELECT id FROM user WHERE id=?", (self.ctx.student_id,))
        if not r:
            uid = mgr.create_user("小明", grade="八年级", nickname="小明", target="中考")
            self.ctx.student_id = uid

    def _refresh_user_switcher(self):
        """刷新用户切换下拉框。"""
        self.user_switcher.blockSignals(True)
        self.user_switcher.clear()
        users = self.ctx.dm.query("SELECT id, name, nickname FROM user ORDER BY id")
        for u in users:
            display = u.get("nickname") or u.get("name") or f"用户#{u['id']}"
            self.user_switcher.addItem(f"👤 {display}", u["id"])
        # 选中当前用户
        for i in range(self.user_switcher.count()):
            if self.user_switcher.itemData(i) == self.ctx.student_id:
                self.user_switcher.setCurrentIndex(i)
                break
        self.user_switcher.blockSignals(False)

    def _on_user_switch(self, idx: int):
        """用户切换。"""
        if idx < 0:
            return
        uid = self.user_switcher.itemData(idx)
        if uid and uid != self.ctx.student_id:
            self.ctx.student_id = uid
            # 刷新当前视图
            w = self.stack.currentWidget()
            refresh = getattr(w, "refresh", None)
            if callable(refresh):
                refresh()

    # ---- 导航 ----
    def _switch(self, key: str):
        # 隐藏导航栏（学习流全屏），否则显示
        self._nav_bar.setVisible(key != "learning_flow")
        for k, btn in self.nav_buttons.items():
            on = (k == key)
            btn.setChecked(on)
            btn.setStyleSheet(self._nav_style(on))
        if key == "learning_center":
            self.stack.setCurrentWidget(self._dashboard)
        elif key == "learning_flow":
            self.stack.setCurrentWidget(self._learning_flow)
        else:
            self.stack.setCurrentWidget(self.views[key])
        # 切换时刷新（数据可能已变化）
        w = self.stack.currentWidget()
        refresh = getattr(w, "refresh", None)
        if callable(refresh):
            refresh()

    def _start_learning_flow(self):
        """首页「开始学习 →」回调。"""
        self._switch("learning_flow")
        self._learning_flow.start_session(subject="数学", grade="七年级")

    def _go_home(self):
        """学习流「返回首页」回调。"""
        self._switch("learning_center")

    def _start_recovery_flow(self, knowledge_ids=None, task_id=None):
        """诊断中心「开始强化训练」回调。"""
        self._switch("learning_flow")
        self._learning_flow.start_session(
            subject="数学", grade="七年级",
            knowledge_ids=knowledge_ids,
        )

    def _show_diagnosis(self):
        """学习流奖励页「查看诊断报告」回调。"""
        self._switch("diagnosis")

    @staticmethod
    def _nav_style(active: bool) -> str:
        if active:
            return ("QPushButton{background:#1f6feb;color:white;border:none;"
                    "padding:8px 16px;border-radius:6px;font-weight:bold;}")
        return ("QPushButton{background:transparent;color:#333;border:none;"
                "padding:8px 16px;border-radius:6px;}"
                "QPushButton:hover{background:#e1e7f0;}")
