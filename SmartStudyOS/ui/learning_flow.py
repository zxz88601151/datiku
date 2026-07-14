# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""学习流（Phase 2.1 核心闭环）。

内部 QStackedWidget 五步骤：

  0 — 练习（逐题作答 → 提交 → 即时反馈）
  1 — 小结（正确/错误分布 + 准确率 + 用时）
  2 — 错因分析（按错误标签分布 + 薄弱知识点诊断）
  3 — 补救练习（基于薄弱知识点的再次组卷练习）
  4 — 完成奖励（统计 + 鼓励 + 返回首页）
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QProgressBar, QPushButton, QRadioButton, QStackedWidget, QTextBrowser,
    QVBoxLayout, QWidget,
)

from .app_context import AppContext
from services.learning_service import ExerciseService
from core.learning_session import LearningSession
from core.ai_engine.base import TutorRequest

# ---- 页面常量 ----
_PG_PRACTICE = 0   # 练习
_PG_SUMMARY = 1    # 小结
_PG_ANALYSIS = 2   # 错因分析
_PG_RECOVERY = 3   # 补救练习
_PG_REWARD = 4     # 完成奖励


class _Card(QFrame):
    """圆角卡片。"""

    def __init__(self, title: str = ""):
        super().__init__()
        self.setStyleSheet("""
            _Card { background: #ffffff; border: 1px solid #e1e4e8;
                    border-radius: 12px; }
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 16, 20, 16)
        self._layout.setSpacing(8)
        if title:
            lbl = QLabel(title)
            lbl.setStyleSheet("font-size:15px; font-weight:600; color:#24292f;")
            self._layout.addWidget(lbl)


class _ProgressBar(QProgressBar):
    """扁平进度条。"""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(6)
        self.setTextVisible(False)
        self.setStyleSheet("""
            QProgressBar { background: #eaeef2; border: none; border-radius: 3px; }
            QProgressBar::chunk { background: #1f6feb; border-radius: 3px; }
        """)


# ===================================================================
#  学习流主视图
# ===================================================================
class LearningFlow(QWidget):
    """学习流主视图。由外部调用 start_session() 启动。"""

    def __init__(self, ctx: AppContext, on_go_home: callable, on_show_diagnosis: callable = None):
        super().__init__()
        self.ctx = ctx
        self._on_go_home = on_go_home
        self._on_show_diagnosis = on_show_diagnosis
        self._svc = ExerciseService(ctx.dm, ctx.bank, ctx.le, ctx.kg)
        self.sess: Optional[LearningSession] = None
        self._entry_ts: float = 0.0
        self._feedback_showing: bool = False
        self._recovery_session: Optional[LearningSession] = None
        self._recovery_records: list = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self._stack = QStackedWidget()
        root.addWidget(self._stack)

        self._build_practice_page()
        self._build_summary_page()
        self._build_analysis_page()
        self._build_recovery_page()
        self._build_reward_page()

    # ---- 构建各页面 ------------------------------------------------

    def _make_light_btn(self, text: str, callback, primary=False):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        if primary:
            btn.setStyleSheet("""
                QPushButton { background:#1f6feb; color:#fff; font-size:15px;
                              font-weight:600; border:none; border-radius:8px;
                              padding:10px 28px; min-height:18px; }
                QPushButton:hover { background:#1857c4; }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton { background:#f3f5f9; color:#24292f; font-size:14px;
                              border:1px solid #d0d7de; border-radius:8px;
                              padding:8px 20px; }
                QPushButton:hover { background:#e8eaef; }
            """)
        btn.clicked.connect(callback)
        return btn

    # ---- 练习页面（PG 0）----------------------------------------

    def _build_practice_page(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(32, 20, 32, 20)
        root.setSpacing(12)

        # 顶部：进度条 + 退出按钮
        top_row = QHBoxLayout()
        progress_col = QVBoxLayout()
        self.pb_progress = _ProgressBar()
        progress_col.addWidget(self.pb_progress)

        # 进度文字
        self.lbl_progress = QLabel("准备中…")
        self.lbl_progress.setStyleSheet("font-size:13px; color:#656d76;")
        progress_col.addWidget(self.lbl_progress)
        top_row.addLayout(progress_col, 1)

        self.btn_exit = QPushButton("✕ 退出")
        self.btn_exit.setFixedSize(60, 26)
        self.btn_exit.setCursor(Qt.PointingHandCursor)
        self.btn_exit.setStyleSheet("""
            QPushButton { background:#ffeef0; color:#cf222e; border:1px solid #cf222e;
                          border-radius:4px; font-size:11px; }
            QPushButton:hover { background:#cf222e; color:#fff; }
        """)
        self.btn_exit.clicked.connect(self._on_exit)
        top_row.addWidget(self.btn_exit)
        root.addLayout(top_row)

        # 题目类型/难度
        self.lbl_meta = QLabel("")
        self.lbl_meta.setStyleSheet("font-size:12px; color:#656d76;")
        root.addWidget(self.lbl_meta)

        # 题目内容（可滚动）
        self.txt_question = QTextBrowser()
        self.txt_question.setOpenExternalLinks(False)
        self.txt_question.setStyleSheet("""
            QTextBrowser { background:#f6f8fa; border:1px solid #d0d7de;
                           border-radius:8px; padding:16px; font-size:15px;
                           color:#24292f; }
        """)
        self.txt_question.setMinimumHeight(100)
        root.addWidget(self.txt_question, 1)

        # 答题区
        self.answer_area = QVBoxLayout()
        root.addLayout(self.answer_area)

        # 选项组（选择题用）
        self.answer_group = QButtonGroup(self)
        self.input_text = QLineEdit()
        self.input_text.setPlaceholderText("在此输入答案…")
        self.input_text.setStyleSheet("""
            QLineEdit { border:1px solid #d0d7de; border-radius:6px;
                        padding:10px 12px; font-size:14px; }
        """)
        self.answer_area.addWidget(self.input_text)

        # 提交按钮
        self.btn_submit = self._make_light_btn("提交", self._on_submit, primary=True)
        root.addWidget(self.btn_submit)

        # 反馈区（提交后显示）
        self.feedback_card = _Card()
        self.feedback_lbl = QLabel("")
        self.feedback_lbl.setWordWrap(True)
        self.feedback_lbl.setStyleSheet("font-size:14px; color:#24292f;")
        self.feedback_card._layout.addWidget(self.feedback_lbl)
        self.ai_reply = QLabel("")
        self.ai_reply.setWordWrap(True)
        self.ai_reply.setStyleSheet("font-size:13px; color:#656d76; padding:4px 0;")
        self.feedback_card._layout.addWidget(self.ai_reply)
        self.feedback_card.hide()
        root.addWidget(self.feedback_card)

        # 下一题按钮（提交后显示）
        self.btn_next = self._make_light_btn("下一题  →", self._on_next)
        self.btn_next.hide()
        root.addWidget(self.btn_next)

        self._stack.addWidget(page)

    # ---- 小结页面（PG 1）----------------------------------------

    def _build_summary_page(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(32, 40, 32, 20)
        root.setAlignment(Qt.AlignCenter)

        title_row = QHBoxLayout()
        self.lbl_summary_title = QLabel("🎉 本阶段练习完成")
        self.lbl_summary_title.setStyleSheet("font-size:22px; font-weight:700; color:#24292f;")
        title_row.addWidget(self.lbl_summary_title, 1)
        exit_sm = QPushButton("退出")
        exit_sm.setFixedSize(50, 22)
        exit_sm.setCursor(Qt.PointingHandCursor)
        exit_sm.setStyleSheet("""
            QPushButton { background:#ffeef0; color:#cf222e; border:1px solid #cf222e;
                          border-radius:4px; font-size:10px; }
            QPushButton:hover { background:#cf222e; color:#fff; }
        """)
        exit_sm.clicked.connect(self._on_exit)
        title_row.addWidget(exit_sm)
        root.addLayout(title_row)

        self.lbl_summary_stats = QLabel("")
        self.lbl_summary_stats.setStyleSheet("font-size:15px; color:#656d76; margin:8px 0;")
        root.addWidget(self.lbl_summary_stats)

        btn = self._make_light_btn("查看错因分析  →", lambda: self._stack.setCurrentIndex(_PG_ANALYSIS), primary=True)
        root.addWidget(btn)
        root.addStretch(1)
        self._stack.addWidget(page)

    # ---- 错因分析页面（PG 2）------------------------------------

    def _build_analysis_page(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(32, 20, 32, 20)
        root.setSpacing(12)

        title_row = QHBoxLayout()
        title = QLabel("🔍 错因分析")
        title.setStyleSheet("font-size:20px; font-weight:700; color:#24292f;")
        title_row.addWidget(title, 1)
        exit_an = QPushButton("退出")
        exit_an.setFixedSize(50, 22)
        exit_an.setCursor(Qt.PointingHandCursor)
        exit_an.setStyleSheet("""
            QPushButton { background:#ffeef0; color:#cf222e; border:1px solid #cf222e;
                          border-radius:4px; font-size:10px; }
            QPushButton:hover { background:#cf222e; color:#fff; }
        """)
        exit_an.clicked.connect(self._on_exit)
        title_row.addWidget(exit_an)
        root.addLayout(title_row)

        self.analysis_content = QVBoxLayout()
        root.addLayout(self.analysis_content, 1)

        btn = self._make_light_btn("进入补救练习  →", self._on_start_recovery, primary=True)
        root.addWidget(btn)
        btn_skip = self._make_light_btn("跳过，查看完成奖励", lambda: self._stack.setCurrentIndex(_PG_REWARD))
        root.addWidget(btn_skip)
        self._stack.addWidget(page)

    # ---- 补救练习页面（PG 3）------------------------------------

    def _build_recovery_page(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(32, 20, 32, 20)
        root.setSpacing(12)

        title_row = QHBoxLayout()
        self.lbl_recovery_title = QLabel("📖 补救练习")
        self.lbl_recovery_title.setStyleSheet("font-size:20px; font-weight:700; color:#24292f;")
        title_row.addWidget(self.lbl_recovery_title, 1)
        exit_rv = QPushButton("退出")
        exit_rv.setFixedSize(50, 22)
        exit_rv.setCursor(Qt.PointingHandCursor)
        exit_rv.setStyleSheet("""
            QPushButton { background:#ffeef0; color:#cf222e; border:1px solid #cf222e;
                          border-radius:4px; font-size:10px; }
            QPushButton:hover { background:#cf222e; color:#fff; }
        """)
        exit_rv.clicked.connect(self._on_exit)
        title_row.addWidget(exit_rv)
        root.addLayout(title_row)

        self.lbl_recovery_sub = QLabel("基于你的错误，系统推荐以下练习：")
        self.lbl_recovery_sub.setStyleSheet("font-size:14px; color:#656d76;")
        root.addWidget(self.lbl_recovery_sub)

        self.recovery_scroll = QVBoxLayout()
        root.addLayout(self.recovery_scroll, 1)

        self.btn_recovery_done = self._make_light_btn("补救完成，查看奖励  →", self._on_recovery_done, primary=True)
        root.addWidget(self.btn_recovery_done)
        self.btn_recovery_skip = self._make_light_btn("跳过补救", lambda: self._stack.setCurrentIndex(_PG_REWARD))
        root.addWidget(self.btn_recovery_skip)
        self._stack.addWidget(page)

    # ---- 奖励页面（PG 4）----------------------------------------

    def _build_reward_page(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(32, 40, 32, 20)
        root.setAlignment(Qt.AlignCenter)

        title_row = QHBoxLayout()
        self.lbl_reward_title = QLabel("🏆 今日学习完成！")
        self.lbl_reward_title.setStyleSheet("font-size:24px; font-weight:700; color:#24292f;")
        title_row.addWidget(self.lbl_reward_title, 1)
        exit_rw = QPushButton("退出")
        exit_rw.setFixedSize(50, 22)
        exit_rw.setCursor(Qt.PointingHandCursor)
        exit_rw.setStyleSheet("""
            QPushButton { background:#ffeef0; color:#cf222e; border:1px solid #cf222e;
                          border-radius:4px; font-size:10px; }
            QPushButton:hover { background:#cf222e; color:#fff; }
        """)
        exit_rw.clicked.connect(self._on_exit)
        title_row.addWidget(exit_rw)
        root.addLayout(title_row)

        self.lbl_reward_detail = QLabel("")
        self.lbl_reward_detail.setStyleSheet("font-size:15px; color:#656d76; margin:8px 0;")
        root.addWidget(self.lbl_reward_detail)

        if self._on_show_diagnosis:
            diag_btn = self._make_light_btn("查看诊断报告  →", self._on_show_diagnosis)
            root.addWidget(diag_btn)
            root.addSpacing(6)

        btn = self._make_light_btn("返回首页", self._on_go_home, primary=True)
        root.addWidget(btn)
        root.addStretch(1)
        self._stack.addWidget(page)

    # ---- 启动会话 ------------------------------------------------

    def start_session(self, subject: str = "数学", grade: str = "七年级",
                      knowledge_ids=None):
        """开始一次新的学习流。"""
        self._recovery_session = None
        self._recovery_records = []
        self._feedback_showing = False

        sess = self._svc.create_practice(
            student_id=self.ctx.student_id,
            subject=subject, grade=grade, size=10,
            knowledge_ids=knowledge_ids,
        )
        self.sess = sess

        if not sess.questions:
            self._stack.setCurrentIndex(_PG_REWARD)
            self.lbl_reward_title.setText("📭 暂无题目")
            self.lbl_reward_detail.setText("当前学科/年级无可用题目，请先导入题库。")
            return

        self._render_question()

    def _render_question(self):
        """渲染当前题目到练习页。"""
        self._stack.setCurrentIndex(_PG_PRACTICE)
        self._feedback_showing = False
        self.feedback_card.hide()
        self.btn_next.hide()
        self.btn_submit.show()
        self.input_text.show()

        sess = self.sess
        q = sess.current_question
        if q is None:
            self._show_summary()
            return

        total = len(sess.questions)
        idx = sess.records.count(None)  # 未答数量
        # 实际当前题号 = len(records) + 1
        cur = len(sess.records) + 1
        self.pb_progress.setMaximum(total)
        self.pb_progress.setValue(cur - 1)
        self.lbl_progress.setText(sess.progress)
        self.lbl_meta.setText(f"{q.type}  ·  难度 {q.difficulty}/5")

        # 题目内容
        self.txt_question.setPlainText(q.content)

        # 答题区
        self._clear_layout(self.answer_area)

        # 移除之前添加的 input_text（它被 addWidget 了，不能重复添加）
        # 重新构建
        self.answer_group = QButtonGroup(self)
        if q.is_choice:
            self.input_text.hide()
            for opt in self.ctx.bank.get_options(q.id):
                rb = QRadioButton(f"{opt.label}. {opt.text}")
                rb.setProperty("label", opt.label)
                rb.setStyleSheet("font-size:14px; padding:4px 0; color:#24292f;")
                self.answer_group.addButton(rb)
                self.answer_area.addWidget(rb)
        else:
            self.input_text.show()
            self.input_text.clear()

        self.answer_area.addStretch(1)
        self._entry_ts = time.time()

    # ---- 提交答案 ------------------------------------------------

    def _on_submit(self):
        if self._feedback_showing or self.sess is None or self.sess.current_question is None:
            return

        q = self.sess.current_question
        if q.is_choice:
            checked = self.answer_group.checkedButton()
            if not checked:
                return
            ans = checked.property("label")
        else:
            ans = self.input_text.text().strip()
            if not ans:
                return

        # 提交到服务层（含 XP + 任务进度）
        rec = self._svc.submit_answer(self.sess, self._entry_ts, ans)
        correct = rec.correct

        # 显示反馈
        self._feedback_showing = True
        self.btn_submit.hide()
        self.feedback_card.show()
        self.btn_next.show()

        if correct:
            self.feedback_lbl.setText("✅ 答对了！")
            self.feedback_lbl.setStyleSheet("font-size:15px; font-weight:600; color:#1a7f37;")
            self.ai_reply.setText("")
        else:
            self.feedback_lbl.setText("❌ 答错了")
            self.feedback_lbl.setStyleSheet("font-size:15px; font-weight:600; color:#c0392b;")
            # AI 解释
            try:
                kid = q.knowledge_relation[0] if q.knowledge_relation else None
                req = TutorRequest(student_id=self.ctx.student_id, knowledge_id=kid)
                reply = self.ctx.tutor.evaluate(req, correct=False)
                self.ai_reply.setText(reply.content)
            except Exception:
                self.ai_reply.setText("")

            # 显示错因标签
            if rec.error_tags:
                tags_str = "  ·  ".join(rec.error_tags[:3])
                self.ai_reply.setText(self.ai_reply.text() + f"\n\n📌 错误类型：{tags_str}")

    def _on_next(self):
        """下一题。若已完成全部则进入小结页。"""
        has_more = self.sess.advance()
        if has_more:
            self._render_question()
        else:
            self._show_summary()

    # ---- 小结 ---------------------------------------------------

    def _show_summary(self):
        self._stack.setCurrentIndex(_PG_SUMMARY)
        report = self.sess.complete() if not self.sess.is_completed else self.sess.complete()

        total = report["total"]
        correct = report["correct"]
        wrong = report["wrong"]
        acc = report["accuracy"] * 100
        dur = report["total_duration_sec"]
        dur_str = f"{dur // 60} 分 {dur % 60} 秒"

        self.lbl_summary_stats.setText(
            f"正确 {correct} / {total} 题  ({acc:.0f}%)\n"
            f"用时 {dur_str}\n\n"
            f"{'🎯 表现不错！' if acc >= 70 else '💪 继续加油！'}"
        )

    # ---- 错因分析 -----------------------------------------------

    def _show_analysis(self):
        self._stack.setCurrentIndex(_PG_ANALYSIS)
        self._clear_layout(self.analysis_content)

        report = self.sess.complete()  # 幂等
        causes = report["error_causes"]

        if not causes:
            self.analysis_content.addWidget(QLabel("🎉 全部答对，无错因分析。"))
            return

        # 错因分布
        card = _Card("错误类型分布")
        for tag, cnt in sorted(causes.items(), key=lambda x: -x[1]):
            row = QHBoxLayout()
            lbl_tag = QLabel(tag)
            lbl_tag.setStyleSheet("font-size:13px; color:#24292f; min-width:80px;")
            row.addWidget(lbl_tag)
            pb = QProgressBar()
            pb.setMaximum(sum(causes.values()))
            pb.setValue(cnt)
            pb.setFixedHeight(6)
            pb.setTextVisible(False)
            pb.setStyleSheet("""
                QProgressBar { background:#eaeef2; border:none; border-radius:3px; }
                QProgressBar::chunk { background:#cf222e; border-radius:3px; }
            """)
            row.addWidget(pb, 1)
            lbl_cnt = QLabel(f"×{cnt}")
            lbl_cnt.setStyleSheet("font-size:12px; color:#656d76; min-width:30px;")
            row.addWidget(lbl_cnt)
            card._layout.addLayout(row)
        self.analysis_content.addWidget(card)

        # 薄弱知识点
        weak_ids = report.get("weak_knowledge_ids", [])
        if weak_ids:
            weak_card = _Card("📌 需要加强的知识点")
            for kid in weak_ids[:5]:
                kn = self.ctx.kg.get(kid)
                name = kn.name if kn else f"#{kid}"
                lbl = QLabel(f"  ·  {name}")
                lbl.setStyleSheet("font-size:13px; color:#656d76;")
                weak_card._layout.addWidget(lbl)
            self.analysis_content.addWidget(weak_card)

        self.analysis_content.addStretch(1)

    # ---- 补救练习 -----------------------------------------------

    def _on_start_recovery(self):
        """基于薄弱知识点生成补救练习。"""
        report = self.sess.complete()
        weak_ids = report.get("weak_knowledge_ids", [])
        if not weak_ids:
            self._stack.setCurrentIndex(_PG_REWARD)
            return

        # 生成 5 题补救练习
        recover_sess = LearningSession(self.ctx.bank, self.ctx.le, self.ctx.dm)
        recover_sess.create(
            student_id=self.ctx.student_id,
            subject=self.sess.subject or "数学",
            grade=self.sess.grade or "七年级",
            size=5,
            knowledge_ids=weak_ids,
        )
        self._recovery_session = recover_sess
        self._recovery_records = []

        # 渲染补救练习（简化版：一项一项展示）
        self._clear_layout(self.recovery_scroll)
        self.lbl_recovery_sub.setText("基于你的错误，系统推荐以下练习：")

        for i, q in enumerate(recover_sess.questions):
            card = _Card(f"补救 {i+1}")
            card._layout.addWidget(QLabel(q.content))
            card.setStyleSheet("""
                _Card { background:#fffbea; border:1px solid #d4a82c;
                        border-radius:8px; margin:2px 0; }
            """)
            lbl = QLabel(f"答案请自行对照  |  知识点：{', '.join(str(k) for k in (q.knowledge_relation or []))}")
            lbl.setStyleSheet("font-size:12px; color:#656d76;")
            card._layout.addWidget(lbl)
            self.recovery_scroll.addWidget(card)

        self._stack.setCurrentIndex(_PG_RECOVERY)

    def _on_recovery_done(self):
        self._stack.setCurrentIndex(_PG_REWARD)

    # ---- 中途退出 -----------------------------------------------

    def _on_exit(self):
        """用户中途退出学习流，返回首页。"""
        if self.sess and hasattr(self.sess, 'complete'):
            try:
                # 尝试保存已答题目记录
                from utils.logger import get_logger
                log = get_logger("learning_flow")
                log.info(f"user exited early: session={self.sess.session_id} "
                         f"answered={len(self.sess.records)}/{len(self.sess.questions)}")
            except Exception:
                pass
        self._on_go_home()

    # ---- 完成奖励 -----------------------------------------------

    def _show_reward(self):
        self._stack.setCurrentIndex(_PG_REWARD)
        if not self.sess:
            return

        result = self._svc.complete_practice(self.sess)
        report = result["session_report"]
        d_report = result["diagnosis_report"]

        acc = report["accuracy"] * 100
        dur = report["total_duration_sec"]
        dur_str = f"{dur // 60} 分 {dur % 60} 秒"
        medal = "🏆" if acc >= 80 else "⭐" if acc >= 60 else "💪"
        self.lbl_reward_title.setText(f"{medal} 今日学习完成！")

        diag_summary = ""
        if d_report and hasattr(d_report, 'findings') and d_report.findings:
            diag_summary = f"诊断发现 {len(d_report.findings)} 个错误模式" \
                           f"  ·  可信度 {d_report.confidence*100:.0f}%"

        self.lbl_reward_detail.setText(
            f"正确 {report['correct']} / {report['total']} 题  ({acc:.0f}%)"
            f"  ·  用时 {dur_str}\n"
            + (diag_summary + "\n" if diag_summary else "")
            + "继续坚持，每天进步一点点！"
        )

    # ---- 辅助 ---------------------------------------------------

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            w = layout.takeAt(0).widget()
            if w:
                w.deleteLater()
