# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""种子数据加载器（幂等）。

将 resource/seed 下的 JSON 导入数据库。重复运行不会重复插入。
首次启动由 main.py 自动调用，保证 Demo 学生与「初中数学七年级」知识世界就绪。
同时加载盐城1-6年级全科（语文/数学/英语/科学）知识图谱与题库。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import config.settings as cfg
from database.manager import DataManager
from core.knowledge_engine import KnowledgeGraph, KnowledgeNode
from core.question_engine import QuestionBank, Question, Option


def _seed_path(name: str) -> Path:
    return cfg.PROJECT_ROOT / "resource" / "seed" / name


def seed_if_empty(dm: DataManager) -> bool:
    """若知识库为空则导入种子，返回是否执行了导入。"""
    if dm.query_one("SELECT 1 FROM kg_node LIMIT 1"):
        return False

    # 演示学生（未成年用户：含监护人字段，满足合规最小必要）
    if not dm.query_one("SELECT 1 FROM user WHERE id = 1"):
        dm.execute(
            "INSERT INTO user (id, name, grade, school, guardian, created_at) VALUES (?,?,?,?,?,?)",
            (1, "演示学生", "七年级", "盐城某中学", "家长", "2026-01-01T00:00:00"),
        )

    # ---- 知识节点 ----
    kg = KnowledgeGraph(dm)
    kdata = json.loads(_seed_path("knowledge_seed.json").read_text(encoding="utf-8"))
    name_to_id: dict[str, int] = {}
    # 先插入所有节点（parent 暂用 None，二次回填）
    for n in kdata["nodes"]:
        node = KnowledgeNode(
            name=n["name"], subject=kdata["subject"], grade=kdata["grade"],
            parent_id=None, difficulty=n.get("difficulty", 1),
            importance=n.get("importance", 0.5), relation=[],
            content=n.get("content", ""), formula=n.get("formula", ""),
            examples=n.get("examples", ""), pitfalls=n.get("pitfalls", ""),
        )
        nid = kg.add(node)
        name_to_id[n["name"]] = nid
    # 回填父子关系
    for n in kdata["nodes"]:
        if n.get("parent"):
            child = kg.get(name_to_id[n["name"]])
            child.parent_id = name_to_id[n["parent"]]
            kg.update(child)
    # 建立跨链接 relation
    for n in kdata["nodes"]:
        for rel_name in n.get("relation", []):
            if rel_name in name_to_id:
                kg.link(name_to_id[n["name"]], name_to_id[rel_name])

    # ---- 题目 ----
    bank = QuestionBank(dm)
    qdata = json.loads(_seed_path("question_seed.json").read_text(encoding="utf-8"))
    for q in qdata["questions"]:
        kid = name_to_id.get(q["knowledge"])
        question = Question(
            subject=qdata["subject"], grade=qdata["grade"], type=q["type"],
            difficulty=q.get("difficulty", 1), content=q["content"],
            answer=q.get("answer", ""), analysis=q.get("analysis", ""),
            knowledge_relation=[kid] if kid else [],
        )
        opts = [Option(label=o["label"], text=o["text"], is_correct=o.get("correct", False))
                for o in q.get("options", [])]
        bank.add(question, opts)

    return True


# ====================================================================
# 盐城1-6年级全科数据导入（首次启动自动执行）
# ====================================================================

_YANCHENG_SUBJECTS = [
    ("yancheng_math", "数学"),
    ("yancheng_chinese", "语文"),
    ("yancheng_english", "英语"),
    ("yancheng_science", "科学"),
]


def _find_knowledge_node(kg: KnowledgeGraph, subject: str, grade: str, name: str) -> Any:
    """模糊查找知识点节点。"""
    rows = kg.dm.query(
        "SELECT id, name FROM kg_node WHERE subject=? AND grade=? AND name=?",
        (subject, grade, name),
    )
    return rows[0] if rows else None


