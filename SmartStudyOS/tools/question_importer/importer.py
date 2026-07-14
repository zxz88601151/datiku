# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""导入编排器 + 自动知识点绑定 + CLI。

职责：
1. 解析（Excel/JSON）→ 归一化行。
2. 自动知识点绑定：将 (学科, 年级, 章节, 知识点) 解析到知识图谱节点，
   知识点支持「字符串」或「数组」（一题绑定多个知识点）。
   复用已存在节点；缺失时按 create_missing 决定是否自动建 学科→年级→章节→知识点 链路。
3. 质量校验 + 重复检测。
4. 入库（题目 + 选项），知识点绑定写入 knowledge_relation。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from database.manager import DataManager
from core.knowledge_engine import KnowledgeGraph, KnowledgeNode
from core.question_engine import QuestionBank, Question, Option

from .excel_parser import parse_excel, _build_options
from .json_parser import parse_json
from .validator import validate_row, ALLOWED_TYPES
from .duplicate_check import DuplicateChecker, norm_key


def normalize_row(raw: Dict[str, Any], source: str) -> Dict[str, Any]:
    """将解析器产物转为标准行（含 options）。

    knowledge 保持原始形态（str 或 list），由 validator / binder 处理。
    """
    row = {
        "grade": str(raw.get("grade", "")).strip(),
        "subject": str(raw.get("subject", "")).strip(),
        "chapter": str(raw.get("chapter", "")).strip(),
        "knowledge": raw.get("knowledge", ""),
        "type": str(raw.get("type", "")).strip(),
        "content": str(raw.get("content", "")).strip(),
        "answer": str(raw.get("answer", "")).strip(),
        "analysis": str(raw.get("analysis", "")).strip(),
        "difficulty": raw.get("difficulty"),
        "exam_weight": raw.get("exam_weight", 1),
        "error_tags": raw.get("error_tags") or [],
    }
    if "options" in raw and isinstance(raw["options"], list):
        row["options"] = raw["options"]
    elif source == "excel":
        row["options"] = _build_options(raw)
    else:
        row["options"] = []
    return row


class BindError(Exception):
    pass


class KnowledgeBinder:
    """(学科, 年级, 章节, 知识点) → 知识图谱节点（支持多知识点）。"""

    def __init__(self, kg: KnowledgeGraph, create_missing: bool = True):
        self.kg = kg
        self.create_missing = create_missing

    def bind(self, subject: str, grade: str, chapter: str, knowledge: Any
             ) -> Tuple[List[Any], List[str]]:
        created: List[str] = []
        ids: List[Any] = []

        # 1) 章节节点（可选）
        chapter_node = None
        if chapter:
            chapter_node = self.kg.find(subject, grade, chapter)
            if chapter_node is None:
                if not self.create_missing:
                    raise BindError(f"章节不存在且禁止自动创建：{chapter}")
                subj_node = self.kg.find(subject, "", subject)
                if subj_node is None:
                    subj_node = self.kg.get(self.kg.add(
                        KnowledgeNode(name=subject, subject=subject, grade="", parent_id=None)))
                    created.append(f"学科节点:{subject}")
                grade_node = self.kg.find(subject, grade, grade)
                if grade_node is None:
                    grade_node = self.kg.get(self.kg.add(
                        KnowledgeNode(name=grade, subject=subject, grade=grade, parent_id=subj_node.id)))
                    created.append(f"年级节点:{subject}/{grade}")
                chapter_node = self.kg.get(self.kg.add(
                    KnowledgeNode(name=chapter, subject=subject, grade=grade, parent_id=grade_node.id)))
                created.append(f"章节节点:{subject}/{grade}/{chapter}")

        # 2) 知识点叶子节点（可多个）
        klist = knowledge if isinstance(knowledge, list) else [knowledge]
        for k in klist:
            k = str(k).strip()
            if not k:
                continue
            kn = self.kg.find(subject, grade, k)
            if kn is None:
                if not self.create_missing:
                    raise BindError(f"知识点不存在且禁止自动创建：{k}")
                parent_id = chapter_node.id if chapter_node else None
                kn = self.kg.get(self.kg.add(
                    KnowledgeNode(name=k, subject=subject, grade=grade, parent_id=parent_id)))
                created.append(f"知识点节点:{subject}/{grade}/{chapter}/{k}"
                               if chapter else f"知识点节点:{subject}/{grade}/{k}")
            ids.append(kn.id)
        return ids, created


