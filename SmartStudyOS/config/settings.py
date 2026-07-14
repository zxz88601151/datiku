# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""SmartStudy OS —— 全局配置。

设计原则（来自冻结版架构 v1.0）：
- 地区/教材体系不写死出版社，采用 地区 → 教材版本 → 学科 → 章节 → 知识点 的可扩展层级。
- 所有密钥（AI API Key 等）只允许从环境变量/外部配置文件读取，禁止硬编码。
- 引擎层（core/*）仅依赖标准库，保证可无头运行、可单元测试。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "SmartStudy OS"
APP_VERSION = "1.0.0"
APP_SUBTITLE = "智慧学习知识库系统 · 江苏盐城教材体系"

# 项目根目录：支持开发模式（源码）和 PyInstaller 冻结模式
if getattr(sys, "frozen", False):
    _base = Path(sys._MEIPASS)
else:
    _base = Path(__file__).resolve().parent.parent
PROJECT_ROOT = _base

# 数据目录：编译模式下使用用户 AppData 确保可写
if getattr(sys, "frozen", False):
    DATA_DIR = Path(os.environ.get("APPDATA", "~")) / APP_NAME / "data"
else:
    DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 单一 SQLite 文件（逻辑上按 user_/kg_/q_/learn_ 表前缀区分域）。
DB_PATH = DATA_DIR / "smartstudy.db"

# ---------------------------------------------------------------------------
# 地区 / 教材体系（可扩展：后续南京/苏州/上海只需追加记录）
# ---------------------------------------------------------------------------
REGION = {
    "province": "江苏",
    "city": "盐城",
}

# 学段 → 学科映射
SUBJECTS = {
    "小学": ["语文", "数学", "英语", "科学"],
    "初中": ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"],
    "高中": ["语文", "数学", "英语", "物理", "化学", "生物"],
}

# 12 个年级（小学 6 + 初中 3 + 高中 3）
GRADES = [
    "一年级", "二年级", "三年级", "四年级", "五年级", "六年级",
    "七年级", "八年级", "九年级",
    "高一", "高二", "高三",
]
# 年级 → 学段序号（1..12），供排序与升学路径使用
GRADE_LEVEL = {g: i + 1 for i, g in enumerate(GRADES)}

# 题型
QUESTION_TYPES = ["选择题", "填空题", "计算题", "证明题", "实验题", "作文题"]

# 错题归因分类（粗粒度，向后兼容）
WRONG_REASONS = ["概念错误", "计算错误", "审题错误", "方法错误", "其他"]

# 错因标签标准集（Phase 1.5-D 强化）：用于题目预标注 + 学生作答错因归因。
# 由命题/教研经验归纳，覆盖初中数学高频失分维度，供 AI 老师与错因画像使用。
ERROR_TAGS = [
    "概念混淆",       # 相近概念分辨不清（如平方根/算术平方根）
    "公式误用",       # 套错公式或记错形式
    "计算失误",       # 四则运算、符号算术错
    "符号错误",       # 正负号、去括号变号错
    "审题不清",       # 未读全条件/误解问法
    "单位遗漏",       # 漏写或换算错单位
    "分类讨论遗漏",   # 漏掉 k=0、零长度等边界情况
    "隐含条件忽视",   # 忽略分母≠0、根号内≥0、实际意义约束
    "图形理解偏差",   # 读图/作图错误，位置关系判断错
    "移项不变号",     # 等式/不等式移项未变号
    "去分母漏乘",     # 去分母时常数项漏乘
    "忽略分母不为0",  # 分式/反比例函数定义域
    "混淆增减性",     # 函数 k 符号与增减性
    "定理记反",       # 圆周角/切线/相似定理方向错
    "模型列错",       # 实际应用等量关系列错
    "坐标系误用",     # 象限/对称点/距离算错
    "漏乘分配律",     # 乘法分配律漏乘
    "约分遗漏",       # 分式未约到最简
    "未乘倒数",       # 除以分数未转乘倒数
    "小数点位数错",   # 小数乘除点错小数点
]

# ---------------------------------------------------------------------------
# AI 配置（敏感信息：仅从环境变量读取，提供空模板）
# ---------------------------------------------------------------------------
AI_CONFIG = {
    "provider": os.getenv("SMARTSTUDY_AI_PROVIDER", "local"),  # "local" | "api"
    "api_base": os.getenv("SMARTSTUDY_AI_BASE", ""),
    "api_key_env": "SMARTSTUDY_AI_API_KEY",  # 仅存环境变量名，绝不存真实密钥
    "model": os.getenv("SMARTSTUDY_AI_MODEL", "local-template"),
    "temperature": 0.7,
}

# 遗忘曲线时间常数（天）。值越小遗忘越快，可后续按学科差异化
FORGET_TAU_DAYS = 2.0

# 推荐分权重（必须与冻结版架构公式一致）
RECOMMEND_WEIGHTS = {
    "weak": 0.40,      # 薄弱程度
    "forget": 0.30,    # 遗忘程度
    "importance": 0.20,  # 重要程度
    "explore": 0.10,   # 随机探索
}


def get_ai_api_key() -> str:
    """从环境变量安全读取 AI Key，缺失返回空串（本地模式不需要）。"""
    return os.getenv(AI_CONFIG["api_key_env"], "")
