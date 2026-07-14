#!/usr/bin/env python3
# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""盐城专项数据导入脚本 — 将生成的知识图谱和题目导入 SmartStudy OS 数据库。

用法：
    python tools/yancheng_import.py                # 导入到默认 smartstudy.db
    python tools/yancheng_import.py --db data/smartstudy.db  # 指定数据库
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# 确保项目根在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.manager import DataManager
from core.knowledge_engine import KnowledgeGraph, KnowledgeNode
from core.question_engine import QuestionBank, Question, Option

# 盐城数据路径配置
KNOWLEDGE_DIRS = {
    "数学": PROJECT_ROOT / "resource" / "knowledge" / "yancheng_math",
    "语文": PROJECT_ROOT / "resource" / "knowledge" / "yancheng_chinese",
    "英语": PROJECT_ROOT / "resource" / "knowledge" / "yancheng_english",
    "科学": PROJECT_ROOT / "resource" / "knowledge" / "yancheng_science",
}

QUESTIONS_DIRS = {
    "数学": PROJECT_ROOT / "resource" / "questions" / "yancheng_math",
    "语文": PROJECT_ROOT / "resource" / "questions" / "yancheng_chinese",
    "英语": PROJECT_ROOT / "resource" / "questions" / "yancheng_english",
    "科学": PROJECT_ROOT / "resource" / "questions" / "yancheng_science",
}


