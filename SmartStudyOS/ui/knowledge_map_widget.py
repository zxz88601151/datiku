# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""知识地图小部件 —— QGraphicsView 树形可视化。

从一个种子节点（或根节点）开始，展示其子层级的知识点掌握度状态：
- 掌握 (≥0.7) → 绿色
- 学习中 (≥0.4) → 橙色
- 薄弱 (<0.4) → 红色
- 未学习 (None) → 灰色

支持单步下钻（点击节点展开子节点）和缩放（Ctrl+滚轮）。
"""

from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPen
from PySide6.QtWidgets import (
    QFrame, QGraphicsEllipseItem, QGraphicsItem, QGraphicsLineItem,
    QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView, QHBoxLayout,
    QLabel, QPushButton, QVBoxLayout, QWidget,
)

from core.knowledge_engine import KnowledgeGraph
from database.manager import DataManager

_NODE_RADIUS = 28
_LEVEL_GAP = 80
_SIBLING_GAP = 30


class _NodeItem(QGraphicsEllipseItem):
    """代表知识点的一个圆形节点。"""

    def __init__(self, x: float, y: float, name: str, node_id: int,
                 mastery: Optional[float], parent_item: Optional["_NodeItem"]):
        super().__init__(QRectF(x - _NODE_RADIUS, y - _NODE_RADIUS,
                                _NODE_RADIUS * 2, _NODE_RADIUS * 2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.node_id = node_id
        self.mastery = mastery
        self.parent_item = parent_item
        self.child_items: List[_NodeItem] = []
        self.expanded = False
        self._cx = x  # 圆心 X（供连线计算使用）
        self._cy = y  # 圆心 Y

        # 颜色
        m = mastery if mastery is not None else -1
        if m >= 0.7:
            color = "#1a7f37"  # 绿
        elif m >= 0.4:
            color = "#d4a72c"  # 橙
        elif m >= 0:
            color = "#cf222e"  # 红
        else:
            color = "#afb8c1"  # 灰（无数据）

        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(QColor("#ffffff"), 2))

        # 标签
        label = name if len(name) <= 8 else name[:7] + "…"
        self._text = QGraphicsSimpleTextItem(label, self)
        self._text.setFont(QFont("Microsoft YaHei", 8, QFont.Weight.Bold))
        self._text.setBrush(QBrush(QColor("#ffffff")))
        self._text.setPos(x - self._text.boundingRect().width() / 2,
                          y - self._text.boundingRect().height() / 2)

    def set_child_mastery_color(self):
        """根据子节点掌握度更新自身环状渐变色（整体健康度指示）。"""
        if not self.child_items:
            return
        avg = sum(c.mastery or 0.0 for c in self.child_items) / len(self.child_items)
        if avg >= 0.7:
            c = "#1a7f37"
        elif avg >= 0.4:
            c = "#d4a72c"
        else:
            c = "#cf222e"
        self.setBrush(QBrush(QColor(c)))


class KnowledgeMapWidget(QWidget):
    """知识地图主控件。"""

    node_clicked = Signal(int, str)  # node_id, node_name

    def __init__(self, dm: DataManager, kg: KnowledgeGraph):
        super().__init__()
        self.dm = dm
        self.kg = kg
        self._mastery_cache: Dict[int, float] = {}
        self._current_root_id: Optional[int] = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        # 顶栏
        top = QHBoxLayout()
        self.lbl_title = QLabel("知识地图")
        self.lbl_title.setStyleSheet("font-size:14px; font-weight:600; color:#24292f;")
        top.addWidget(self.lbl_title)
        top.addStretch(1)
        self.btn_back = QPushButton("← 返回")
        self.btn_back.setFixedWidth(60)
        self.btn_back.setStyleSheet("""
            QPushButton { background:#f3f5f9; border:1px solid #d0d7de;
                          border-radius:4px; padding:2px 8px; font-size:11px; }
            QPushButton:hover { background:#e1e7f0; }
        """)
        self.btn_back.clicked.connect(self._go_up)
        self.btn_back.hide()
        top.addWidget(self.btn_back)
        root.addLayout(top)

        # 图例
        legend = QHBoxLayout()
        legend.setSpacing(12)
        for label, color in [("掌握", "#1a7f37"), ("学习中", "#d4a72c"),
                              ("薄弱", "#cf222e"), ("未学习", "#afb8c1")]:
            w = QFrame()
            w.setFixedSize(10, 10)
            w.setStyleSheet(f"background:{color}; border-radius:5px;")
            legend.addWidget(w)
            legend.addWidget(QLabel(label))
        legend.addStretch(1)
        root.addLayout(legend)

        # 视图
        self._scene = QGraphicsScene(self)
        self._view = QGraphicsView(self._scene)
        self._view.setRenderHint(self._view.renderHints().Antialiasing)
        self._view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._view.setStyleSheet("background:#f9fafb; border:1px solid #e1e4e8; border-radius:8px;")
        self._view.wheelEvent = self._custom_wheel
        self._view.mousePressEvent = self._custom_click
        root.addWidget(self._view, 1)

    def _custom_wheel(self, event):
        """Ctrl+滚轮缩放，普通滚轮滚动。"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 0.85
            self._view.scale(factor, factor)
        else:
            QGraphicsView.wheelEvent(self._view, event)

    def _custom_click(self, event):
        """点击节点展开其子层级。"""
        QGraphicsView.mousePressEvent(self._view, event)
        if event.button() == Qt.MouseButton.LeftButton:
            items = self._view.items(event.position().toPoint())
            for item in items:
                if isinstance(item, _NodeItem):
                    self._drill_down(item.node_id)
                    break

    # ---- 公共接口 ----
    def refresh(self, student_id: int):
        """基于学生掌握度刷新地图。"""
        # 加载掌握度缓存
        rows = self.dm.query(
            "SELECT knowledge_id, mastery FROM learn_state WHERE student_id=?",
            (student_id,),
        )
        self._mastery_cache = {r["knowledge_id"]: r.get("mastery", 0.0) for r in rows}
        self._current_root_id = None
        self.btn_back.hide()
        self._render_root()

    def _render_root(self):
        """渲染根层级（数学 → 代数/函数/几何/概率/统计）。"""
        self._scene.clear()
        roots = self.kg.get_roots()
        # 过滤数学科目的根节点
        roots = [r for r in roots if getattr(r, "subject", "") == "数学"]
        if not roots:
            roots = self.dm.query(
                "SELECT id, name FROM kg_node WHERE subject='数学' AND parent_id IS NULL LIMIT 5"
            )
        items = []
        for i, r in enumerate(roots):
            name = r.name
            nid = r.id
            x = 150 + i * 170
            y = 50
            m = self._mastery_cache.get(nid)
            item = _NodeItem(x, y, name, nid, m, None)
            self._scene.addItem(item)
            items.append(item)

        # 渲染种子节点下的一级子节点
        for parent in items:
            children = self.kg.get_children(parent.node_id) or []
            if not children:
                continue
            cx = parent._cx
            cy = parent._cy + _LEVEL_GAP
            total_w = max(1, len(children) - 1) * _SIBLING_GAP
            start_x = cx - total_w / 2
            for j, child in enumerate(children):
                name = child.name
                nid = child.id
                x = start_x + j * _SIBLING_GAP
                y = cy
                m = self._mastery_cache.get(nid)
                child_item = _NodeItem(x, y, name, nid, m, parent)
                self._scene.addItem(child_item)
                # 连线：从父节点底边到子节点顶边
                line = QGraphicsLineItem(
                    parent._cx, parent._cy + _NODE_RADIUS,
                    child_item._cx, child_item._cy - _NODE_RADIUS,
                )
                line.setPen(QPen(QColor("#d0d7de"), 1.5))
                line.setZValue(-1)
                self._scene.addItem(line)
                parent.child_items.append(child_item)

        self._scene.setSceneRect(self._scene.itemsBoundingRect().adjusted(-30, -20, 30, 20))
        self._view.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _drill_down(self, node_id: int):
        """点击节点，向下展开一层子节点。"""
        children = self.kg.get_children(node_id) or []
        if not children:
            return  # 叶节点无子节点可展开

        # 只保留当前布局，在原节点下方增加子节点
        self._current_root_id = node_id
        self.btn_back.show()

        # 重新渲染：清空，以该节点为根
        self._scene.clear()
        kn = self.kg.get(node_id)
        name = kn.name if kn else f"#{node_id}"
        m = self._mastery_cache.get(node_id)

        center_x = 150
        center_y = 40
        root_item = _NodeItem(center_x, center_y, name, node_id, m, None)
        self._scene.addItem(root_item)

        for j, child in enumerate(children):
            name = child.name
            nid = child.id
            x = center_x + (j - len(children) / 2 + 0.5) * _SIBLING_GAP * 2.5
            y = center_y + _LEVEL_GAP
            cm = self._mastery_cache.get(nid)
            child_item = _NodeItem(x, y, name, nid, cm, root_item)
            self._scene.addItem(child_item)
            line = QGraphicsLineItem(
                root_item._cx, root_item._cy + _NODE_RADIUS,
                child_item._cx, child_item._cy - _NODE_RADIUS,
            )
            line.setPen(QPen(QColor("#d0d7de"), 1.5))
            line.setZValue(-1)
            self._scene.addItem(line)
            root_item.child_items.append(child_item)
            root_item.set_child_mastery_color()

        self._scene.setSceneRect(self._scene.itemsBoundingRect().adjusted(-30, -20, 30, 20))
        self._view.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _go_up(self):
        """返回上一级。"""
        self._current_root_id = None
        self.btn_back.hide()
        self._render_root()
