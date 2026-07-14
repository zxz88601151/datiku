# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""SmartStudy OS Dashboard（Phase 2.2 学习驾驶舱）。

升级首页，整合四大核心组件：
① 学科能力卡（子领域掌握度分解）
② 知识地图（QGraphicsView 树形可视化）
③ 学习趋势（30 天掌握度折线图）
④ AI 建议卡（规则化，不依赖大模型）

全部数据来自真实数据库（learn_state / learning_snapshot / learn_wrong）。
"""

from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from .app_context import AppContext
from .knowledge_map_widget import KnowledgeMapWidget
from .trend_chart_widget import TrendChartCard
from . import design as ds
from core.learning_snapshot import LearningSnapshot, SuggestionEngine

# 子领域关键词分组（映射知识点名称到能力分类）
_CATEGORIES: Dict[str, List[str]] = {
    "代数": ["有理数", "整式", "方程", "不等式", "实数", "因式分解",
            "因式", "分式", "二次根", "根式", "幂", "指数", "对数",
            "数列", "代数式"],
    "函数": ["函数", "一次函数", "二次函数", "反比例", "正比例",
            "增减性", "图像", "坐标"],
    "几何": ["三角形", "四边形", "圆", "勾股", "相似", "全等",
            "轴对称", "旋转", "平移", "投影", "视图",
            "周长", "面积", "体积", "角", "线", "面"],
    "概率统计": ["概率", "统计", "数据", "频数", "频率", "排列", "组合"],
}


class _Card(QFrame):
    """通用卡片容器。"""

    def __init__(self, title: str = ""):
        super().__init__()
        self.setStyleSheet("""
            _Card { background: #ffffff; border: 1px solid #e1e4e8;
                    border-radius: 12px; }
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 12, 16, 12)
        self.layout.setSpacing(8)
        if title:
            lbl = QLabel(title)
            lbl.setStyleSheet("font-size:13px; font-weight:600; color:#24292f;")
            self.layout.addWidget(lbl)


