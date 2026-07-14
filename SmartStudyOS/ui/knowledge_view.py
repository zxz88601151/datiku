# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""知识库视图 —— 知识世界浏览器。

左侧知识点树（来自 Knowledge Graph），右侧展示概念/公式/例题/易错点/关联。
搜索框按名称检索。知识点即「世界节点」。
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QTextBrowser, QLineEdit, QPushButton, QSplitter,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from .app_context import AppContext
from . import design as ds


class KnowledgeView(QWidget):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("搜索知识点："))
        self.search = QLineEdit()
        self.search.setPlaceholderText("输入关键词，如：函数 / 绝对值")
        self.search.returnPressed.connect(self._do_search)
        bar.addWidget(self.search, 1)
        btn = QPushButton("搜索")
        btn.clicked.connect(self._do_search)
        bar.addWidget(btn)
        root.addLayout(bar)

        split = QSplitter(Qt.Orientation.Horizontal)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("知识地图")
        self.tree.itemClicked.connect(self._on_select)
        split.addWidget(self.tree)

        self.detail = QTextBrowser()
        split.addWidget(self.detail)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 2)
        root.addWidget(split, 1)

    def refresh(self):
        self.tree.clear()
        for root_node in self.ctx.kg.get_roots():
            self._add_node(self.tree, root_node)

    def _add_node(self, parent, node, parent_item=None):
        item = QTreeWidgetItem([node.name])
        item.setData(0, Qt.ItemDataRole.UserRole, node.id)
        if parent_item is None:
            parent.addTopLevelItem(item)
        else:
            parent_item.addChild(item)
        for child in self.ctx.kg.get_children(node.id):
            self._add_node(parent, child, item)

    def _on_select(self, item, _col):
        nid = item.data(0, Qt.ItemDataRole.UserRole)
        node = self.ctx.kg.get(nid)
        if not node:
            return
        html = [f"<h3>{node.name}</h3><p style='color:#666'>{node.grade} · {node.subject} · 难度 {node.difficulty}/5</p>"]
        if node.content:
            html.append(f"<p><b>概念：</b>{node.content}</p>")
        if node.formula:
            html.append(f"<p><b>公式：</b>{node.formula}</p>")
        if node.examples:
            html.append(f"<p><b>例题：</b>{node.examples}</p>")
        if node.pitfalls:
            html.append(f"<p style='color:#c0392b'><b>易错点：</b>{node.pitfalls}</p>")
        related = self.ctx.kg.get_related(node.id)
        if related:
            html.append("<p><b>关联知识：</b>" + "、".join(n.name for n in related) + "</p>")
        self.detail.setHtml("".join(html))

    def _do_search(self):
        kw = self.search.text().strip()
        if not kw:
            self.refresh()
            return
        hits = self.ctx.kg.search(kw)
        self.tree.clear()
        if not hits:
            item = QTreeWidgetItem([f"未找到「{kw}」"])
            self.tree.addTopLevelItem(item)
            return
        for node in hits:
            item = QTreeWidgetItem([node.name])
            item.setData(0, Qt.ItemDataRole.UserRole, node.id)
            item.setToolTip(0, f"{node.grade} · {node.subject}")
            self.tree.addTopLevelItem(item)
