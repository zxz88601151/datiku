# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""SmartStudy OS 统一设计系统（Phase 3.0）。

所有视图共享的颜色、排版、间距、组件样式。集中管理，避免各视图硬编码。
引擎与数据库零修改。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout

# ═══════════════════════════════════════════════════════════════════
# 颜色系统
# ═══════════════════════════════════════════════════════════════════
COLOR = {
    "primary": "#1f6feb",
    "primary_hover": "#1857c4",
    "primary_light": "#ddf4ff",
    "success": "#1a7f37",
    "success_light": "#dafbe1",
    "warning": "#d4a72c",
    "warning_light": "#fff8c5",
    "danger": "#cf222e",
    "danger_light": "#ffeef0",
    "bg_page": "#f0f2f5",
    "bg_card": "#ffffff",
    "bg_subtle": "#f6f8fa",
    "bg_nav": "#f3f5f9",
    "text_primary": "#24292f",
    "text_secondary": "#656d76",
    "text_muted": "#afb8c1",
    "text_inverse": "#ffffff",
    "border": "#e1e4e8",
    "border_light": "#d0d7de",
    "progress_bg": "#eaeef2",
    "nav_hover": "#e1e7f0",
}

# ═══════════════════════════════════════════════════════════════════
# 样式工具函数
# ═══════════════════════════════════════════════════════════════════

def card_style() -> str:
    return f"""
        QFrame#card {{
            background: {COLOR["bg_card"]};
            border: 1px solid {COLOR["border"]};
            border-radius: 12px;
        }}
    """

def card_css(border_radius: int = 12, border_color: str = None) -> str:
    bc = border_color or COLOR["border"]
    return f"background:{COLOR['bg_card']};border:1px solid {bc};border-radius:{border_radius}px;"

def shadow_style() -> str:
    """卡片阴影（QFrame 不支持 box-shadow, 通过 border 模拟层次感）"""
    return f"border:1px solid {COLOR['border']};border-bottom:2px solid #d0d7de;"

def progress_bar_css(color: str = None) -> str:
    c = color or COLOR["primary"]
    return f"""
        QProgressBar {{ background:{COLOR["progress_bg"]}; border:none;
                       border-radius:4px; }}
        QProgressBar::chunk {{ background:{c}; border-radius:4px; }}
    """

def btn_primary_css() -> str:
    return f"""
        QPushButton {{ background:{COLOR["primary"]}; color:{COLOR["text_inverse"]};
                       font-size:14px; font-weight:600; border:none;
                       border-radius:8px; padding:10px 24px; }}
        QPushButton:hover {{ background:{COLOR["primary_hover"]}; }}
    """

def btn_secondary_css() -> str:
    return f"""
        QPushButton {{ background:{COLOR["bg_subtle"]}; color:{COLOR["text_primary"]};
                       font-size:13px; border:1px solid {COLOR["border_light"]};
                       border-radius:6px; padding:6px 14px; }}
        QPushButton:hover {{ background:{COLOR["nav_hover"]}; }}
    """

def btn_small_css() -> str:
    return f"""
        QPushButton {{ background:{COLOR["bg_subtle"]}; color:{COLOR["text_primary"]};
                       font-size:11px; border:1px solid {COLOR["border_light"]};
                       border-radius:4px; padding:4px 10px; }}
        QPushButton:hover {{ background:{COLOR["nav_hover"]}; }}
    """

def mastery_color(mastery: float) -> str:
    if mastery is None:
        return COLOR["text_muted"]
    if mastery >= 0.7:
        return COLOR["success"]
    if mastery >= 0.4:
        return COLOR["warning"]
    return COLOR["danger"]

# ═══════════════════════════════════════════════════════════════════
# 共享组件类
# ═══════════════════════════════════════════════════════════════════

class Card(QFrame):
    """统一卡片容器。"""

    def __init__(self, title: str = "", border_color: str = None, padding: int = 16):
        super().__init__()
        self.setObjectName("card")
        self.setStyleSheet(f"""
            #card {{ background:{COLOR["bg_card"]}; border:1px solid {border_color or COLOR["border"]};
                     border-radius:12px; }}
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(padding, padding * 0.75, padding, padding * 0.75)
        self.layout.setSpacing(8)
        if title:
            lbl = QLabel(title)
            lbl.setStyleSheet(f"font-size:14px; font-weight:600; color:{COLOR['text_primary']};")
            self.layout.addWidget(lbl)


class SectionTitle(QLabel):
    """段落标题。"""

    def __init__(self, text: str, size: int = 18):
        super().__init__(text)
        self.setStyleSheet(f"font-size:{size}px; font-weight:700; color:{COLOR['text_primary']};")


class BodyText(QLabel):
    """正文文字。"""

    def __init__(self, text: str = "", color: str = None, size: int = 13):
        super().__init__(text)
        self.setWordWrap(True)
        self.setStyleSheet(f"font-size:{size}px; color:{color or COLOR['text_secondary']};")


class MasteryBar(QProgressBar):
    """掌握度进度条。"""

    def __init__(self, value: float = 0.0, height: int = 6):
        super().__init__()
        self.setFixedHeight(height)
        self.setTextVisible(False)
        self.setValue(int(value * 100))
        self.update_color(value)

    def set_mastery(self, value: float):
        self.setValue(int(value * 100))
        self.update_color(value)

    def update_color(self, value: float):
        c = mastery_color(value)
        self.setStyleSheet(progress_bar_css(c))


class PrimaryButton(QPushButton):
    """主要操作按钮。"""

    def __init__(self, text: str, callback=None):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(btn_primary_css())
        if callback:
            self.clicked.connect(callback)


class SecondaryButton(QPushButton):
    """次要操作按钮。"""

    def __init__(self, text: str, callback=None, small: bool = False):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(btn_small_css() if small else btn_secondary_css())
        if callback:
            self.clicked.connect(callback)


class Badge(QLabel):
    """徽章标签。"""

    def __init__(self, text: str, color: str = COLOR["primary"], bg: str = None):
        super().__init__(text)
        bg = bg or f"{color}18"
        self.setStyleSheet(f"""
            background:{bg}; color:{color}; font-size:11px; font-weight:600;
            border-radius:6px; padding:2px 8px;
        """)