class _SubjectCard(QFrame):
    """学科能力卡（显示子领域掌握度）。"""

    def __init__(self, subject: str, categories: Dict[str, float]):
        super().__init__()
        self.setStyleSheet(f"""
            _SubjectCard {{ background:{ds.COLOR["bg_card"]};
                           border:1px solid {ds.COLOR["border"]};
                           border-radius:10px; }}
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(4)

        title = ds.BodyText(subject, color=ds.COLOR["text_primary"], size=14)
        title.setStyleSheet(f"font-size:14px; font-weight:700; color:{ds.COLOR['text_primary']};")
        root.addWidget(title)

        for name, mastery in sorted(categories.items(), key=lambda x: -x[1]):
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl = QLabel(name)
            lbl.setStyleSheet(f"font-size:11px; color:{ds.COLOR['text_secondary']}; min-width:48px;")
            row.addWidget(lbl)

            pb = QProgressBar()
            pb.setValue(int(mastery * 100))
            pb.setFixedHeight(5)
            pb.setTextVisible(False)
            pb.setStyleSheet(ds.progress_bar_css(ds.mastery_color(mastery)))
            row.addWidget(pb, 1)

            pct = QLabel(f"{mastery*100:.0f}%")
            pct.setStyleSheet(f"font-size:11px; color:{ds.COLOR['text_secondary']}; min-width:28px;")
            row.addWidget(pct)
            root.addLayout(row)


class _SuggestionCard(QFrame):
    """AI 建议卡（规则化）。"""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            _SuggestionCard { background: #ffffff; border: 1px solid #e1e4e8;
                              border-radius: 10px; }
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 10, 14, 10)
        self._layout.setSpacing(4)

        title = QLabel("💡 学习建议")
        title.setStyleSheet("font-size:13px; font-weight:600; color:#24292f;")
        self._layout.addWidget(title)

        self._container = QVBoxLayout()
        self._container.setSpacing(4)
        self._layout.addLayout(self._container)

    def set_suggestions(self, suggestions: List[dict]):
        self._clear_container()
        if not suggestions:
            empty = QLabel("🎉 暂无建议，继续保持！")
            empty.setStyleSheet("font-size:12px; color:#afb8c1;")
            self._container.addWidget(empty)
            return
        for s in suggestions:
            card = QFrame()
            card.setStyleSheet("""
                QFrame { background: #f6f8fa; border-radius: 6px; padding: 8px; }
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(8, 6, 8, 6)
            cl.setSpacing(2)

            lbl = QLabel(f"{s.get('label', '')}  {s.get('title', '')}")
            lbl.setWordWrap(True)
            lbl.setStyleSheet("font-size:12px; font-weight:600; color:#24292f;")
            cl.addWidget(lbl)

            detail = QLabel(s.get("detail", ""))
            detail.setWordWrap(True)
            detail.setStyleSheet("font-size:11px; color:#656d76;")
            cl.addWidget(detail)

            self._container.addWidget(card)

    def _clear_container(self):
        while self._container.count():
            w = self._container.takeAt(0).widget()
            if w:
                w.deleteLater()


# ===================================================================
#  Dashboard 主视图
# ===================================================================
class Dashboard(QWidget):
    """SmartStudy OS 学习驾驶舱。"""

    def __init__(self, ctx: AppContext, on_start_learning: callable):
        super().__init__()
        self.ctx = ctx
        self._on_start = on_start_learning

        self._snapshot = LearningSnapshot(ctx.dm, ctx.le, ctx.kg)
        self._suggester = SuggestionEngine(ctx.dm, ctx.le, ctx.kg)
        self._build()

    def _build(self):
        # 滚动区域（内容可能超出窗口）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #f0f2f5; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(16)

        # ----- ① 头部：用户信息 + 今日进度 -----
        self._header = QWidget()
        hdr_layout = QHBoxLayout(self._header)
        hdr_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_name = QLabel("👤 小明")
        self.lbl_name.setStyleSheet("font-size:20px; font-weight:700; color:#24292f;")
        hdr_layout.addWidget(self.lbl_name)

        hdr_layout.addSpacing(12)

        self.lbl_level = QLabel()
        self.lbl_level.setStyleSheet("""
            background:#ddf4ff; color:#0969da; font-size:12px; font-weight:600;
            border-radius:8px; padding:2px 10px;
        """)
        hdr_layout.addWidget(self.lbl_level)

        hdr_layout.addStretch(1)

        self.lbl_today = QLabel("今日完成 0%")
        self.lbl_today.setStyleSheet("font-size:14px; color:#656d76;")
        hdr_layout.addWidget(self.lbl_today)

        root.addWidget(self._header)

        # ----- ② 学科能力卡 -----
        self._subject_row = QHBoxLayout()
        self._subject_row.setSpacing(12)
        self._math_card = _SubjectCard("数学", {})
        self._subject_row.addWidget(self._math_card)
        # 预留英语/物理卡（当前仅数学有数据）
        root.addLayout(self._subject_row)

        # ----- ③ 主内容区：知识地图 + 右侧面板 -----
        main_row = QHBoxLayout()
        main_row.setSpacing(12)

        # 知识地图（2/3 宽度）
        map_card = _Card()
        self._knowledge_map = KnowledgeMapWidget(self.ctx.dm, self.ctx.kg)
        map_card.layout.addWidget(self._knowledge_map, 1)
        main_row.addWidget(map_card, 2)

        # 右侧面板（1/3 宽度）
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        # 趋势图
        trend_card = _Card()
        self._trend_chart = TrendChartCard()
        trend_card.layout.addWidget(self._trend_chart, 1)
        right_col.addWidget(trend_card, 1)

        # AI 建议
        self._suggestion_card = _SuggestionCard()
        right_col.addWidget(self._suggestion_card, 2)

        main_row.addLayout(right_col, 1)
        root.addLayout(main_row, 1)

        # ----- ④ 底部：开始学习按钮 -----
        btn = QPushButton("开始学习  →")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { background:#1f6feb; color:#fff; font-size:16px;
                          font-weight:600; border:none; border-radius:10px;
                          padding:14px 0; }
            QPushButton:hover { background:#1857c4; }
        """)
        btn.clicked.connect(self._on_start)
        root.addWidget(btn)

        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ---- 刷新 ---------------------------------------------------
    def refresh(self):
        """从真实数据库刷新全部组件。"""
        sid = self.ctx.student_id

        # 1) 用户信息
        name = "小明"
        try:
            row = self.ctx.dm.query_one("SELECT name FROM user WHERE id=?", (sid,))
            if row and row.get("name"):
                name = row["name"]
        except Exception as e:
            from utils.logger import log
            log.exception("dashboard refresh failed", exc_info=e)
        self.lbl_name.setText(f"👤 {name}")

        # 等级 + XP（来自 Growth Engine）
        from core.growth_engine import XPManager
        xp_mgr = XPManager(self.ctx.dm)
        g = xp_mgr.get_state(sid)
        self.lbl_level.setText(f"Lv.{g['level']}  {g['xp']}/{g['xp_for_next']}XP")

        # 今日快照
        snap = self._snapshot.ensure_latest_snapshot(sid)
        mins = snap.get("study_minutes", 0) or 0
        target = 30  # 每日目标 30 分钟
        today_pct = min(100, int(mins / target * 100))
        self.lbl_today.setText(f"今日完成 {today_pct}%  ·  {mins}/{target} 分钟")

        # 2) 学科能力卡
        self._refresh_subject_cards(sid)

        # 3) 知识地图
        self._knowledge_map.refresh(sid)

        # 4) 趋势
        trend_data = self._snapshot.get_trend(sid, days=30)
        self._trend_chart.set_data(trend_data)

        # 5) 建议
        suggestions = self._suggester.get_suggestions(sid)
        self._suggestion_card.set_suggestions(suggestions)

    def _refresh_subject_cards(self, sid: int):
        """刷新子领域能力分解卡。"""
        rows = self.ctx.dm.query(
            "SELECT ls.knowledge_id, ls.mastery, kn.name "
            "FROM learn_state ls "
            "JOIN kg_node kn ON kn.id = ls.knowledge_id "
            "WHERE ls.student_id=? AND kn.subject='数学'",
            (sid,),
        )
        cat_mastery: Dict[str, list] = {}
        for r in rows:
            name = r.get("name", "") or ""
            m = r.get("mastery", 0.0) or 0.0
            assigned = False
            for cat, keywords in _CATEGORIES.items():
                if any(k in name for k in keywords):
                    cat_mastery.setdefault(cat, []).append(m)
                    assigned = True
                    break
            if not assigned:
                cat_mastery.setdefault("其他", []).append(m)

        # 计算平均掌握度
        result = {}
        for cat, vals in cat_mastery.items():
            result[cat] = sum(vals) / len(vals) if vals else 0.0
        overall = sum(result.values()) / len(result) if result else 0.0

        # 取 Top4 分类展示
        ordered = sorted(result.items(), key=lambda x: -x[1])
        top4 = dict(ordered[:6])

        # 刷新数学卡（当前仅数学有数据）
        new_card = _SubjectCard("数学", top4)
        self._subject_row.replaceWidget(self._math_card, new_card)
        self._math_card.deleteLater()
        self._math_card = new_card

        self._subject_row.update()
        self.update()
