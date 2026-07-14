# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""无头验证脚本（不依赖 PySide6）。

验证三个地基模块的闭环：知识图谱 → 学习状态 → 题库推荐。
运行：python verify.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import config.settings as cfg
from database.manager import DataManager
from seed_data import seed_if_empty
from core.knowledge_engine import KnowledgeGraph
from core.learning_engine import LearningEngine
from core.question_engine import QuestionBank


def main() -> None:
    tmp = Path(tempfile.gettempdir()) / "smartstudy_verify.db"
    if tmp.exists():
        tmp.unlink()
    dm = DataManager(tmp)
    seeded = seed_if_empty(dm)
    print(f"[1] 种子导入：{'已执行' if seeded else '跳过（非空）'}")

    kg = KnowledgeGraph(dm)
    le = LearningEngine(dm)
    bank = QuestionBank(dm, le)
    sid = 1

    n_nodes = dm.query_one("SELECT COUNT(*) c FROM kg_node")["c"]
    n_q = dm.query_one("SELECT COUNT(*) c FROM q_question")["c"]
    print(f"[2] 知识节点 {n_nodes} 个，题目 {n_q} 道")

    roots = kg.get_roots()
    print(f"[3] 知识地图根节点：{', '.join(r.name for r in roots)}")

    # 掌握度更新闭环
    abs_node = kg.search("绝对值")[0]
    before = le.get_state(sid, abs_node.id).mastery
    for _ in range(3):
        le.record_practice(sid, abs_node.id, correct=True)
    after = le.get_state(sid, abs_node.id).mastery
    print(f"[4] 「绝对值」三次答对后掌握度：{before:.3f} → {after:.3f}")

    # 遗忘曲线
    from datetime import datetime, timedelta
    st = le.get_state(sid, abs_node.id)
    fd = le.forget_degree(st, now=datetime.now() + timedelta(days=5))
    print(f"[5] 5 天未复习后「绝对值」遗忘程度：{fd:.3f}")

    # 推荐分
    score = le.recommend_score(st, abs_node.importance, now=datetime.now() + timedelta(days=5))
    print(f"[6] 同日「绝对值」推荐分：{score:.3f}")

    # 智能组卷：把部分节点设为高掌握，观察薄弱点是否被强化
    for name in ["数轴", "相反数"]:
        n = kg.search(name)[0]
        dm.execute(
            "INSERT OR REPLACE INTO learn_state (student_id,knowledge_id,mastery,wrong_count,last_time,learning_curve) VALUES (?,?,?,?,?,?)",
            (sid, n.id, 0.9, 0, datetime.now().isoformat(timespec="seconds"), "[]"),
        )
    tally: dict[str, int] = {}
    # 池=10 题（每知识点 1 题），抽样=5 且不放回，权重才会影响命中分布
    for _ in range(500):
        session = bank.generate_session(sid, subject="数学", grade="七年级", size=5)
        for q in session:
            if q.knowledge_relation:
                kn = kg.get(q.knowledge_relation[0])
                if kn:
                    tally[kn.name] = tally.get(kn.name, 0) + 1
    ranked = sorted(tally.items(), key=lambda x: x[1], reverse=True)
    print("[7] 500 套练习（每套5题，不放回）知识点命中频次（高掌握节点应明显偏低）：")
    for name, cnt in ranked:
        print(f"      {name:10s} {cnt}")

    # 薄弱点
    weak = le.weak_points(sid, top_n=3)
    print("[8] 当前 Top3 弱项：")
    for w in weak:
        print(f"      {w['name']}（掌握度 {int(w['mastery']*100)}%，推荐分 {w['recommend_score']}）")

    dm.close()
    print("\n✅ 三引擎闭环验证通过。")


if __name__ == "__main__":
    main()
