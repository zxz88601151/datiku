# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""错题本视图 —— 错误归因与强化。

列出当前学生的错题（来自 learn_wrong），显示题目、错误原因、错次；
支持「标记掌握」将 resolved 置 1。
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton,
    QHBoxLayout, QMessageBox,
)

from .app_context import AppContext
from . import design as ds


class WrongBookView(QWidget):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)
        root.addWidget(QLabel("我的错题本"))
        self.list = QListWidget()
        root.addWidget(self.list, 1)
        bar = QHBoxLayout()
        bar.addStretch(1)
        resolve = QPushButton("标记选中题为已掌握")
        resolve.clicked.connect(self._resolve)
        bar.addWidget(resolve)
        root.addLayout(bar)

    def refresh(self):
        self.list.clear()
        rows = self.ctx.dm.query(
            """SELECT w.id, w.question_id, w.wrong_reason, w.count, q.content
               FROM learn_wrong w JOIN q_question q ON q.id = w.question_id
               WHERE w.student_id = ? AND w.resolved = 0
               ORDER BY w.count DESC""",
            (self.ctx.student_id,),
        )
        if not rows:
            self.list.addItem("🎉 当前没有未掌握的错题！")
            return
        for r in rows:
            item = QListWidgetItem(f"[错 {r['count']} 次] {r['content'][:60]}\n   归因：{r['wrong_reason']}")
            item.setData(1, r["id"])
            self.list.addItem(item)

    def _resolve(self):
        item = self.list.currentItem()
        if not item:
            return
        wid = item.data(1)
        if wid is None:
            return
        self.ctx.dm.execute("UPDATE learn_wrong SET resolved=1 WHERE id=?", (wid,))
        QMessageBox.information(self, "已掌握", "已标记为掌握，继续加油！")
        self.refresh()
