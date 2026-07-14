# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""题库批量导入工具包。

流程：解析(Excel/JSON) → 自动知识点绑定 → 数据质量校验 → 重复检测 → 入库。
设计原则：
- 不人工录入，批量导入前必须校验，避免污染 SQLite。
- 自动知识点绑定保证题目与知识图谱节点关联，否则 AI 推荐无法工作。
- 复用 core 层引擎（KnowledgeGraph / QuestionBank），不绕开数据底座。
"""

from .importer import QuestionImporter, ImportReport, run_cli
from .excel_parser import parse_excel
from .json_parser import parse_json
from .validator import validate_row, ALLOWED_TYPES
from .duplicate_check import DuplicateChecker, norm_key

__all__ = [
    "QuestionImporter", "ImportReport", "run_cli",
    "parse_excel", "parse_json", "validate_row", "ALLOWED_TYPES",
    "DuplicateChecker", "norm_key",
]
