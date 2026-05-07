from __future__ import annotations

import json
import os
import subprocess
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from harbor.core.workspace import load_workspace_config, load_workspace_paths, resolve_workspace_config_path


VISIBILITY_ORDER = {"internal": 0, "repo": 1, "public": 2}
TYPE_SET = {"feature", "bugfix", "refactor", "chore", "incident"}
IMPORTANCE_SET = {"trivial", "normal", "high", "critical"}
VISIBILITY_SET = set(VISIBILITY_ORDER.keys())


@dataclass
class DiaryEntry:
    ver: int
    ts: str
    author: str
    type: str
    importance: str
    visibility: str
    summary: str
    details: Optional[str] = None
    ref_commit: Optional[str] = None
    scope: Optional[List[str]] = None
    functions: Optional[List[str]] = None

    def to_json(self) -> str:
        return json.dumps({k: v for k, v in asdict(self).items() if v is not None}, ensure_ascii=False)


class DiaryManager:
    def __init__(self, repo_root: Optional[Path] = None, config_path: Optional[Path] = None) -> None:
        """初始化 Diary 路径上下文（canonical 写入 + legacy 读取兼容）。

        规则:
          - `repo_root` 优先；若未提供，可从 `config_path` 兼容推断。
          - canonical diary root 由工作区配置解析（默认 `.harbor/diary`）。
          - `specs/diary` 与 `diary.dir` 仅作为 legacy read-compatible source。
          - 所有兼容路径必须位于 repo root 内；越界时抛 `ValueError`。
        """
        self.repo_root = self._resolve_repo_root(explicit_repo_root=repo_root, config_path=config_path)
        self.config_path = config_path or resolve_workspace_config_path(self.repo_root)
        workspace_paths = load_workspace_paths(self.repo_root, enforce_write_safety=True)
        self.diary_dir = workspace_paths.diary_root
        self.legacy_diary_dirs = self._resolve_legacy_diary_dirs()

    def log(
        self,
        summary: str,
        type: str = "feature",
        importance: str = "normal",
        visibility: str = "internal",
        details: Optional[str] = None,
        ref_commit: Optional[str] = None,
        author: Optional[str] = None,
        ts: Optional[str] = None,
    ) -> DiaryEntry:
        """写入一条 DiaryEntry 到当月 JSONL。

        功能:
          - 构造 DiaryEntry 并追加写入 canonical `.harbor/diary/{YYYY-MM}.jsonl`。
          - 自动处理月度轮转与文件创建。
          - 生成缺省元数据：`ts`（ISO8601 UTC）、`author`（读取 git user.name 或默认 "AI"）。

        使用场景:
          - CLI `harbor log` 的核心实现。
          - 在 `harbor sync --pre-commit` 中写入重要事件草稿。

        依赖:
          - 文件系统访问（canonical `.harbor/diary` 目录）。
          - legacy `specs/diary` 仅用于读取兼容，不作为写入目标。
          - `harbor.core.diary.DiaryManager` 数据模型与校验。

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: once

        Args:
          summary (str): 变更摘要。
          type (str): `feature|bugfix|refactor|chore|incident`。
          importance (str): `trivial|normal|high|critical`。
          visibility (str): `internal|repo|public`。
          details (str | None): 详细描述，可选。
          ref_commit (str | None): 关联 Git Hash，可选。
          author (str | None): 提交人；缺省从优先级策略获取或 "AI"。
          ts (str | None): 指定 ISO8601 时间戳；缺省为当前 UTC。

        Returns:
          DiaryEntry: 已校验并写入的条目对象。

        Raises:
          ValueError: 枚举值不合法或必填字段为空。
          OSError: 目录/文件不可写或创建失败。
          ConfigError: 配置不可访问或路径越界。
        """
        if not summary or not isinstance(summary, str):
            raise ValueError("summary is required")
        if type not in TYPE_SET:
            raise ValueError("invalid type")
        if importance not in IMPORTANCE_SET:
            raise ValueError("invalid importance")
        if visibility not in VISIBILITY_SET:
            raise ValueError("invalid visibility")
        resolved_author = author or self._resolve_author()
        resolved_ts = ts or self._utc_now_iso()
        entry = DiaryEntry(
            ver=1,
            ts=resolved_ts,
            author=resolved_author,
            type=type,
            importance=importance,
            visibility=visibility,
            summary=summary,
            details=details,
            ref_commit=ref_commit,
        )
        target = self._current_file_path(resolved_ts)
        target.parent.mkdir(parents=True, exist_ok=True)
        line = entry.to_json()
        with target.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        return entry

    def load_active(self, min_visibility: str = "internal") -> List[DiaryEntry]:
        now = datetime.utcnow()
        prev_month = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
        months = [now.strftime("%Y-%m"), prev_month.strftime("%Y-%m")]
        res: List[DiaryEntry] = []
        seen: Set[str] = set()
        for m in months:
            for base_dir in self._iter_read_dirs():
                p = Path(base_dir) / f"{m}.jsonl"
                if not p.exists():
                    continue
                for line in p.read_text(encoding="utf-8").splitlines():
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    if not isinstance(obj, dict):
                        continue
                    dedupe_key = self._entry_dedupe_key(obj)
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)
                    vis = str(obj.get("visibility", "internal"))
                    if VISIBILITY_ORDER.get(vis, 0) < VISIBILITY_ORDER.get(min_visibility, 0):
                        continue
                    res.append(self._from_dict(obj))
        return res

    def export_markdown(self, since: Optional[str] = None, min_visibility: str = "repo") -> str:
        items = self.load_active(min_visibility=min_visibility)
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                items = [e for e in items if self._parse_ts(e.ts) >= since_dt]
            except Exception:
                pass
        items_sorted = sorted(items, key=lambda e: e.ts, reverse=True)
        lines: List[str] = []
        lines.append("# Harbor Diary Export")
        emoji = {"critical": "🔴", "high": "🟠", "normal": "🔵", "trivial": "⚪"}
        for e in items_sorted:
            mark = emoji.get(e.importance, "🔵")
            lines.append(f"- {mark} [{e.type}] {e.ts} {e.summary} (by {e.author})")
            if e.details:
                lines.append(f"  - {e.details}")
        return "\n".join(lines)

    def _resolve_repo_root(self, explicit_repo_root: Optional[Path], config_path: Optional[Path]) -> Path:
        if explicit_repo_root is not None:
            return Path(explicit_repo_root).resolve()
        if config_path is not None:
            cfg = Path(config_path).resolve()
            if cfg.name == "harbor.yaml" and cfg.parent.name == "config" and cfg.parent.parent.name == ".harbor":
                return cfg.parent.parent.parent.resolve()
            if cfg.name == "config.yaml" and cfg.parent.name == ".harbor":
                return cfg.parent.parent.resolve()
        return Path.cwd().resolve()

    def _ensure_within_repo(self, target: Path, *, field_name: str) -> Path:
        resolved = Path(target).resolve()
        try:
            resolved.relative_to(self.repo_root)
        except ValueError as exc:
            raise ValueError(
                f"Invalid diary path for '{field_name}': '{resolved.as_posix()}' "
                f"escapes repo root '{self.repo_root.as_posix()}'."
            ) from exc
        return resolved

    def _resolve_legacy_diary_dirs(self) -> List[Path]:
        dirs: List[Path] = []
        fixed_legacy = self._ensure_within_repo(self.repo_root / "specs" / "diary", field_name="legacy.specs_diary")
        dirs.append(fixed_legacy)

        loaded = load_workspace_config(self.repo_root)
        cfg = dict(loaded.get("config") or {})
        legacy_dir_raw = (cfg.get("diary", {}) or {}).get("dir")
        if legacy_dir_raw:
            legacy_dir = self._ensure_within_repo(self.repo_root / str(legacy_dir_raw), field_name="diary.dir")
            if legacy_dir != self.diary_dir and legacy_dir not in dirs:
                dirs.append(legacy_dir)
        return dirs

    def _iter_read_dirs(self) -> List[Path]:
        dirs: List[Path] = [self.diary_dir]
        for p in self.legacy_diary_dirs:
            if p not in dirs:
                dirs.append(p)
        return dirs

    def _current_file_path(self, ts_iso: str) -> Path:
        y = ts_iso[:4]
        m = ts_iso[5:7]
        return Path(self.diary_dir) / f"{y}-{m}.jsonl"

    def _entry_dedupe_key(self, obj: Dict[str, Any]) -> str:
        normalized = self._normalize_for_hash(obj)
        payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _normalize_for_hash(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): self._normalize_for_hash(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
        if isinstance(value, list):
            return [self._normalize_for_hash(v) for v in value]
        if isinstance(value, tuple):
            return [self._normalize_for_hash(v) for v in value]
        if isinstance(value, Path):
            return value.as_posix()
        return value

    def _resolve_author(self) -> str:
        env = os.getenv("HARBOR_AUTHOR")
        if env:
            return env.strip().strip("'\"")
        try:
            v = subprocess.check_output(["git", "config", "--get", "user.name"], stderr=subprocess.DEVNULL).decode("utf-8").strip()
            if v:
                return v.strip().strip("'\"")
        except Exception:
            pass
        for k in ("USER", "USERNAME"):
            v2 = os.getenv(k)
            if v2:
                return v2.strip().strip("'\"")
        return "AI"

    def _utc_now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _parse_ts(self, ts: str) -> datetime:
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return datetime.utcnow()

    def _from_dict(self, obj: Dict[str, Any]) -> DiaryEntry:
        return DiaryEntry(
            ver=int(obj.get("ver", 1)),
            ts=str(obj.get("ts", "")),
            author=str(obj.get("author", "")),
            type=str(obj.get("type", "")),
            importance=str(obj.get("importance", "normal")),
            visibility=str(obj.get("visibility", "internal")),
            summary=str(obj.get("summary", "")),
            details=obj.get("details"),
            ref_commit=obj.get("ref_commit"),
            scope=obj.get("scope"),
            functions=obj.get("functions"),
        )
