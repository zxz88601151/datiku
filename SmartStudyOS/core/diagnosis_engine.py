# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""AI 错因诊断引擎（Phase 2.3）。

从「题目错了」到「为什么错」，四层诊断流水线：

1. ErrorAnalyzer    — 聚合 session 或历史事件中的错误标签，按知识点分组
2. PatternDetector  — 匹配预定义错误模式库，识别知识缺陷 vs 粗心
3. RecoveryPlanner  — 沿先修链查找根因，生成补救学习路径
4. InterventionTracker — 持久化诊断报告 + 恢复任务，追踪掌握度变化

不依赖大模型 —— 基于规则引擎 + 统计 + 知识图谱，可解释性强。
"""

from __future__ import annotations

import uuid
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from database.manager import DataManager
from core.knowledge_engine import KnowledgeGraph
from core.learning_engine import LearningEngine


# ---------------------------------------------------------------------------
# 错误模式库（标准模式，匹配 config.settings.ERROR_TAGS 中的标签）
# ---------------------------------------------------------------------------
# 每条模式：名称、关联知识点、症状标签、根因知识点、置信度权重
ERROR_PATTERNS: List[Dict[str, Any]] = [
    {
        "id": "FUNC_SLOPE_SIGN",
        "name": "斜率符号判断错误",
        "subject": "数学",
        "knowledge": ["一次函数", "函数图像"],
        "symptoms": ["符号错误", "混淆增减性"],
        "root_knowledge": ["正比例函数", "一次函数"],
        "recovery_steps": ["复习正比例函数 y=kx 中 k 的符号与图像关系",
                           "练习根据 k 符号判断函数图像"],
    },
    {
        "id": "FUNC_INTERCEPT",
        "name": "截距理解错误",
        "knowledge": ["一次函数", "函数图像"],
        "symptoms": ["公式误用", "概念混淆"],
        "root_knowledge": ["一次函数", "坐标系"],
        "recovery_steps": ["复习一次函数 y=kx+b 中 b 的含义",
                           "练习从图像读取截距"],
    },
    {
        "id": "ALG_EQ_MOVE",
        "name": "移项不变号",
        "knowledge": ["一元一次方程", "二元一次方程组", "不等式"],
        "symptoms": ["移项不变号", "符号错误"],
        "root_knowledge": ["一元一次方程"],
        "recovery_steps": ["复习移项法则：过等号变符号",
                           "练习 10 道移项基础题"],
    },
    {
        "id": "ALG_DENOM",
        "name": "去分母漏乘",
        "knowledge": ["一元一次方程", "分式"],
        "symptoms": ["去分母漏乘", "漏乘分配律"],
        "root_knowledge": ["一元一次方程"],
        "recovery_steps": ["复习去分母：每项都要乘以最小公倍数",
                           "练习含分母方程的完整解法"],
    },
    {
        "id": "GEO_MODEL",
        "name": "几何模型列错",
        "knowledge": ["全等三角形", "相似三角形", "四边形", "圆"],
        "symptoms": ["模型列错", "定理记反", "分类讨论遗漏"],
        "root_knowledge": ["三角形", "全等三角形", "相似三角形"],
        "recovery_steps": ["回顾常见几何模型（A 字型、8 字型）",
                           "练习模型识别与条件标注"],
    },
    {
        "id": "GEO_COORD",
        "name": "坐标系误用",
        "knowledge": ["平面直角坐标系", "函数图像"],
        "symptoms": ["坐标系误用", "坐标轴读取错误"],
        "root_knowledge": ["平面直角坐标系"],
        "recovery_steps": ["复习坐标系四象限与坐标表示",
                           "练习点坐标到函数图像的映射"],
    },
    {
        "id": "CALC_COMPUTE",
        "name": "基础计算失误",
        "knowledge": ["有理数运算", "实数运算", "整式运算"],
        "symptoms": ["计算失误", "小数点位数错"],
        "root_knowledge": ["有理数运算"],
        "recovery_steps": ["复习运算法则与优先级",
                           "每日 5 分钟口算训练"],
    },
    {
        "id": "CALC_FORMULA",
        "name": "公式误用",
        "knowledge": ["乘法公式", "因式分解", "二次根式"],
        "symptoms": ["公式误用", "约分遗漏"],
        "root_knowledge": ["整式运算", "因式分解"],
        "recovery_steps": ["整理常用公式卡片",
                           "练习公式的正向与逆向使用"],
    },
    {
        "id": "GEOM_CIRCLE",
        "name": "圆的性质理解不足",
        "knowledge": ["圆", "圆的性质", "圆周角"],
        "symptoms": ["定理记反", "图形理解偏差"],
        "root_knowledge": ["圆", "三角形"],
        "recovery_steps": ["复习圆心角定理与圆周角定理",
                           "练习圆中角度关系的推理"],
    },
    {
        "id": "STATS_PROB",
        "name": "概率统计概念混淆",
        "knowledge": ["概率", "统计"],
        "symptoms": ["概念混淆", "单位遗漏"],
        "root_knowledge": ["概率", "统计"],
        "recovery_steps": ["区分概率与频数概念",
                           "练习用树状图/列表法计算概率"],
    },
]


# ---------------------------------------------------------------------------
# 诊断数据结构
# ---------------------------------------------------------------------------
class DiagnosticFinding:
    """单条诊断发现。"""
    def __init__(self, pattern_id: str, pattern_name: str,
                 knowledge_id: int, knowledge_name: str,
                 frequency: int, total_errors: int,
                 root_knowledge_ids: List[int],
                 recovery_steps: List[str],
                 is_root_cause: bool = False):
        self.pattern_id = pattern_id
        self.pattern_name = pattern_name
        self.knowledge_id = knowledge_id
        self.knowledge_name = knowledge_name
        self.frequency = frequency
        self.total_errors = total_errors
        self.root_knowledge_ids = root_knowledge_ids
        self.recovery_steps = recovery_steps
        self.is_root_cause = is_root_cause

    @property
    def confidence(self) -> float:
        ratio = self.frequency / max(1, self.total_errors)
        return min(1.0, ratio + 0.15)  # 保底 0.15 可信度

    def to_dict(self) -> dict:
        return {
            "pattern_id": self.pattern_id,
            "pattern_name": self.pattern_name,
            "knowledge_id": self.knowledge_id,
            "knowledge_name": self.knowledge_name,
            "frequency": self.frequency,
            "total_errors": self.total_errors,
            "confidence": round(self.confidence, 3),
            "root_knowledge_ids": self.root_knowledge_ids,
            "recovery_steps": self.recovery_steps,
            "is_root_cause": self.is_root_cause,
        }


class DiagnosisReport:
    """完整的诊断报告。"""
    def __init__(self, student_id: int, session_id: str,
                 findings: List[DiagnosticFinding],
                 total_errors: int, total_questions: int):
        self.student_id = student_id
        self.session_id = session_id
        self.findings = findings
        self.total_errors = total_errors
        self.total_questions = total_questions
        self.created_at = datetime.now().isoformat(timespec="seconds")

    @property
    def confidence(self) -> float:
        return max((f.confidence for f in self.findings), default=0.0)

    @property
    def primary(self) -> Optional[DiagnosticFinding]:
        return max(self.findings, key=lambda f: f.frequency) if self.findings else None


class RecoveryPath:
    """一条补救学习路径。"""
    def __init__(self, finding: DiagnosticFinding,
                 prerequisite_steps: List[Dict[str, Any]],
                 target_question_ids: List[int]):
        self.finding = finding
        self.prerequisite_steps = prerequisite_steps   # [{knowledge_id, name, mastery}]
        self.target_question_ids = target_question_ids
        self.status = "pending"


# ---------------------------------------------------------------------------
# 诊断引擎
# ---------------------------------------------------------------------------
class DiagnosisEngine:
    """四层诊断引擎。"""

    def __init__(self, dm: DataManager, kg: KnowledgeGraph, le: LearningEngine):
        self.dm = dm
        self.kg = kg
        self.le = le

    # =============== 1. ErrorAnalyzer ===============
    def analyze_session_errors(self, student_id: int, session_id: str,
                                session_results: List[dict]) -> Dict[str, Any]:
        """从一次 session 的作答结果聚合错误标签。

        session_results: [{question_id, correct, error_tags, knowledge_id, ...}]
        返回：{error_tag: {count, knowledge_ids: set, question_ids: []}}
        """
        agg: Dict[str, Dict] = {}
        for r in session_results:
            if r.get("correct", True):
                continue
            tags = r.get("error_tags") or []
            kid = r.get("knowledge_id")
            qid = r.get("question_id")
            for tag in tags:
                if tag not in agg:
                    agg[tag] = {"count": 0, "knowledge_ids": set(), "question_ids": []}
                agg[tag]["count"] += 1
                if kid:
                    agg[tag]["knowledge_ids"].add(kid)
                if qid:
                    agg[tag]["question_ids"].append(qid)
        return agg

    def analyze_historical_errors(self, student_id: int, limit_days: int = 30) -> Dict[str, Any]:
        """从 learning_event 和 learn_wrong 聚合近期错误。"""
        since = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                 .isoformat(timespec="seconds"))
        if limit_days:
            from datetime import timedelta
            since = (datetime.now() - timedelta(days=limit_days)).isoformat(timespec="seconds")

        # 从 learn_wrong 获取
        wrong_rows = self.dm.query(
            "SELECT qw.question_id, qw.count, qw.wrong_reason, q.knowledge_relation "
            "FROM learn_wrong qw "
            "JOIN q_question q ON q.id = qw.question_id "
            "WHERE qw.student_id=? AND qw.resolved=0",
            (student_id,),
        )
        agg: Dict[str, Dict] = {}
        for r in wrong_rows:
            reason = (r.get("wrong_reason") or "").strip()
            cnt = r.get("count", 1)
            kids = self.dm.loads(r.get("knowledge_relation") or "[]")
            tags = [t.strip() for t in reason.split(";") if t.strip()] if reason and reason != "待归因" else ["待归因"]
            for tag in tags:
                if tag not in agg:
                    agg[tag] = {"count": 0, "knowledge_ids": set(), "question_ids": []}
                agg[tag]["count"] += cnt
                for kid in kids:
                    agg[tag]["knowledge_ids"].add(kid)
                agg[tag]["question_ids"].append(r["question_id"])
        return agg

    # =============== 2. PatternDetector ===============
    def detect(self, error_aggregation: Dict[str, Dict],
               student_id: int) -> List[DiagnosticFinding]:
        """匹配错误模式，生成诊断发现列表。"""
        total_errors = sum(v["count"] for v in error_aggregation.values())
        if total_errors == 0:
            return []

        # 1) 按知识点聚合错误标签
        kid_tag_counts: Dict[int, Counter] = defaultdict(Counter)
        kid_names: Dict[int, str] = {}
        for tag, info in error_aggregation.items():
            for kid in info["knowledge_ids"]:
                kid_tag_counts[kid][tag] += info["count"]
                if kid not in kid_names:
                    kn = self.kg.get(kid)
                    kid_names[kid] = kn.name if kn else f"#{kid}"

        # 2) 匹配错误模式库
        findings = []
        for kid, tag_counter in kid_tag_counts.items():
            kname = kid_names.get(kid, "")
            top_tags = [t for t, _ in tag_counter.most_common(5)]
            top_freq = tag_counter.most_common(1)[0][1] if tag_counter else 0

            # 匹配知识名称 + 症状标签
            best_match = None
            best_overlap = 0
            for pattern in ERROR_PATTERNS:
                kn_overlap = len([k for k in pattern["knowledge"] if k in kname])
                tag_overlap = len([t for t in pattern["symptoms"] if t in top_tags])
                overlap = kn_overlap + tag_overlap
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_match = pattern

            if best_match and best_overlap > 0:
                # 解析根因知识点 ID
                root_ids = []
                for rname in best_match["root_knowledge"]:
                    rnodes = self.dm.query(
                        "SELECT id FROM kg_node WHERE subject='数学' AND name LIKE ?",
                        (f"%{rname}%",),
                    )
                    for rn in rnodes:
                        root_ids.append(rn["id"])

                findings.append(DiagnosticFinding(
                    pattern_id=best_match["id"],
                    pattern_name=best_match["name"],
                    knowledge_id=kid,
                    knowledge_name=kname,
                    frequency=top_freq,
                    total_errors=total_errors,
                    root_knowledge_ids=root_ids[:3],
                    recovery_steps=best_match.get("recovery_steps", []),
                ))
            else:
                # 无匹配时的兜底诊断
                findings.append(DiagnosticFinding(
                    pattern_id="GENERIC",
                    pattern_name=f"{kname}相关错误",
                    knowledge_id=kid,
                    knowledge_name=kname,
                    frequency=top_freq,
                    total_errors=total_errors,
                    root_knowledge_ids=[kid],
                    recovery_steps=[f"复习 {kname} 基本概念与典型题"],
                ))

        # 3) 根因定位：检查先修知识点
        for finding in findings:
            root_ids = set(finding.root_knowledge_ids)
            for rid in list(root_ids):
                if rid == finding.knowledge_id:
                    continue
                # 检查先修掌握度
                st = self.le.get_state(student_id, rid)
                if st and st.mastery < 0.45:
                    finding.is_root_cause = True
                    break

        return sorted(findings, key=lambda f: -f.frequency)

    # =============== 3. RecoveryPlanner ===============
    def plan_recovery(self, student_id: int,
                      findings: List[DiagnosticFinding],
                      top_n: int = 2) -> List[RecoveryPath]:
        """为前 N 个发现生成补救路径。"""
        paths = []
        for finding in findings[:top_n]:
            # 先修节点掌握度
            prereq_steps = []
            for rid in finding.root_knowledge_ids:
                if rid == finding.knowledge_id and len(finding.root_knowledge_ids) > 1:
                    continue
                st = self.le.get_state(student_id, rid)
                kn = self.kg.get(rid)
                prereq_steps.append({
                    "knowledge_id": rid,
                    "name": kn.name if kn else f"#{rid}",
                    "mastery": round(st.mastery, 3) if st else 0.0,
                })

            # 生成目标题目列表（基于目标知识点）
            qids = []
            target_kids = [finding.knowledge_id] + finding.root_knowledge_ids
            for kid in set(target_kids):
                qs = self.le.get_state(student_id, kid)  # not needed
                qrows = self.dm.query(
                    "SELECT id FROM q_question "
                    "WHERE knowledge_relation LIKE ? ORDER BY RANDOM() LIMIT 5",
                    (f"%\"{kid}\"%",),
                )
                qids.extend(r["id"] for r in qrows)

            paths.append(RecoveryPath(
                finding=finding,
                prerequisite_steps=prereq_steps,
                target_question_ids=qids[:8],
            ))
        return paths

    # =============== 4. InterventionTracker ===============
    def save_report(self, report: DiagnosisReport) -> int:
        """持久化诊断报告并写入 recovery_task。"""
        # 主报告
        summary = {
            "findings": [f.to_dict() for f in report.findings],
            "total_errors": report.total_errors,
            "total_questions": report.total_questions,
        }
        report_id = self.dm.insert("diagnosis_report", {
            "student_id": report.student_id,
            "session_id": report.session_id,
            "summary": self.dm.dumps(summary),
            "confidence": round(report.confidence, 3),
            "created_at": report.created_at,
        })
        # 恢复任务
        for finding in report.findings[:2]:
            target_kids = list(dict.fromkeys(
                finding.root_knowledge_ids + [finding.knowledge_id]))
            qids = []
            for kid in target_kids:
                rows = self.dm.query(
                    "SELECT id FROM q_question WHERE knowledge_relation LIKE ? LIMIT 4",
                    (f"%\"{kid}\"%",),
                )
                qids.extend(r["id"] for r in rows)
            self.dm.insert("recovery_task", {
                "student_id": report.student_id,
                "report_id": report_id,
                "finding_id": finding.pattern_id,
                "finding_name": finding.pattern_name,
                "source_knowledge_id": finding.knowledge_id,
                "target_knowledge_ids": self.dm.dumps(target_kids),
                "question_ids": self.dm.dumps(qids[:8]),
                "pre_mastery_before": round(finding.confidence, 2),
                "status": "pending",
                "created_at": datetime.now().isoformat(timespec="seconds"),
            })
        return report_id

    def get_recent_report(self, student_id: int) -> Optional[dict]:
        """获取最近一份诊断报告（含 findings 解析）。"""
        row = self.dm.query_one(
            "SELECT * FROM diagnosis_report WHERE student_id=? ORDER BY id DESC LIMIT 1",
            (student_id,),
        )
        if row:
            row["summary"] = self.dm.loads(row.get("summary") or "{}")
        return row

    def get_pending_tasks(self, student_id: int) -> List[dict]:
        """获取待处理的恢复任务。"""
        rows = self.dm.query(
            "SELECT * FROM recovery_task WHERE student_id=? AND status='pending' ORDER BY id",
            (student_id,),
        )
        for r in rows:
            r["question_ids"] = self.dm.loads(r.get("question_ids") or "[]")
            r["target_knowledge_ids"] = self.dm.loads(r.get("target_knowledge_ids") or "[]")
        return rows

    def complete_task(self, task_id: int, post_mastery: float = 0.0):
        """标记恢复任务完成。"""
        self.dm.execute(
            "UPDATE recovery_task SET status='completed', post_mastery=? WHERE id=?",
            (round(post_mastery, 3), task_id),
        )

    # =============== 全流程 ===============
    def run_full_diagnosis(self, student_id: int, session_id: str,
                            session_results: List[dict]) -> DiagnosisReport:
        """执行完整诊断流水线：分析 → 检测 → 规划 → 保存。"""
        agg = self.analyze_session_errors(student_id, session_id, session_results)
        # 补充历史错误
        hist = self.analyze_historical_errors(student_id, limit_days=30)
        for tag, info in hist.items():
            if tag in agg:
                agg[tag]["count"] += info["count"]
                agg[tag]["knowledge_ids"].update(info["knowledge_ids"])
            else:
                agg[tag] = info

        total_errors = sum(v["count"] for v in agg.values())
        total_questions = total_errors + 10  # 近似

        findings = self.detect(agg, student_id)
        report = DiagnosisReport(student_id, session_id, findings,
                                  total_errors, total_questions)
        self.save_report(report)
        return report
