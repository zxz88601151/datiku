# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""知识图谱引擎（Knowledge Graph Engine）。

提供知识点的增删改查、层级树构建、祖先/后代路径、跨链接关联查询。
这是整个系统的「灵魂」——普通刷题软件只有「章节→题目」扁平结构，
本引擎维护「概念世界」：节点是知识点，边是关联关系与先修依赖。
"""

from __future__ import annotations

from typing import Dict, List, Optional

from database.manager import DataManager
from .node import KnowledgeNode


class KnowledgeGraph:
    def __init__(self, dm: DataManager):
        self.dm = dm

    # ---- 写 -----------------------------------------------------------
    def add(self, node: KnowledgeNode) -> int:
        return self.dm.insert("kg_node", node.to_row())

    def update(self, node: KnowledgeNode) -> None:
        if node.id is None:
            raise ValueError("node.id 为空，无法更新")
        self.dm.update("kg_node", node.to_row(), "id = ?", (node.id,))

    def delete(self, node_id: int) -> None:
        # 父节点删除会级联删除子节点（ON DELETE CASCADE）
        self.dm.execute("DELETE FROM kg_node WHERE id = ?", (node_id,))

    def link(self, node_id: int, related_id: int) -> None:
        """建立双向跨链接（relation 边）。"""
        a = self.get(node_id)
        b = self.get(related_id)
        if not a or not b:
            return
        if related_id not in a.relation:
            a.relation.append(related_id)
            self.update(a)
        if node_id not in b.relation:
            b.relation.append(node_id)
            self.update(b)

    # ---- 读 -----------------------------------------------------------
    def get(self, node_id: int) -> Optional[KnowledgeNode]:
        row = self.dm.query_one("SELECT * FROM kg_node WHERE id = ?", (node_id,))
        return KnowledgeNode.from_row(row) if row else None

    def get_children(self, parent_id: Optional[int]) -> List[KnowledgeNode]:
        if parent_id is None:
            rows = self.dm.query(
                "SELECT * FROM kg_node WHERE parent_id IS NULL ORDER BY id"
            )
        else:
            rows = self.dm.query(
                "SELECT * FROM kg_node WHERE parent_id = ? ORDER BY id", (parent_id,)
            )
        return [KnowledgeNode.from_row(r) for r in rows]

    def get_by_subject_grade(self, subject: str, grade: str) -> List[KnowledgeNode]:
        rows = self.dm.query(
            "SELECT * FROM kg_node WHERE subject = ? AND grade = ? ORDER BY id",
            (subject, grade),
        )
        return [KnowledgeNode.from_row(r) for r in rows]

    def find(self, subject: str, grade: str, name: str) -> Optional[KnowledgeNode]:
        """按 (学科, 年级, 名称) 精确定位节点，供导入器做知识点绑定复用。"""
        row = self.dm.query_one(
            "SELECT * FROM kg_node WHERE subject = ? AND grade = ? AND name = ?",
            (subject, grade, name),
        )
        return KnowledgeNode.from_row(row) if row else None

    def get_roots(self) -> List[KnowledgeNode]:
        return self.get_children(None)

    def get_related(self, node_id: int) -> List[KnowledgeNode]:
        node = self.get(node_id)
        if not node:
            return []
        return [self.get(rid) for rid in node.relation if self.get(rid)]

    def get_ancestors(self, node_id: int) -> List[KnowledgeNode]:
        """返回从根到当前节点的先修路径。"""
        path: List[KnowledgeNode] = []
        cur = self.get(node_id)
        seen = set()
        while cur and cur.id not in seen:
            seen.add(cur.id)
            path.append(cur)
            if cur.parent_id is None:
                break
            cur = self.get(cur.parent_id)
        return list(reversed(path))

    def get_descendants(self, node_id: int) -> List[KnowledgeNode]:
        """返回以 node_id 为根的全部后代（广度优先）。"""
        out: List[KnowledgeNode] = []
        queue = [node_id]
        while queue:
            nid = queue.pop(0)
            children = self.get_children(nid)
            for c in children:
                out.append(c)
                queue.append(c.id)
        return out

    def search(self, keyword: str, subject: Optional[str] = None) -> List[KnowledgeNode]:
        kw = f"%{keyword}%"
        if subject:
            rows = self.dm.query(
                "SELECT * FROM kg_node WHERE name LIKE ? AND subject = ?", (kw, subject)
            )
        else:
            rows = self.dm.query("SELECT * FROM kg_node WHERE name LIKE ?", (kw,))
        return [KnowledgeNode.from_row(r) for r in rows]

    # ---- 树导出（供 UI 渲染 / 知识地图） ------------------------------
    def build_tree(self, root_id: Optional[int] = None) -> Dict:
        """导出嵌套字典树：{node, children:[...]}。"""
        node = self.get(root_id) if root_id else None
        if root_id is not None and node is None:
            return {}
        children = self.get_children(root_id)

        def _rec(n: KnowledgeNode) -> Dict:
            return {
                "id": n.id,
                "name": n.name,
                "difficulty": n.difficulty,
                "mastery": n.mastery,
                "importance": n.importance,
                "children": [_rec(c) for c in self.get_children(n.id)],
            }

        if node is None:
            # 多根：返回森林
            return {
                "forest": True,
                "roots": [_rec(c) for c in children],
            }
        return _rec(node)
