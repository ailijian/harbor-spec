from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


class HarborDB:
    """Harbor 索引的高性能存储后端（SQLite）。

    功能:
      - 以 SQLite 替代 JSON 索引，支持 O(1) 级内存占用与 WAL 并发读取。
      - 提供文件级元数据与 L3 契约条目的插入/更新/查询接口。
      - 支持从旧版 `.harbor/cache/l3_index.json` 迁移到 `harbor.db`。

    使用场景:
      - IndexBuilder 流式写入解析结果。
      - SyncEngine 基于 mtime 的快速跳过与按文件对比。

    依赖:
      - sqlite3（标准库）

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: once

    Args:
      db_path (Optional[Path]): 数据库文件路径，默认 `.harbor/cache/harbor.db`。
      project_root (Optional[Path]): 项目根目录，用于路径归一化，默认 `Path.cwd()`。

    Raises:
      IOError: 当数据库文件不可写或初始化失败。
    """

    def __init__(self, db_path: Optional[Path] = None, project_root: Optional[Path] = None) -> None:
        self.root = (project_root or Path.cwd()).resolve()
        self.db_path = (db_path or (Path(".harbor") / "cache" / "harbor.db")).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.conn = sqlite3.connect(str(self.db_path), isolation_level=None, check_same_thread=False)
        except Exception as ex:
            raise IOError(f"failed to open sqlite database: {ex}")
        self.conn.row_factory = sqlite3.Row
        self._apply_pragmas()
        self._ensure_schema()

    def _apply_pragmas(self) -> None:
        cur = self.conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    def _ensure_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
              path TEXT PRIMARY KEY,
              last_modified REAL,
              status TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
              id TEXT PRIMARY KEY,
              file_path TEXT NOT NULL,
              signature_hash TEXT,
              body_hash TEXT,
              contract_hash TEXT,
              meta TEXT,
              FOREIGN KEY(file_path) REFERENCES files(path) ON DELETE CASCADE
            )
            """
        )
        cur.close()

    @contextmanager
    def transaction(self):
        """事务上下文管理器（单文件原子写入）。

        功能:
          - 开启 `BEGIN IMMEDIATE`，确保写入原子性。
          - 正常结束提交，异常时回滚。

        使用场景:
          - IndexBuilder 在处理单个文件时批量 upsert。

        依赖:
          - sqlite3 事务

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: once
        """
        cur = self.conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            yield
            cur.execute("COMMIT")
        except Exception:
            cur.execute("ROLLBACK")
            raise
        finally:
            cur.close()

    def _posix_rel(self, path: str | Path) -> str:
        p = Path(path)
        try:
            rel = p.resolve().relative_to(self.root)
        except Exception:
            rel = p.resolve()
        s = rel.as_posix()
        return s.replace("\\", "/")

    def migrate_from_json(self, json_path: Path) -> bool:
        """从旧版 JSON 索引迁移到 SQLite。

        功能:
          - 读取 `.harbor/cache/l3_index.json`，导入 `files` 与 `entries`。
          - 成功后将旧文件重命名为备份。

        使用场景:
          - 项目升级到 v1.0.2 的 SQLite 存储后端时的兼容迁移。

        依赖:
          - sqlite3
          - json

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: once

        Args:
          json_path (Path): 旧版索引文件路径。

        Returns:
          bool: 若迁移发生且成功，返回 True；否则返回 False。
        """
        jp = Path(json_path)
        if not jp.exists():
            return False
        data: Dict[str, Any]
        try:
            data = json.loads(jp.read_text(encoding="utf-8"))
        except Exception:
            return False
        files = data.get("files", {}) or {}
        if not files:
            return False
        with self.transaction():
            for fp, meta in files.items():
                mtime = float(meta.get("mtime", 0.0))
                path_posix = self._posix_rel(fp)
                self.upsert_file(path_posix, mtime, "indexed")
                items = meta.get("items", []) or []
                for it in items:
                    entry_obj = {
                        "id": it.get("id"),
                        "file_path": path_posix,
                        "signature_hash": it.get("signature_hash"),
                        "body_hash": it.get("body_hash"),
                        "contract_hash": it.get("contract_hash"),
                        "meta": {
                            "name": it.get("name"),
                            "scope": it.get("scope"),
                            "strictness": it.get("strictness"),
                            "lineno": it.get("lineno"),
                            "qualified_name": it.get("qualified_name"),
                            "docstring_raw_hash": it.get("docstring_raw_hash"),
                        },
                    }
                    self.upsert_entry(entry_obj)
        try:
            ts = time.strftime("%Y%m%d%H%M%S", time.localtime())
            jp.rename(jp.with_name(f"l3_index.json.bak-{ts}"))
        except Exception:
            # 迁移成功但重命名失败不视为致命错误
            pass
        return True

    def upsert_file(self, path: str | Path, mtime: float, status: str) -> None:
        """插入或更新文件记录。

        功能:
          - 以 `path` 为主键写入/更新文件的 `last_modified/status`。

        使用场景:
          - 索引构建阶段记录文件快照。

        依赖:
          - sqlite3 UPSERT

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: once

        Args:
          path (str|Path): 文件路径（存储为项目根相对 POSIX）。
          mtime (float): 磁盘修改时间戳。
          status (str): indexed|skipped|error。
        """
        p = self._posix_rel(path)
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO files(path, last_modified, status)
            VALUES(?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
              last_modified=excluded.last_modified,
              status=excluded.status
            """,
            (p, float(mtime), status),
        )
        cur.close()

    def upsert_entry(self, entry_obj: Dict[str, Any]) -> None:
        """插入或更新函数条目。

        功能:
          - 以 `id` 为主键写入/更新 `signature/body/contract/meta`。

        使用场景:
          - 单文件事务中批量写入解析条目。

        依赖:
          - sqlite3 UPSERT

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: once

        Args:
          entry_obj (Dict[str, Any]): 条目对象，包含必要字段。
        """
        eid = entry_obj.get("id")
        fp = self._posix_rel(entry_obj.get("file_path"))
        sig = entry_obj.get("signature_hash")
        body = entry_obj.get("body_hash")
        contract = entry_obj.get("contract_hash")
        meta = json.dumps(entry_obj.get("meta") or {}, ensure_ascii=False)
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO entries(id, file_path, signature_hash, body_hash, contract_hash, meta)
            VALUES(?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              file_path=excluded.file_path,
              signature_hash=excluded.signature_hash,
              body_hash=excluded.body_hash,
              contract_hash=excluded.contract_hash,
              meta=excluded.meta
            """,
            (eid, fp, sig, body, contract, meta),
        )
        cur.close()

    def get_file(self, path: str | Path) -> Optional[Dict[str, Any]]:
        """查询单文件记录。

        功能:
          - 返回 `path/last_modified/status`，用于增量跳过。

        使用场景:
          - SyncEngine 快速检查阶段。

        依赖:
          - sqlite3 查询

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only
        """
        p = self._posix_rel(path)
        cur = self.conn.cursor()
        cur.execute("SELECT path, last_modified, status FROM files WHERE path = ?", (p,))
        row = cur.fetchone()
        cur.close()
        if not row:
            return None
        return {"path": row["path"], "last_modified": row["last_modified"], "status": row["status"]}

    def get_file_entries(self, path: str | Path) -> List[Dict[str, Any]]:
        """查询指定文件的所有条目。

        功能:
          - 返回该文件下的所有 L3 条目与哈希。

        使用场景:
          - 按文件对比变更。

        依赖:
          - sqlite3 查询

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only
        """
        p = self._posix_rel(path)
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, file_path, signature_hash, body_hash, contract_hash, meta FROM entries WHERE file_path = ?",
            (p,),
        )
        rows = cur.fetchall()
        cur.close()
        out: List[Dict[str, Any]] = []
        for r in rows or []:
            meta = {}
            try:
                meta = json.loads(r["meta"] or "{}")
            except Exception:
                meta = {}
            out.append(
                {
                    "id": r["id"],
                    "file_path": r["file_path"],
                    "signature_hash": r["signature_hash"],
                    "body_hash": r["body_hash"],
                    "contract_hash": r["contract_hash"],
                    "meta": meta,
                }
            )
        return out

    def get_all_files(self) -> List[Tuple[str, float]]:
        """列出所有已索引文件及其 mtime。

        功能:
          - 返回 `(path, last_modified)` 列表，便于快速 Diff。

        使用场景:
          - 缺失文件的检测与清理。

        依赖:
          - sqlite3 查询

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only
        """
        cur = self.conn.cursor()
        cur.execute("SELECT path, last_modified FROM files")
        rows = cur.fetchall()
        cur.close()
        return [(r["path"], r["last_modified"]) for r in rows or []]

    def purge_missing(self, current_paths: Iterable[str | Path]) -> int:
        """删除 DB 中存在但磁盘已缺失的文件记录。

        功能:
          - 基于当前扫描得到的文件集合，清理 DB 中的幽灵项。

        使用场景:
          - SyncEngine 扫描结束后的清理阶段。

        依赖:
          - sqlite3

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: once

        Args:
          current_paths (Iterable[str|Path]): 本次扫描得到的文件路径集合。

        Returns:
          int: 删除的记录数量。
        """
        keep = set(self._posix_rel(p) for p in current_paths)
        all_files = [p for p, _ in self.get_all_files()]
        to_delete = [p for p in all_files if p not in keep]
        if not to_delete:
            return 0
        cur = self.conn.cursor()
        cnt = 0
        try:
            cur.execute("BEGIN IMMEDIATE")
            for p in to_delete:
                cur.execute("DELETE FROM files WHERE path = ?", (p,))
                cnt += cur.rowcount or 0
            cur.execute("COMMIT")
        except Exception:
            cur.execute("ROLLBACK")
            raise
        finally:
            cur.close()
        return cnt
