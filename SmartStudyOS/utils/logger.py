# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""结构化日志（Phase 3.1 稳定性重构）。

替代 print() 调试，提供分级日志输出到文件和控制台。
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)

_LOG_FORMAT = "%(asctime)s [%(levelname)-5s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """获取或创建命名日志器。所有日志器共享文件 Handler。"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)

    # 文件 Handler（全部级别）
    fh = logging.FileHandler(_LOG_DIR / "smartstudy.log", encoding="utf-8", mode="a")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    logger.addHandler(fh)

    # 错误文件 Handler（仅 ERROR+）
    eh = logging.FileHandler(_LOG_DIR / "error.log", encoding="utf-8", mode="a")
    eh.setLevel(logging.ERROR)
    eh.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    logger.addHandler(eh)

    # 控制台 Handler（非 DEBUG 模式）
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S"))
    logger.addHandler(ch)

    return logger


# 全局便捷引用
log = get_logger("smartstudy")
