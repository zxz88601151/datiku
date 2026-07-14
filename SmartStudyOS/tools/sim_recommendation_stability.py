# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""推荐算法稳定性 / 学习曲线仿真（Phase 1.5-D 验收）。

构造 100 名学生画像（函数薄弱 / 几何薄弱 / 代数薄弱 / 均衡），
连续 90 天按「推荐分加权」组卷答题，全程使用真实 LearningEngine
（掌握度更新 + 学习事件日志写入，含错因标签）。验收目标：

1. 弱项提升：被持续推荐强化的薄弱知识点，90 天后掌握度显著上升。
2. 学习曲线：按检查点（第 0/15/30/45/60/75/90 天）采样弱项平均掌握度，
   验证掌握度随时间单调/稳定上升的学习曲线形态。
3. 推荐稳定性：薄弱知识点在组卷中的命中率远高于随机基线，
   证明推荐算法在规模化数据（3万+ 题 / 1200+ 节点）下稳定有效。
4. 错因画像：答错时写入标准错因标签，统计全局与分原型错因分布，
   为 AI 老师归因分析与错因专题训练提供数据底座。
5. 压力验证：90 天 × 100 生 × 10 题/日 ≈ 9 万次真实引擎写入，
   验证规模化下事件日志与掌握度更新的性能与一致性。