def _import_yancheng_knowledge(dm: DataManager) -> int:
    """导入盐城知识图谱，返回新增节点数。"""
    kg = KnowledgeGraph(dm)
    total = 0

    for subdir, subject in _YANCHENG_SUBJECTS:
        kdir = cfg.PROJECT_ROOT / "resource" / "knowledge" / subdir
        if not kdir.exists():
            continue

        for gf in sorted(kdir.glob("grade*.json")):
            with open(gf, "r", encoding="utf-8") as f:
                data = json.load(f)
            grade = data["grade"]

            # 创建根节点
            root = _find_knowledge_node(kg, subject, "", subject)
            if root is None:
                kg.add(KnowledgeNode(name=subject, subject=subject, grade="", parent_id=None))
                total += 1

            # 创建年级节点
            gnode = _find_knowledge_node(kg, subject, grade, grade)
            root = _find_knowledge_node(kg, subject, "", subject)
            if gnode is None and root:
                kg.add(KnowledgeNode(name=grade, subject=subject, grade=grade, parent_id=root["id"]))
                total += 1

            # 建立名称索引
            name_index: Dict[str, int] = {}
            chap_index: Dict[str, int] = {}

            # 先找已有的节点
            for nd in data.get("nodes", []):
                name = nd["name"]
                existing = _find_knowledge_node(kg, subject, grade, name)
                if existing:
                    name_index[name] = existing["id"]
                    if nd.get("type") == "chapter":
                        chap_index[name] = existing["id"]

            # 新增缺失节点
            for nd in data.get("nodes", []):
                name = nd["name"]
                if name in name_index:
                    continue

                parent_name = nd.get("parent")
                parent_id = None
                if parent_name:
                    parent_id = chap_index.get(parent_name)

                ntype = nd.get("type", "knowledge")
                important = bool(nd.get("important"))
                imp = 0.85 if important else 0.45
                errors = nd.get("errors") or []
                formula = nd.get("formula", "")

                kn = KnowledgeNode(
                    name=name, subject=subject, grade=grade,
                    parent_id=parent_id,
                    summary=nd.get("summary", ""),
                    node_type=ntype,
                    important=important,
                    importance=imp,
                    formula=formula,
                    errors=errors if isinstance(errors, list) else [errors],
                )
                nid = kg.add(kn)
                name_index[name] = nid
                if ntype == "chapter":
                    chap_index[name] = nid
                total += 1

    return total


def _import_yancheng_questions(dm: DataManager) -> int:
    """导入盐城题库，返回导入题数。"""
    bank = QuestionBank(dm)
    kg = KnowledgeGraph(dm)
    total = 0

    for subdir, subject in _YANCHENG_SUBJECTS:
        qdir = cfg.PROJECT_ROOT / "resource" / "questions" / subdir
        if not qdir.exists():
            continue

        for qf in sorted(qdir.glob("grade*.json")):
            with open(qf, "r", encoding="utf-8") as f:
                data = json.load(f)
            grade = data["grade"]

            for qd in data.get("questions", []):
                qid = qd.get("id", "")
                if qid and dm.query_one("SELECT 1 FROM q_question WHERE id=?", (qid,)):
                    continue

                # 知识点绑定
                klist = qd.get("knowledge", [])
                if isinstance(klist, str):
                    klist = [klist]
                nids: List[int] = []
                for kn in klist:
                    node = _find_knowledge_node(kg, subject, grade, kn)
                    if node:
                        nids.append(node["id"])

                q = Question(
                    subject=subject, grade=grade,
                    type=qd.get("type", "选择题"),
                    difficulty=qd.get("difficulty", 3),
                    content=qd.get("content", ""),
                    answer=qd.get("answer", ""),
                    analysis=qd.get("analysis", ""),
                    knowledge_relation=nids,
                )
                opts = [
                    Option(label=o.get("label", ""), text=o.get("text", ""),
                           is_correct=bool(o.get("correct")))
                    for o in qd.get("options", [])
                ]
                bank.add(q, opts)
                total += 1

    return total


def import_yancheng_data(dm: DataManager) -> Dict[str, int]:
    """导入所有盐城数据，返回统计信息。"""
    result = {"knowledge": 0, "questions": 0}
    result["knowledge"] = _import_yancheng_knowledge(dm)
    result["questions"] = _import_yancheng_questions(dm)
    return result
