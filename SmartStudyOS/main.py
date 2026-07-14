# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""SmartStudy OS 启动入口。

职责：
1. 初始化数据层并导入种子（若为空）。
2. 构建 AppContext（连接四个引擎 + 演示学生）。
3. 启动 PySide6 主窗口。

运行：在项目根目录执行 `python main.py`（需先 pip install PySide6）。
"""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("未检测到 PySide6，请先安装：pip install PySide6")
        return 1

    from database.manager import DataManager
    from seed_data import seed_if_empty, import_yancheng_data
    from ui.app_context import AppContext
    from ui.main_window import MainWindow

    dm = DataManager()
    if seed_if_empty(dm):
        print("已导入基础种子数据")
        # 首次启动时一并导入盐城全科数据
        stats = import_yancheng_data(dm)
        print(f"已导入盐城数据: {stats['knowledge']} 知识节点 + {stats['questions']} 题目")
    ctx = AppContext(student_id=1)

    app = QApplication(sys.argv)
    win = MainWindow(ctx)
    win.show()
    code = app.exec()
    ctx.close()
    return code


if __name__ == "__main__":
    sys.exit(main())
