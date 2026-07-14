# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""30 天学习趋势小部件 —— QPainter 折线图。

渲染来自 learning_snapshot 的掌握度时序数据：
- X 轴：日期（最近 N 天，自动适配）
- Y 轴：掌握度 0–100%
- 折线 + 面积渐变填充
- 首末标注数据点
"""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class TrendChart(QWidget):
    """掌握度趋势折线图。"""

    def __init__(self):
        super().__init__()
        self._data: List[dict] = []       # [{"date":..., "overall_mastery":...}]
        self.setMinimumHeight(140)
        self.setMaximumHeight(200)

    def set_data(self, data: List[dict]):
        self._data = data
        self.update()

    def paintEvent(self, event):
        if not self._data:
            painter = QPainter(self)
            painter.setPen(QColor("#afb8c1"))
            painter.setFont(QFont("Microsoft YaHei", 11))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "暂无趋势数据")
            painter.end()
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        pad = {"left": 32, "right": 12, "top": 12, "bottom": 28}
        pw = w - pad["left"] - pad["right"]
        ph = h - pad["top"] - pad["bottom"]

        if pw < 20 or ph < 20:
            painter.end()
            return

        values = [d.get("overall_mastery", 0.0) or 0.0 for d in self._data]
        n = len(values)
        if n < 2:
            painter.end()
            return

        vmin = 0.0
        vmax = max(values + [0.1])
        vmax = max(vmax, 0.3)  # 至少显示到 30%
        vrange = vmax - vmin or 0.1

        def _x(i: int) -> float:
            return pad["left"] + (i / (n - 1)) * pw

        def _y(v: float) -> float:
            return pad["top"] + ph - ((v - vmin) / vrange) * ph

        # ---- 网格线 ----
        painter.setPen(QPen(QColor("#eaeef2"), 1))
        for pct in (0.25, 0.50, 0.75):
            yy = _y(pct * vmax)
            painter.drawLine(int(pad["left"]), int(yy), int(w - pad["right"]), int(yy))
            painter.setPen(QColor("#afb8c1"))
            painter.setFont(QFont("Microsoft YaHei", 8))
            painter.drawText(int(0), int(yy - 6), int(pad["left"] - 4), 12,
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                             f"{pct * 100:.0f}%")

        # ---- 面积填充 ----
        path = QPainterPath()
        path.moveTo(_x(0), _y(values[0]))
        for i in range(1, n):
            path.lineTo(_x(i), _y(values[i]))
        path.lineTo(_x(n - 1), _y(0))
        path.lineTo(_x(0), _y(0))
        path.closeSubpath()

        grad = QLinearGradient(0, _y(vmax), 0, h - pad["bottom"])
        grad.setColorAt(0.0, QColor("#1f6feb").lighter(150))
        grad.setColorAt(1.0, QColor("#ffffff"))
        painter.fillPath(path, QBrush(grad))

        # ---- 折线 ----
        painter.setPen(QPen(QColor("#1f6feb"), 2))
        line_path = QPainterPath()
        line_path.moveTo(_x(0), _y(values[0]))
        for i in range(1, n):
            line_path.lineTo(_x(i), _y(values[i]))
        painter.drawPath(line_path)

        # ---- 数据点 ----
        painter.setBrush(QBrush(QColor("#1f6feb")))
        for i in (0, n - 1):
            painter.drawEllipse(int(_x(i)) - 3, int(_y(values[i])) - 3, 6, 6)

        # ---- X 轴标签（首尾日期） ----
        painter.setPen(QColor("#656d76"))
        painter.setFont(QFont("Microsoft YaHei", 8))
        first_date = self._data[0].get("date", "")
        last_date = self._data[-1].get("date", "")
        painter.drawText(int(_x(0)) - 20, h - 22, 40, 16,
                         Qt.AlignmentFlag.AlignCenter, first_date[-5:])
        painter.drawText(int(_x(n - 1)) - 20, h - 22, 40, 16,
                         Qt.AlignmentFlag.AlignCenter, last_date[-5:])

        # ---- 当前值标注 ----
        last_v = values[-1]
        painter.setPen(QPen(QColor("#1f6feb"), 1))
        lbl = f"{last_v * 100:.0f}%"
        painter.setFont(QFont("Microsoft YaHei", 9, QFont.Weight.Bold))
        painter.drawText(int(_x(n - 1)) - 12, int(_y(last_v)) - 14, 28, 14,
                         Qt.AlignmentFlag.AlignCenter, lbl)

        painter.end()


class TrendChartCard(QWidget):
    """趋势卡片（标题 + 图表组合）。"""

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        lbl = QLabel("学习趋势")
        lbl.setStyleSheet("font-size:13px; font-weight:600; color:#24292f;")
        root.addWidget(lbl)

        self.chart = TrendChart()
        root.addWidget(self.chart, 1)

    def set_data(self, data: List[dict]):
        self.chart.set_data(data)
