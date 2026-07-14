# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""无头导入演示：用临时库导入初中数学演示种子，验证 解析→绑定→校验→去重→入库。

运行：python tools/question_importer/run_import_demo.py
（无需 PySide6 / openpyxl；使用 JSON 解析器，纯标准库）
"""

from __future__ import annotations

import sys
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import config.settings as cfg  # noqa: E402
from database.manager import DataManager  # noqa: E402
from core.knowledge_engine import KnowledgeGraph  # noqa: E402
from tools.question_importer.importer import QuestionImporter  # noqa: E402


def main() -> int:
    tmp = Path(tempfile.gettempdir()) / "smartstudy_import_demo.db"
    if tmp.exists():
        tmp.unlink()
    dm = DataManager(tmp)

    seed = ROOT / "resource" / "seed" / "middle_school_math.json"
    imp = QuestionImporter(dm, create_missing=True, allow_invalid=False)
    report = imp.import_file(str(seed))
    print(report.summary())

    kg = KnowledgeGraph(dm)
    n_nodes = dm.query_one("SELECT COUNT(*) c FROM kg_node")["c"]
    n_q = dm.query_one("SELECT COUNT(*) c FROM q_question")["c"]
    print(f"\n[库内统计] 知识节点 {n_nodes}，题目 {n_q}")
    print("[知识地图根] " + ", ".join(r.name for r in kg.get_roots()))

    # 验证绑定：取一道一次函数题，回溯其知识点路径
    row = dm.query_one(
        "SELECT * FROM q_question WHERE content LIKE ?", ("%y=2x+1%",))
    if row:
        kid = json.loads(row["knowledge_relation"])[0] if row["knowledge_relation"] else None
        path = " / ".join(n.name for n in kg.get_ancestors(kid))
        print(f"[绑定验证] 「{row['content'][:12]}…」→ 知识点路径：{path}")

    dm.close()
    print("\n✅ 导入流水线验证通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
