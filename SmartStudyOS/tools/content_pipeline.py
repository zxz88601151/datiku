# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""内容管线（Phase 1.5-B）：知识树 → 题库，灌入 SQLite。

流程：
1. 加载 resources/knowledge/**/grade*.json（富化知识世界）。
2. 导入 resources/questions/**/grade*.json（题目），create_missing=False
   强制「题目只绑定已声明的知识点」，从源头防止知识图谱污染。

用法：
    python -m tools.content_pipeline --db data/smartstudy.db
    python -m tools.content_pipeline --reset      # 清空后重建（开发用）
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import config.settings as cfg
from database.manager import DataManager
from core.knowledge_engine import KnowledgeGraph
from core.question_engine import QuestionBank

from tools.content.load_knowledge import load_knowledge_dir
from tools.question_importer.importer import QuestionImporter
from tools.question_importer.json_parser import parse_json


def _reset(dm: DataManager) -> None:
    print("⚠️  执行 --reset：清空 kg_node / q_* / learn_* 全部数据")
    for t in ("learn_wrong", "learn_record", "learn_state", "q_option", "q_question", "kg_node"):
        dm.execute(f"DELETE FROM {t}")


def run(db_path=None, reset=False, require_existing_knowledge=True) -> int:
    db_path = Path(db_path) if db_path else cfg.DB_PATH
    dm = DataManager(db_path)
    if reset:
        _reset(dm)

    # 1) 知识树
    n_nodes = load_knowledge_dir(dm, cfg.PROJECT_ROOT / "resource" / "knowledge")
    print(f"[1] 知识节点就绪: {n_nodes}")

    # 2) 题库（强制完整性：只绑定已存在知识点）
    imp = QuestionImporter(dm, create_missing=False, allow_invalid=False)
    q_root = cfg.PROJECT_ROOT / "resource" / "questions"
    total = 0
    if not q_root.exists():
        print(f"[2] 题库目录不存在：{q_root}（请先运行 generator）", file=sys.stderr)
        return 1
    for sub in ("middle_math", "primary_math"):
        d = q_root / sub
        if not d.exists():
            continue
        for p in sorted(d.glob("grade*.json")):
            try:
                report = imp.import_file(str(p))
                total += report.inserted
                print(f"    {p.name}: 入库 {report.inserted} / 跳过(错){report.skipped_invalid} / 跳过(重){report.skipped_duplicate}")
            except Exception as e:
                print(f"    {p.name} 导入失败: {e}", file=sys.stderr)
    print(f"[2] 题目总数: {total}")
    print("✅ 内容管线完成")
    return 0


def run_fast(db_path=None, reset=False) -> int:
    """规模化快速装载：事务化批量写入，适配万级题库。

    复用 validator 质量闸门与 duplicate_check 去重，但在单个事务内
    完成全部插入（避免逐条 COMMIT 的性能瓶颈），并将题目严格绑定到
    已声明的知识点（create_missing=False 等价语义）。
    """
    from core.knowledge_engine import KnowledgeGraph
    from tools.question_importer.validator import validate_row
    from tools.question_importer.duplicate_check import norm_key, DuplicateChecker

    db_path = Path(db_path) if db_path else cfg.DB_PATH
    dm = DataManager(db_path)
    if reset:
        _reset(dm)

    # 1) 知识树
    n_nodes = load_knowledge_dir(dm, cfg.PROJECT_ROOT / "resource" / "knowledge")
    print(f"[1] 知识节点就绪: {n_nodes}")

    name_to_id = {
        (r["subject"], r["name"]): r["id"]
        for r in dm.query("SELECT id, subject, name FROM kg_node")
    }

    q_root = cfg.PROJECT_ROOT / "resource" / "questions"
    if not q_root.exists():
        print(f"[2] 题库目录不存在：{q_root}（请先运行 generator）", file=sys.stderr)
        return 1

    files = []
    for sub in ("middle_math", "primary_math"):
        d = q_root / sub
        if d.exists():
            files.extend(sorted(d.glob("grade*.json")))

    items = []
    for p in files:
        data = json.loads(p.read_text(encoding="utf-8"))
        items.extend(data.get("questions", []))

    dup = DuplicateChecker(dm)
    stats = {"inserted": 0, "invalid": 0, "duplicate": 0, "options": 0}
    with dm.transaction():
        for it in items:
            subject = str(it.get("subject", "")).strip()
            grade = str(it.get("grade", "")).strip()
            # 严格绑定：知识点必须已声明
            kids = []
            ok = True
            for kname in (it.get("knowledge") or []):
                kid = name_to_id.get((subject, str(kname).strip()))
                if kid is None:
                    ok = False
                    break
                kids.append(kid)
            if not ok or not kids:
                stats["invalid"] += 1
                continue
            errs, _ = validate_row(it)
            if errs:
                stats["invalid"] += 1
                continue
            key = norm_key(it)
            if dup.is_duplicate(key):
                stats["duplicate"] += 1
                continue
            dup.mark(key)
            # 知识点文本（用于库内知识点感知去重，避免跨子知识点题干雷同被误判重复）
            ktext = "·".join(str(x).strip().lower() for x in (it.get("knowledge") or []))
            qrow = {
                "subject": subject,
                "grade": grade,
                "type": str(it.get("type", "")).strip(),
                "difficulty": int(it.get("difficulty", 3)),
                "content": str(it.get("content", "")).strip(),
                "answer": str(it.get("answer", "")).strip(),
                "analysis": str(it.get("analysis", "") or "").strip(),
                "knowledge_relation": DataManager.dumps(kids),
                "exam_weight": int(it.get("exam_weight", 3) or 3),
                "error_tags": DataManager.dumps(it.get("error_tags") or []),
                "ktext": ktext,
            }
            qid = dm.insert_nc("q_question", qrow)
            stats["inserted"] += 1
            for o in (it.get("options") or []):
                dm.insert_nc("q_option", {
                    "question_id": qid,
                    "label": str(o.get("label", "")),
                    "text": str(o.get("text", "")),
                    "is_correct": 1 if o.get("correct") else 0,
                })
                stats["options"] += 1

    print(f"[2] 快速装载完成: 入库 {stats['inserted']} 题 / 选项 {stats['options']} "
          f"/ 质量拦截 {stats['invalid']} / 去重 {stats['duplicate']}")
    print("✅ 内容管线（快速模式）完成")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="SmartStudy OS 内容管线")
    ap.add_argument("--db", default=None)
    ap.add_argument("--reset", action="store_true", help="清空后重建（开发用）")
    ap.add_argument("--fast", action="store_true", help="事务化快速批量装载（万级题库）")
    args = ap.parse_args()
    if args.fast:
        raise SystemExit(run_fast(db_path=args.db, reset=args.reset))
    raise SystemExit(run(db_path=args.db, reset=args.reset))


if __name__ == "__main__":
    main()