@dataclass
class ImportReport:
    parsed: int = 0
    inserted: int = 0
    skipped_invalid: int = 0
    skipped_duplicate: int = 0
    auto_created_nodes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: List[Tuple[int, str, List[str]]] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            "==== 导入报告 ====",
            f"解析行数        : {self.parsed}",
            f"成功入库        : {self.inserted}",
            f"跳过(质量错误)  : {self.skipped_invalid}",
            f"跳过(重复)      : {self.skipped_duplicate}",
            f"自动创建节点    : {len(set(self.auto_created_nodes))}",
            f"警告数          : {len(self.warnings)}",
        ]
        uniq_created = sorted(set(self.auto_created_nodes))
        if uniq_created:
            lines.append("-- 新建知识点路径 --")
            lines += [f"  + {p}" for p in uniq_created]
        if self.details:
            lines.append("-- 跳过明细 --")
            for idx, kind, msgs in self.details:
                lines.append(f"  行{idx}: [{kind}] " + "; ".join(msgs))
        if self.warnings:
            lines.append("-- 警告 --")
            lines += [f"  ! {w}" for w in self.warnings]
        return "\n".join(lines)


class QuestionImporter:
    def __init__(self, dm: DataManager, create_missing: bool = True,
                 allow_invalid: bool = False):
        self.dm = dm
        self.kg = KnowledgeGraph(dm)
        self.bank = QuestionBank(dm)  # 导入阶段无需学习引擎
        self.binder = KnowledgeBinder(self.kg, create_missing)
        self.allow_invalid = allow_invalid

    def import_file(self, path: str) -> ImportReport:
        p = Path(path)
        if p.suffix.lower() in (".xlsx", ".xlsm", ".xls"):
            raws = parse_excel(str(p))
            source = "excel"
        elif p.suffix.lower() == ".json":
            raws = parse_json(str(p))
            source = "json"
        else:
            raise ValueError(f"不支持的文件类型：{p.suffix}")
        return self.import_rows(raws, source)

    @staticmethod
    def _coerce_weight(v: Any) -> int:
        try:
            w = int(v)
        except (TypeError, ValueError):
            return 1
        return max(1, min(5, w))

    def import_rows(self, raws: List[Dict[str, Any]], source: str = "json"
                    ) -> ImportReport:
        report = ImportReport()
        checker = DuplicateChecker(self.dm)
        for i, raw in enumerate(raws, 1):
            report.parsed += 1
            row = normalize_row(raw, source)
            errors, warns = validate_row(row)
            report.warnings.extend(f"行{i}: {w}" for w in warns)
            if errors:
                if not self.allow_invalid:
                    report.skipped_invalid += 1
                    report.details.append((i, "invalid", errors))
                    continue

            # 绑定知识点（字符串或数组）
            try:
                node_ids, created = self.binder.bind(
                    row["subject"], row["grade"], row["chapter"], row["knowledge"])
            except BindError as e:
                report.skipped_invalid += 1
                report.details.append((i, "bind", [str(e)]))
                continue
            if not node_ids:
                report.skipped_invalid += 1
                report.details.append((i, "bind", ["未解析到任何知识点"]))
                continue
            report.auto_created_nodes.extend(created)

            # 选择题：答案未填则回退到正确选项 label
            options = row.get("options") or []
            if row["type"] == "选择题" and not row["answer"] and options:
                correct = next((o for o in options if o.get("correct")), None)
                if correct:
                    row["answer"] = str(correct.get("label", ""))
                    report.warnings.append(f"行{i}: 选择题答案回退为正确选项 {row['answer']}")

            # 去重
            key = norm_key(row)
            if checker.is_duplicate(key):
                report.skipped_duplicate += 1
                continue
            checker.mark(key)

            # 入库
            q = Question(
                subject=row["subject"], grade=row["grade"], type=row["type"],
                difficulty=row["difficulty"],
                exam_weight=self._coerce_weight(row["exam_weight"]),
                content=row["content"], answer=row["answer"], analysis=row["analysis"],
                knowledge_relation=node_ids,
                error_tags=row.get("error_tags") or [],
            )
            opts = [Option(label=o.get("label", ""), text=o.get("text", ""),
                           is_correct=bool(o.get("correct"))) for o in options]
            self.bank.add(q, opts)
            report.inserted += 1
        return report


def run_cli(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="SmartStudy OS 题库批量导入")
    ap.add_argument("path", help="Excel(.xlsx) 或 JSON 题目文件")
    ap.add_argument("--db", default=None, help="SQLite 路径（默认项目 data/smartstudy.db）")
    ap.add_argument("--no-create-missing", action="store_true",
                    help="禁止自动创建缺失的知识点/章节节点（用于强制数据完整性）")
    ap.add_argument("--allow-invalid", action="store_true",
                    help="允许质量不合格的行也入库（不推荐）")
    args = ap.parse_args(argv)

    import config.settings as cfg
    db_path = Path(args.db) if args.db else cfg.DB_PATH
    dm = DataManager(db_path)
    imp = QuestionImporter(dm, create_missing=not args.no_create_missing,
                           allow_invalid=args.allow_invalid)
    try:
        report = imp.import_file(args.path)
    except Exception as e:
        print(f"导入失败：{e}", file=sys.stderr)
        return 1
    print(report.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