def import_knowledge(dm: DataManager, subject: str) -> Tuple[int, int]:
    """导入知识图谱，返回 (导入数, 更新数)。"""
    kg = KnowledgeGraph(dm)
    kg_dir = KNOWLEDGE_DIRS[subject]
    if not kg_dir.exists():
        print(f"  ⚠ 知识图谱目录不存在: {kg_dir}")
        return (0, 0)
    
    imported = 0
    updated = 0
    
    # 按年级顺序处理
    grade_files = sorted(kg_dir.glob("grade*.json"))
    for gf in grade_files:
        with open(gf, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        grade = data["grade"]
        version = data.get("version", "盐城专用")
        
        # 先创建学科根节点（如果不存在）
        subj_root = kg.find(subject, "", subject)
        if subj_root is None:
            subj_root = kg.get(kg.add(KnowledgeNode(
                name=subject, subject=subject, grade="", parent_id=None)))
            imported += 1
        
        # 创建年级节点
        grade_node = kg.find(subject, grade, grade)
        if grade_node is None:
            grade_node = kg.get(kg.add(KnowledgeNode(
                name=grade, subject=subject, grade=grade, parent_id=subj_root.id)))
            imported += 1
        
        # 创建 name -> node_id 的临时索引（第一遍）
        name_to_id: Dict[str, int] = {}
        all_nodes_data = data.get("nodes", [])
        
        # 先处理 chapter 节点（可带 parent 引用）
        tmp_index: Dict[str, int] = {}
        chapter_ids: Dict[str, int] = {}
        
        for node in all_nodes_data:
            name = node["name"]
            ntype = node.get("type", "knowledge")
            parent_name = node.get("parent")
            
            # 找到父节点ID
            parent_id = None
            if parent_name:
                if parent_name in chapter_ids:
                    parent_id = chapter_ids[parent_name]
                else:
                    # 父节点可能是其他 chapter
                    parent_node = kg.find(subject, grade, parent_name)
                    if parent_node:
                        parent_id = parent_node.id
            
            existing = kg.find(subject, grade, name)
            if existing:
                node_id = existing.id
                updated += 1
                # 更新字段
                kg.dm.execute(
                    "UPDATE kg_node SET summary=?, node_type=?, important=? WHERE id=?",
                    (node.get("summary", ""), ntype,
                     bool(node.get("important")), node_id))
            else:
                # 创建新节点
                important = bool(node.get("important"))
                importance = 0.85 if important else 0.45
                formula = node.get("formula", "")
                errors = node.get("errors") or []
                
                kn = KnowledgeNode(
                    name=name, subject=subject, grade=grade,
                    parent_id=parent_id,
                    summary=node.get("summary", ""),
                    node_type=ntype,
                    important=important,
                    importance=importance,
                    formula=formula,
                    errors=errors,
                    content=node.get("summary", ""),
                )
                new_node = kg.get(kg.add(kn))
                node_id = new_node.id
                imported += 1
            
            if ntype == "chapter":
                chapter_ids[name] = node_id
            tmp_index[name] = node_id
        
        # 第二遍：建立章节下知识点与章节的父子关系修正
        for node in all_nodes_data:
            name = node["name"]
            parent_name = node.get("parent")
            if parent_name and parent_name in chapter_ids:
                node_id = tmp_index[name]
                parent_id = chapter_ids[parent_name]
                kg.dm.execute(
                    "UPDATE kg_node SET parent_id=? WHERE id=? AND parent_id IS NULL",
                    (parent_id, node_id))
        
        print(f"  ✓ {subject}/{grade}: {len(all_nodes_data)} 节点 (新增 {imported}, 更新 {updated})")
    
    return (imported, updated)


def import_questions(dm: DataManager, subject: str) -> int:
    """导入题库，返回导入题目数。"""
    bank = QuestionBank(dm)
    kg = KnowledgeGraph(dm)
    q_dir = QUESTIONS_DIRS[subject]
    if not q_dir.exists():
        print(f"  ⚠ 题库目录不存在: {q_dir}")
        return 0
    
    total = 0
    grade_files = sorted(q_dir.glob("grade*.json"))
    
    for qf in grade_files:
        with open(qf, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        grade = data["grade"]
        questions = data.get("questions", [])
        
        for q_data in questions:
            # 跳过已有题目（按id去重）
            q_id = q_data.get("id", "")
            if q_id:
                existing = dm.query_one("SELECT id FROM q_question WHERE id=?", (q_id,))
                if existing:
                    continue
            
            # 解析知识点绑定
            knowledge_list = q_data.get("knowledge", [])
            if isinstance(knowledge_list, str):
                knowledge_list = [knowledge_list]
            
            node_ids = []
            for kn in knowledge_list:
                node = kg.find(subject, grade, kn)
                if node:
                    node_ids.append(node.id)
            
            # 构建题目对象
            q = Question(
                subject=subject,
                grade=grade,
                type=q_data.get("type", "选择题"),
                difficulty=q_data.get("difficulty", 3),
                content=q_data.get("content", ""),
                answer=q_data.get("answer", ""),
                analysis=q_data.get("analysis", ""),
                knowledge_relation=node_ids,
            )
            
            # 选项
            opts_data = q_data.get("options", [])
            opts = [Option(label=o.get("label", ""), text=o.get("text", ""),
                           is_correct=bool(o.get("correct"))) for o in opts_data]
            
            # 入库
            bank.add(q, opts)
            total += 1
        
        print(f"  ✓ {subject}/{grade}: {len(questions)} 题 (导入 {total})")
    
    return total


def main():
    ap = argparse.ArgumentParser(description="盐城专项数据导入")
    ap.add_argument("--db", default=None, help="数据库路径")
    args = ap.parse_args()
    
    import config.settings as cfg
    db_path = Path(args.db) if args.db else cfg.DB_PATH
    dm = DataManager(db_path)
    
    print("=" * 60)
    print("盐城专项数据导入 SmartStudy OS")
    print("=" * 60)
    print(f"数据库: {db_path}")
    print()
    
    subjects = ["数学", "语文", "英语", "科学"]
    total_k = 0
    total_q = 0
    
    for subject in subjects:
        print(f"\n--- {subject} ---")
        
        # 导入知识图谱
        k_imported, k_updated = import_knowledge(dm, subject)
        total_k += k_imported
        
        # 导入题库
        q_imported = import_questions(dm, subject)
        total_q += q_imported
    
    print("\n" + "=" * 60)
    print(f"导入完成！")
    print(f"  知识节点: 新增 {total_k} 个")
    print(f"  题目: {total_q} 道")
    print(f"  覆盖: 数学(1-6) 语文(1-6) 英语(3-6) 科学(1-6)")
    print("=" * 60)


if __name__ == "__main__":
    main()
