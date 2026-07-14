# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""闭环验证（Phase 1.5-B 目标场景）。

模拟「学生A」：小学数学基础尚可，进入八年级后做一次函数测试，连续在
「函数图像」上出错 → 系统识别该知识点掌握度低 → 生成以「函数图像基础题」
为主的强化练习，并建议复习先修知识点「正比例函数」。

全程使用临时 SQLite，不污染项目库；数据由知识树 + 题库生成器实时产出。
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import config.settings as cfg
from database.manager import DataManager
from core.knowledge_engine import KnowledgeGraph
from core.question_engine import QuestionBank
from core.learning_engine import LearningEngine

from tools.content.load_knowledge import load_knowledge_dir
from tools.question_importer.importer import QuestionImporter


def main() -> int:
    # 1) 确保知识树与题库资产存在（幂等）
    from tools.content.build_knowledge import main as build_knowledge
    from tools.question_generator.generator import generate_all
    print("== 构建知识树 & 题库资产 ==")
    build_knowledge()
    generate_all(count_per_node=12)

    # 2) 临时库
    tmp = Path(tempfile.mkdtemp()) / "validate_loop.db"
    dm = DataManager(tmp)

    n_nodes = load_knowledge_dir(dm, cfg.PROJECT_ROOT / "resource" / "knowledge")
    imp = QuestionImporter(dm, create_missing=False, allow_invalid=False)
    q_root = cfg.PROJECT_ROOT / "resource" / "questions"
    q_total = 0
    for sub in ("middle_math", "primary_math"):
        for p in sorted((q_root / sub).glob("grade*.json")):
            rep = imp.import_file(str(p))
            q_total += rep.inserted
    print(f"知识节点: {n_nodes}   题目: {q_total}\n")

    # 3) 学生A
    dm.execute(
        "INSERT INTO user (id,name,grade,school,guardian,created_at) VALUES (?,?,?,?,?,?)",
        (1, "学生A", "八年级", "盐城某中学", "家长", "2026-01-01T00:00:00"),
    )
    kg = KnowledgeGraph(dm)
    le = LearningEngine(dm)
    bank = QuestionBank(dm, learning_engine=le)

    # 4) 定位一次函数的知识子树
    fn = kg.find("数学", "八年级", "一次函数")
    assert fn, "一次函数 节点缺失"
    descendants = kg.get_descendants(fn.id)  # 一次函数定义 / 函数图像 / 一次函数性质
    img = kg.find("数学", "八年级", "函数图像")
    assert img, "函数图像 节点缺失"
    img_qs = bank.get_by_knowledge(img.id)
    print(f"『函数图像』题目数: {len(img_qs)}")

    # 5) 模拟学习：定义/性质练到熟练，函数图像连续出错
    for d in descendants:
        if d.name == "函数图像":
            for q in img_qs[:4]:
                le.record_practice(1, d.id, correct=True)
            for q in img_qs[4:7]:
                le.record_practice(1, d.id, correct=False)
        else:
            for _ in range(10):
                le.record_practice(1, d.id, correct=True)

    st = le.get_state(1, img.id)
    print(f"→ 模拟后『函数图像』掌握度: {st.mastery:.3f}   错次: {st.wrong_count}")

    # 6) 智能推荐：八年级一次函数区域，基础难度优先
    kn_ids = [d.id for d in descendants]
    session = bank.generate_session(
        1, subject="数学", grade="八年级", size=10,
        max_difficulty=2, knowledge_ids=kn_ids,
    )
    tally: dict = {}
    for q in session:
        for kid in q.knowledge_relation:
            nn = kg.get(kid)
            if nn:
                tally[nn.name] = tally.get(nn.name, 0) + 1
    print("\n[推荐练习 10 题 · 基础难度] 知识点命中分布：")
    for k, v in sorted(tally.items(), key=lambda x: -x[1]):
        print(f"   {k}: {v} 题")

    # 7) 薄弱点 & 复习建议
    weak = le.weak_points(1, top_n=5)
    print("\n[薄弱点 TOP]")
    for w in weak:
        print(f"   {w['name']:<10} 掌握度 {w['mastery']:<6} 推荐分 {w['recommend_score']}")

    pre = kg.find("数学", "八年级", "正比例函数")
    pre_st = le.get_state(1, pre.id) if pre else None
    print("\n[复习建议]")
    print(f"   『函数图像』的先修链: {' → '.join(img.predecessor) or '(无)'}")
    if pre and pre_st is not None:
        print(f"   建议优先复习『正比例函数』(先修)，当前掌握度 {pre_st.mastery:.3f}")

    # 8) 判定
    img_hits = tally.get("函数图像", 0)
    ok = img_hits >= 6 and st.mastery < 0.5
    print("\n" + ("✅ 闭环验证通过：薄弱知识点被正确识别并优先强化，先修链给出复习建议。"
                  if ok else "⚠️ 验证未达预期，请检查推荐权重或数据分布。"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
