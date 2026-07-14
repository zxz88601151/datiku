# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""SmartStudy OS —— 数据访问层（Data Manager）。

职责：
- 管理 SQLite 连接（单文件，按表前缀逻辑分域）。
- 统一使用参数化查询，杜绝 SQL 拼接注入（符合安全编码规范）。
- 提供建表 / 迁移 / 基础 CRUD 能力，供四个引擎共享。

设计：引擎层不直接写 SQL，而是通过本模块的 typed 方法获取数据访问能力，
从而保证「知识点 / 学习状态 / 题库」三引擎共享同一套安全、一致的数据底座。
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

import config.settings as cfg


def _connect(db_path: Path) -> sqlite3.Connection:
    """建立连接并开启外键约束与行工厂。"""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


class DataManager:
    """SQLite 数据管理器：连接池单例 + 参数化查询封装。"""

    def __init__(self, db_path: Path = cfg.DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = _connect(self.db_path)
        self._auto_commit = True
        self.init_schema()

    # ---- 生命周期 -------------------------------------------------------
    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "DataManager":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # ---- Schema（冻结版架构 v1.0 四域表） ------------------------------
    def init_schema(self) -> None:
        """创建全部表（IF NOT EXISTS，幂等可重复调用）。"""
        cur = self._conn.cursor()
        cur.executescript(
            """
            -- 用户域（学生 / 家长）
            CREATE TABLE IF NOT EXISTS user (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                grade       TEXT,
                school      TEXT,
                guardian    TEXT,            -- 监护人（未成年用户合规字段）
                nickname    TEXT DEFAULT '',
                school_year TEXT DEFAULT '',
                target      TEXT DEFAULT '', -- 如 "中考" / "竞赛" / "日常提升"
                subjects    TEXT DEFAULT '[]', -- JSON: ["数学","英语"]
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_goal (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                subject     TEXT NOT NULL DEFAULT '数学',
                target_score INTEGER DEFAULT 0,
                current_score INTEGER DEFAULT 0,
                deadline    TEXT,             -- "2027-06" 中考月
                priority    INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS user_preference (
                user_id             INTEGER PRIMARY KEY,
                study_time_weekday  TEXT DEFAULT '19:00-21:00',
                difficulty_preference INTEGER DEFAULT 2,  -- 1-5
                learning_style      TEXT DEFAULT 'standard',
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
            );

            -- 知识图谱域
            CREATE TABLE IF NOT EXISTS kg_node (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                subject     TEXT NOT NULL,
                grade       TEXT NOT NULL,
                parent_id   INTEGER,
                difficulty  INTEGER DEFAULT 1,        -- 1-5
                mastery     REAL    DEFAULT 0.0,       -- 0-1 缓存值
                importance  REAL    DEFAULT 0.5,       -- 0-1 重要程度
                relation    TEXT,                     -- JSON: 关联节点 id 列表
                content     TEXT,
                formula     TEXT,
                examples    TEXT,
                pitfalls    TEXT,                     -- 易错点
                FOREIGN KEY (parent_id) REFERENCES kg_node(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_kg_parent ON kg_node(parent_id);
            CREATE INDEX IF NOT EXISTS idx_kg_sg ON kg_node(subject, grade);

            -- 题库域
            CREATE TABLE IF NOT EXISTS q_question (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                subject     TEXT NOT NULL,
                grade       TEXT NOT NULL,
                type        TEXT NOT NULL,
                difficulty  INTEGER DEFAULT 1,
                content     TEXT NOT NULL,
                answer      TEXT,
                analysis    TEXT,
                knowledge_relation TEXT            -- JSON: 绑定知识点 id 列表
            );
            CREATE INDEX IF NOT EXISTS idx_q_sg ON q_question(subject, grade);

            CREATE TABLE IF NOT EXISTS q_option (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                label       TEXT,                   -- A/B/C/D
                text        TEXT,
                is_correct  INTEGER DEFAULT 0,
                FOREIGN KEY (question_id) REFERENCES q_question(id) ON DELETE CASCADE
            );

            -- 学习状态域
            CREATE TABLE IF NOT EXISTS learn_state (
                student_id  INTEGER NOT NULL,
                knowledge_id INTEGER NOT NULL,
                mastery     REAL DEFAULT 0.0,
                wrong_count INTEGER DEFAULT 0,
                last_time   TEXT,
                learning_curve TEXT,               -- JSON: [{t, mastery}]
                PRIMARY KEY (student_id, knowledge_id),
                FOREIGN KEY (student_id) REFERENCES user(id) ON DELETE CASCADE,
                FOREIGN KEY (knowledge_id) REFERENCES kg_node(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS learn_record (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                result      TEXT,                   -- correct / wrong
                spent_sec   INTEGER DEFAULT 0,
                created_at  TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_lr_stu ON learn_record(student_id);

            CREATE TABLE IF NOT EXISTS learn_wrong (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                wrong_reason TEXT,
                count       INTEGER DEFAULT 1,
                mastery     REAL DEFAULT 0.0,
                resolved    INTEGER DEFAULT 0,      -- 0 未掌握 / 1 已掌握
                last_time   TEXT,
                UNIQUE (student_id, question_id)
            );
            CREATE INDEX IF NOT EXISTS idx_lw_stu ON learn_wrong(student_id);

            CREATE TABLE IF NOT EXISTS achievement (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  INTEGER NOT NULL,
                type        TEXT,
                name        TEXT,
                value       TEXT,
                created_at  TEXT NOT NULL
            );

            -- 学习事件日志（Phase 1.5-C）：AI 老师与学习画像的核心数据来源
            CREATE TABLE IF NOT EXISTS learning_event (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id   INTEGER NOT NULL,
                event_type   TEXT NOT NULL,          -- answer_correct / answer_wrong / session / review / mastery_change
                knowledge_id INTEGER,
                before_score REAL,
                after_score  REAL,
                payload      TEXT,                    -- JSON：辅助信息（如题号、难度、推荐分）
                timestamp    TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES user(id) ON DELETE CASCADE,
                FOREIGN KEY (knowledge_id) REFERENCES kg_node(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_le_stu ON learning_event(student_id);
            CREATE INDEX IF NOT EXISTS idx_le_kw ON learning_event(knowledge_id);
            CREATE INDEX IF NOT EXISTS idx_le_ts ON learning_event(timestamp);

            -- 学习快照（Phase 2.2 驾驶舱趋势数据源，避免每次重算历史事件）
            CREATE TABLE IF NOT EXISTS learning_snapshot (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  INTEGER NOT NULL,
                date        TEXT NOT NULL,
                subject     TEXT NOT NULL DEFAULT '数学',
                overall_mastery  REAL DEFAULT 0.0,
                weak_points TEXT,                   -- JSON: {knowledge_id: mastery}
                study_minutes   INTEGER DEFAULT 0,
                UNIQUE (student_id, date)
            );
            CREATE INDEX IF NOT EXISTS idx_ls_date ON learning_snapshot(student_id, date);

            -- 错因诊断报告（Phase 2.3 AI 错因诊断中心）
            CREATE TABLE IF NOT EXISTS diagnosis_report (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  INTEGER NOT NULL,
                session_id  TEXT,
                summary     TEXT,                    -- JSON: findings list
                confidence  REAL DEFAULT 0.0,
                created_at  TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_dr_stu ON diagnosis_report(student_id);

            -- 恢复任务（Phase 2.3 补救执行跟踪）
            CREATE TABLE IF NOT EXISTS recovery_task (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  INTEGER NOT NULL,
                report_id   INTEGER,
                finding_id  TEXT,
                finding_name TEXT,
                source_knowledge_id  INTEGER,
                target_knowledge_ids TEXT,           -- JSON: [id,...]
                question_ids        TEXT,            -- JSON: [id,...]
                pre_mastery_before  REAL DEFAULT 0.0,
                post_mastery        REAL DEFAULT 0.0,
                status      TEXT DEFAULT 'pending',  -- pending / in_progress / completed
                created_at  TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_rt_stu ON recovery_task(student_id);

            -- AI 老师辅导记忆（Phase 2.5）
            CREATE TABLE IF NOT EXISTS tutor_memory (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  INTEGER NOT NULL,
                topic       TEXT NOT NULL,
                summary     TEXT DEFAULT '',
                created_at  TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_tm_stu ON tutor_memory(student_id);

            CREATE TABLE IF NOT EXISTS tutor_chat_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  INTEGER NOT NULL,
                question_type TEXT DEFAULT 'general',
                question    TEXT NOT NULL,
                response    TEXT NOT NULL,
                context_snapshot TEXT,               -- JSON: 当时的上下文快照
                created_at  TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_tcl_stu ON tutor_chat_log(student_id);

            -- 成长系统（Phase 2.6 RPG 成长引擎）
            CREATE TABLE IF NOT EXISTS user_growth (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  INTEGER NOT NULL UNIQUE,
                level       INTEGER DEFAULT 1,
                xp          INTEGER DEFAULT 0,       -- 当前等级内 XP
                total_xp    INTEGER DEFAULT 0,       -- 累计 XP
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS skill_state (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  INTEGER NOT NULL,
                skill_id    TEXT NOT NULL,
                skill_name  TEXT NOT NULL,
                level       INTEGER DEFAULT 1,
                progress    REAL DEFAULT 0.0,         -- 0-1 升级进度
                updated_at  TEXT NOT NULL,
                UNIQUE (student_id, skill_id)
            );

            CREATE TABLE IF NOT EXISTS achievement_record (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id    INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                achievement_name TEXT NOT NULL,
                unlock_time   TEXT NOT NULL,
                UNIQUE (student_id, achievement_id)
            );

            CREATE TABLE IF NOT EXISTS daily_task (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  INTEGER NOT NULL,
                task_date   TEXT NOT NULL,
                task_type   TEXT NOT NULL,
                description TEXT DEFAULT '',
                target      INTEGER DEFAULT 1,
                progress    INTEGER DEFAULT 0,
                reward_xp   INTEGER DEFAULT 10,
                status      TEXT DEFAULT 'pending',  -- pending / completed / claimed
                UNIQUE (student_id, task_date, task_type)
            );
            """
        )
        self._conn.commit()
        self._migrate()

    # ---- Schema 迁移（向后兼容，保留已导入数据） --------------------
    def _migrate(self) -> None:
        """为已存在的数据库补齐 Phase 1.5-B 新增列（幂等）。"""
        kg_cols = {
            "summary": "TEXT", "node_type": "TEXT", "important": "INTEGER",
            "predecessor": "TEXT", "successor": "TEXT", "errors": "TEXT",
            "formula_list": "TEXT",
        }
        self._add_columns("kg_node", kg_cols)
        self._add_columns("q_question", {"exam_weight": "INTEGER", "error_tags": "TEXT", "ktext": "TEXT"})
        self._add_columns("user", {"nickname": "TEXT", "school_year": "TEXT",
                                   "target": "TEXT", "subjects": "TEXT"})

    def _add_columns(self, table: str, cols: dict) -> None:
        existing = {r["name"] for r in self._conn.execute(f"PRAGMA table_info({table})")}
        for col, ctype in cols.items():
            if col not in existing:
                self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ctype}")
        self._conn.commit()

    # ---- 通用安全查询封装（参数化，禁止字符串拼接） --------------------
    def execute(self, sql: str, params: Sequence[Any] = ()) -> sqlite3.Cursor:
        cur = self._conn.execute(sql, tuple(params))
        if self._auto_commit:
            self._conn.commit()
        return cur

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[dict]:
        """返回行字典列表（只读查询）。"""
        cur = self._conn.execute(sql, tuple(params))
        return [dict(r) for r in cur.fetchall()]

    def query_one(self, sql: str, params: Sequence[Any] = ()) -> Optional[dict]:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def insert(self, table: str, row: dict) -> int:
        """通用插入，返回 lastrowid。列名白名单由调用方保证为可信标识符。"""
        cols = list(row.keys())
        placeholders = ", ".join("?" for _ in cols)
        col_sql = ", ".join(cols)
        sql = f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})"
        cur = self._conn.execute(sql, tuple(row[c] for c in cols))
        if self._auto_commit:
            self._conn.commit()
        return cur.lastrowid

    def insert_nc(self, table: str, row: dict) -> int:
        """插入但不提交（需在 transaction() 上下文中使用），返回 lastrowid。"""
        cols = list(row.keys())
        placeholders = ", ".join("?" for _ in cols)
        col_sql = ", ".join(cols)
        sql = f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})"
        cur = self._conn.execute(sql, tuple(row[c] for c in cols))
        return cur.lastrowid

    def executemany_nc(self, sql: str, params_seq: Sequence[Sequence[Any]]) -> None:
        """批量执行不提交（需在 transaction() 上下文中使用）。"""
        self._conn.executemany(sql, [tuple(p) for p in params_seq])

    def update(self, table: str, row: dict, where: str, where_params: Sequence[Any]) -> None:
        cols = [c for c in row.keys() if c not in ("id",)]
        if not cols:
            return
        set_sql = ", ".join(f"{c} = ?" for c in cols)
        sql = f"UPDATE {table} SET {set_sql} WHERE {where}"
        self._conn.execute(sql, tuple(row[c] for c in cols) + tuple(where_params))
        if self._auto_commit:
            self._conn.commit()

    def transaction(self):
        """事务上下文：进入后所有写操作不自动提交，退出时统一提交。

        用于规模化批量装载 / 仿真，将数千次写入合并为单次提交，
        避免逐条 COMMIT 带来的性能瓶颈（符合可用性与成本安全）。
        """
        return _Transaction(self)

    # ---- JSON 字段辅助（relation / curve / knowledge_relation） --------
    @staticmethod
    def dumps(obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=False)

    @staticmethod
    def loads(text: Optional[str]) -> Any:
        if not text:
            return []
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return []


class _Transaction:
    """事务上下文管理器，配合 DataManager.transaction() 使用。"""

    def __init__(self, dm: "DataManager"):
        self.dm = dm
        self._prev_level = None

    def __enter__(self) -> "DataManager":
        self._prev_level = self.dm._conn.isolation_level
        # 保留默认延迟事务模式（isolation_level 不变），仅关闭自动提交。
        # 注意：切勿将 isolation_level 设为 None —— 那会让 SQLite 进入
        # autocommit 模式，导致事务块内每条语句都立即落盘 fsync，
        # 规模化写场景（万级装载 / 仿真）性能将劣化数百倍。
        self.dm._auto_commit = False
        return self.dm

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is None:
                self.dm._conn.commit()
            else:
                self.dm._conn.rollback()
        finally:
            self.dm._conn.isolation_level = self._prev_level
            self.dm._auto_commit = True
