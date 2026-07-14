# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""AI Tutor 工厂 + 学习规划器入口。

根据 config settings 选择 provider：默认 local（模板），可切换 api（远程模型）。
API 模式仅从环境变量读取密钥，绝不出现在代码或配置文件中。
"""

from __future__ import annotations

import config.settings as cfg
from database.manager import DataManager
from .base import AITutor


def build_tutor(dm: DataManager) -> AITutor:
    provider = cfg.AI_CONFIG.get("provider", "local")
    if provider == "api":
        # API 实现在此挂载（需读取环境变量中的密钥）。当前阶段复用本地模板，
        # 后续接入时在此实例化 ApiTutor(dm, base=cfg.AI_CONFIG["api_base"],
        #                                api_key=cfg.get_ai_api_key())。
        from .local import LocalTutor
        return LocalTutor(dm)
    from .local import LocalTutor
    return LocalTutor(dm)
