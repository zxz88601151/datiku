# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""知识树加载器（Phase 1.5-B）。

读取 resources/knowledge/{primary_math,middle_math}/gradeN.json，
将节点幂等写入知识图谱，并建立：
- 父子层级（parent 名称解析）；
- 先修/后继跨链接（predecessor/successor 名称解析，支持跨年级，如 一次函数→二次函数）。

富化字段：summary / formula / formula_list / important / errors / node_type。
importance 由 important 推导（核心考点 0.85，其余 0.45），供推荐分使用。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

from database.manager import DataManager
from core.knowledge_engine import KnowledgeGraph, KnowledgeNode


class KnowledgeTreeLoader:
    def __init__(self, dm: DataManager):
        self.dm = dm
        self.kg = KnowledgeGraph(dm)
        self.index: Dict[Tuple[str, str], int] = {}   # (subject, name) -> id（跨年级解析用）
        self.index_full: Dict[Tuple[str, str, str], int] = {}  # (subject, grade, name) -> id
        self.relations_map: Dict[int, List[str]] = {}  # nid -> 横向关联名称列表（pass2 解析）

    def _upsert(self, subject: str, grade: str, node: dict) -> int:
        name = node["name"]
        existing = self.kg.find(subject, grade, name)
        formula = node.get("formula")
        if isinstance(formula, list):
            formula_list = formula
            formula_str = "\n".join(formula)
        else:
            formula_str = formula or ""
            formula_list = [formula_str] if formula_str else []
        important = bool(node.get("important"))
        fields = {
            "summary": node.get("summary", ""),
            "node_type": node.get("type", "knowledge"),
            "important": important,
            "predecessor": node.get("predecessor") or [],
            "successor": node.get("successor") or [],
            "errors": node.get("errors") or [],
            "formula": formula_str,
            "formula_list": formula_list,
            "importance": 0.85 if important else 0.45,
            "content": node.get("summary", ""),
        }
        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            self.kg.update(existing)
            nid = existing.id
        else:
            kn = KnowledgeNode(name=name, subject=subject, grade=grade, **fields)
            nid = self.kg.add(kn)
        self.index[(subject, name)] = nid
        self.index_full[(subject, grade, name)] = nid
        self.relations_map[nid] = node.get("relations") or []
        return nid

    def load_all(self, trees: List[dict]) -> int:
        # pass1：创建/更新所有节点
        for tree in trees:
            subject, grade = tree["subject"], tree["grade"]
            for node in tree["nodes"]:
                self._upsert(subject, grade, node)
        # pass2：父子层级 + 先修/后继链接 + 横向 relations 关联
        for tree in trees:
            subject, grade = tree["subject"], tree["grade"]
            for node in tree["nodes"]:
                name = node["name"]
                nid = self.index_full[(subject, grade, name)]
                kn = self.kg.get(nid)
                parent = node.get("parent")
                inherited_relations: List[str] = []
                if parent:
                    pid = self.index_full.get((subject, grade, parent)) or self.index.get((subject, parent))
                    if pid and kn.parent_id != pid:
                        kn.parent_id = pid
                        self.kg.update(kn)
                    # 子概念继承父主题的先修/后继依赖（如 函数图像 继承 一次函数→正比例函数）
                    pnode = self.kg.get(pid) if pid else None
                    if pnode:
                        inherited = list(pnode.predecessor) + list(pnode.successor)
                        merged = list(kn.predecessor) + [r for r in inherited if r not in kn.predecessor]
                        if merged != kn.predecessor:
                            kn.predecessor = merged
                            self.kg.update(kn)
                        for r in inherited:
                            rid = self.index.get((subject, r))
                            if rid and rid != nid:
                                self.kg.link(nid, rid)
                        # 继承父节点的横向关联（提升图谱密度）
                        inherited_relations = list(getattr(pnode, "relation", []) or [])
                # 横向关联：本节点声明的 relations + 继承的父级 relations
                rel_names = list(self.relations_map.get(nid, [])) + inherited_relations
                linked_ids: List[int] = list(getattr(kn, "relation", []) or [])
                for rname in rel_names:
                    rid = self.index.get((subject, rname))
                    if rid and rid != nid and rid not in linked_ids:
                        self.kg.link(nid, rid)
                        linked_ids.append(rid)
                        # 反向也建立关联，保证无向可达（思维方法网络）
                        if nid not in (getattr(self.kg.get(rid), "relation", []) or []):
                            rnode = self.kg.get(rid)
                            rnode.relation = list(getattr(rnode, "relation", []) or []) + [nid]
                            self.kg.update(rnode)
                if linked_ids != list(getattr(kn, "relation", []) or []):
                    kn.relation = linked_ids
                    self.kg.update(kn)
                for rel in (node.get("predecessor", []) + node.get("successor", [])):
                    rid = self.index.get((subject, rel))
                    if rid and rid != nid:
                        self.kg.link(nid, rid)
        return len(self.index)


def load_knowledge_dir(dm: DataManager, root: Path) -> int:
    """加载 resources/knowledge 下全部 grade*.json。"""
    loader = KnowledgeTreeLoader(dm)
    trees: List[dict] = []
    for sub in ("middle_math", "primary_math"):
        d = root / sub
        if not d.exists():
            continue
        for p in sorted(d.glob("grade*.json")):
            trees.append(json.loads(p.read_text(encoding="utf-8")))
    return loader.load_all(trees)