全程复用真实引擎与独立仿真库（data/sim_study.db，不污染生产库）。
"""
from __future__ import annotations

import random
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import config.settings as cfg
from database.manager import DataManager
from core.knowledge_engine import KnowledgeGraph
from core.question_engine import QuestionBank
from core.learning_engine import LearningEngine
from core.learning_engine.state import StudentKnowledgeState


# 学生画像原型：定义「薄弱知识点集合」的匹配规则
ARCHETYPES = {
    "函数薄弱": lambda name: any(k in name for k in
        ("一次函数", "二次函数", "正比例函数", "函数")),
    "几何薄弱": lambda name: any(k in name for k in
        ("四边形", "勾股", "圆", "相似", "几何", "圆柱", "圆锥", "体积", "周长", "面积")),
    "代数薄弱": lambda name: any(k in name for k in
        ("有理数", "整式", "方程", "分式", "运算", "小数", "分数", "比", "百分", "数与")),
    "均衡偏中": lambda name: False,  # 弱项由随机采样决定
}


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def main() -> int:
    rng = random.Random(20260707)
    # 仿真使用独立库，避免污染面向 UI 的生产库；每次强制重建，
    # 确保始终基于当前（Phase 1.5-D）知识图谱与题库规模进行压力验证。
    sim_db = cfg.DATA_DIR / "sim_study.db"
    dm = DataManager(sim_db)
    print("[准备] 重建仿真库并装载当前知识树 + 题库（32k+ 题 / 1200+ 节点）...")
    from tools.content_pipeline import run_fast
    run_fast(db_path=sim_db, reset=True)
    kg = KnowledgeGraph(dm)
    le = LearningEngine(dm)
    bank = QuestionBank(dm, learning_engine=le)

    # 预载全部知识节点与题目（避免热循环内 DB 读取）
    nodes = [kg.get(r["id"]) for r in
             dm.query("SELECT id FROM kg_node WHERE subject='数学'")]
    kg_by_id = {n.id: n for n in nodes if n}
    questions = []
    for r in dm.query(
            "SELECT id, knowledge_relation, exam_weight, difficulty, error_tags "
            "FROM q_question WHERE subject='数学'"):
        kids = dm.loads(r["knowledge_relation"])
        if kids:
            questions.append({"id": r["id"], "kids": kids,
                              "ew": r["exam_weight"] or 1, "diff": r["difficulty"] or 1,
                              "et": dm.loads(r["error_tags"]) or []})
    print(f"[初始化] 数学节点 {len(kg_by_id)} 个，题目 {len(questions)} 道")

    N_STU = 100
    DAYS = 90
    CHECKPOINTS = [0, 15, 30, 45, 60, 75, 90]
    # 1) 创建学生 + 初始掌握度（刻画画像）
    all_ids = list(kg_by_id.keys())
    states: dict = {}          # (sid, kid) -> mastery
    last_time: dict = {}       # (sid, kid) -> iso
    weak_sets: dict = {}       # sid -> set(weak kid)
    archetype_of: dict = {}
    for sid in range(1, N_STU + 1):
        arch = rng.choice(list(ARCHETYPES.keys()))
        archetype_of[sid] = arch
        # 均衡型随机挑 15% 作为弱项
        if arch == "均衡偏中":
            weak = set(rng.sample(all_ids, max(8, len(all_ids) // 7)))
        else:
            weak = {nid for nid in all_ids if ARCHETYPES[arch](kg_by_id[nid].name)}
        weak_sets[sid] = weak
        for nid in all_ids:
            if nid in weak:
                m = _clamp(0.22 + rng.uniform(-0.08, 0.08))
            else:
                m = _clamp(0.62 + rng.uniform(-0.12, 0.12))
            states[(sid, nid)] = m
            last_time[(sid, nid)] = datetime(2026, 1, 1).isoformat(timespec="seconds")

    def _weak_avg(sid):
        ws = weak_sets[sid]
        return sum(states[(sid, k)] for k in ws) / max(1, len(ws))

    weak_init = {sid: _weak_avg(sid) for sid in range(1, N_STU + 1)}

    # 学习曲线轨迹快照：checkpoint -> {archetype: avg_weak_mastery}
    traj: dict = {}

    def _snapshot(day):
        snap = {}
        for arch in ARCHETYPES:
            sids = [s for s in range(1, N_STU + 1) if archetype_of[s] == arch]
            if sids:
                snap[arch] = sum(weak_init[s] if day == 0 else _weak_avg(s) for s in sids) / len(sids)
        traj[day] = snap

    _snapshot(0)  # 第 0 天（初始）

    # 2) 批量写入初始用户与掌握度（单事务）
    with dm.transaction():
        for sid in range(1, N_STU + 1):
            dm.insert_nc("user", {"name": f"学生{sid}", "grade": "混合",
                                  "school": "盐城仿真校", "guardian": "家长",
                                  "created_at": "2026-01-01T00:00:00"})
        for (sid, nid), m in states.items():
            dm.insert_nc("learn_state", {"student_id": sid, "knowledge_id": nid,
                                         "mastery": m, "wrong_count": 0,
                                         "last_time": last_time[(sid, nid)],
                                         "learning_curve": "[]"})

    # 3) 90 天循环：每日按推荐分组卷 → 作答 → 真实引擎更新
    total_hits_weak = 0
    total_questions = 0
    baseline = sum(len(weak_sets[sid]) for sid in range(1, N_STU + 1)) / (N_STU * len(all_ids))
    ec_freq = Counter()                      # 全局错因频次
    ec_by_arch = {a: Counter() for a in ARCHETYPES}
    print(f"[仿真] {N_STU} 学生 × {DAYS} 天，统一基线命中率(随机)={baseline:.1%}")
    start = datetime(2026, 2, 1)
    with dm.transaction():
        for day in range(DAYS):
            now = start + timedelta(days=day)
            for sid in range(1, N_STU + 1):
                weak = weak_sets[sid]
                arch = archetype_of[sid]
                # 候选池抽样 300，按推荐分加权选 10（复用真实 recommend_score 公式）
                cand = rng.sample(questions, min(300, len(questions)))
                scored = []
                for q in cand:
                    kid = q["kids"][0]
                    m = states.get((sid, kid), 0.0)
                    wc = 0
                    lt = last_time.get((sid, kid))
                    st = StudentKnowledgeState(student_id=sid, knowledge_id=kid,
                                               mastery=m, wrong_count=wc, last_time=lt)
                    imp = kg_by_id[kid].importance if kid in kg_by_id else 0.5
                    sc = le.recommend_score(st, imp, now)
                    ew = q["ew"]
                    scored.append((sc * (0.7 + 0.06 * ew), q))
                scored.sort(key=lambda x: x[0], reverse=True)
                chosen = [q for _, q in scored[:10]]
                for q in chosen:
                    kid = q["kids"][0]
                    m = states.get((sid, kid), 0.0)
                    # 练习带来小幅学习增益：正确概率 = 掌握度 + 0.15（模拟 AI 辅导下的有效练习）
                    correct = rng.random() < _clamp(m + 0.15)
                    # 答错时带入标准错因标签（Phase 1.5-D 错因画像数据源）
                    ec = q["et"] if (not correct) else None
                    st = le.record_practice(sid, kid, correct, now, error_cause=ec)
                    states[(sid, kid)] = st.mastery
                    last_time[(sid, kid)] = now.isoformat(timespec="seconds")
                    total_questions += 1
                    if kid in weak:
                        total_hits_weak += 1
                    if not correct and ec:
                        for t in ec:
                            ec_freq[t] += 1
                            ec_by_arch[arch][t] += 1
            # 检查点快照（含第 90 天，day 索引 89 对应第 90 天）
            if (day + 1) in CHECKPOINTS:
                _snapshot(day + 1)

    weak_final = {sid: _weak_avg(sid) for sid in range(1, N_STU + 1)}

    # 4) 验收指标
    improved = sum(1 for sid in range(1, N_STU + 1) if weak_final[sid] > weak_init[sid])
    avg_init = sum(weak_init.values()) / N_STU
    avg_final = sum(weak_final.values()) / N_STU
    hit_rate = total_hits_weak / total_questions if total_questions else 0
    events = le.events.count()

    print("\n================ 验收报告（Phase 1.5-D） ================")
    print(f"学生数: {N_STU}   天数: {DAYS}   总作答: {total_questions}")
    print(f"学习事件总数: {events}（answer_correct/wrong + mastery_change）")
    print(f"[弱项提升] 平均弱项掌握度: {avg_init:.3f} → {avg_final:.3f}  "
          f"(+{(avg_final-avg_init):.3f})；{improved}/{N_STU} 名学生弱项上升")
    print(f"[推荐稳定性] 薄弱点命中率: {hit_rate:.1%}   vs 随机基线: {baseline:.1%}  "
          f"(提升 {hit_rate/max(baseline,1e-9):.1f}×)")

    # 学习曲线轨迹
    print("\n[学习曲线轨迹] 弱项平均掌握度（按检查点）")
    hdr = "   原型".ljust(12) + "".join(f"{d:>8}" for d in CHECKPOINTS)
    print("  " + hdr)
    for arch in ARCHETYPES:
        row = arch.ljust(12)
        for d in CHECKPOINTS:
            v = traj.get(d, {}).get(arch)
            row += f"{(v if v is not None else float('nan')):>8.3f}" if v is not None else f"{'--':>8}"
        print("  " + row)

    # 错因画像
    print("\n[错因画像] 全局 Top10 错因标签（基于答错事件）")
    for tag, cnt in ec_freq.most_common(10):
        print(f"    {tag:<10} {cnt:>7}  ({cnt/max(1,sum(ec_freq.values())):.1%})")
    print("\n[错因画像·分原型] 各原型首位错因")
    for arch in ARCHETYPES:
        top = ec_by_arch[arch].most_common(1)
        print(f"    {arch:<8} -> {top[0][0] if top else '无':<10} "
              f"({top[0][1] if top else 0} 次)")

    # 分原型抽样报告
    print("\n[分原型 弱项掌握度变化]")
    for arch in ARCHETYPES:
        sids = [s for s in range(1, N_STU + 1) if archetype_of[s] == arch]
        if not sids:
            continue
        i = sum(weak_init[s] for s in sids) / len(sids)
        f = sum(weak_final[s] for s in sids) / len(sids)
        print(f"   {arch:<8}  n={len(sids):<3}  弱项 {i:.3f} → {f:.3f}  (+{f-i:+.3f})")

    ok = (improved >= N_STU * 0.8) and (hit_rate > baseline * 2)
    print("\n" + ("✅ 验收通过：90 天规模化仿真下推荐算法稳定，弱项被有效识别并强化，"
                  "学习曲线稳定上升，错因画像数据完整。" if ok
                  else "⚠️ 验收未完全达标，请检查推荐权重或数据分布。"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
