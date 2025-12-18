import sqlite3
from pathlib import Path

def posix_rel(root: Path, path: Path) -> str:
    try:
        rel = path.resolve().relative_to(root.resolve())
        return rel.as_posix()
    except Exception:
        return path.resolve().as_posix()

def main():
    db_path = Path(".harbor") / "cache" / "harbor.db"
    root = Path.cwd().resolve()
    print(f"db={db_path.as_posix()} root={root.as_posix()}")
    if not db_path.exists():
        print("harbor.db not found")
        return
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.execute("SELECT path, last_modified, status FROM files")
    rows = cur.fetchall()
    updated = 0
    deleted = 0
    try:
        cur.execute("BEGIN IMMEDIATE")
        for r in rows:
            old_path = r["path"]
            p = Path(old_path)
            try:
                p.resolve().relative_to(root)
                in_root = True
            except Exception:
                in_root = False
            if not in_root:
                cur.execute("DELETE FROM files WHERE path = ?", (old_path,))
                deleted += cur.rowcount or 0
                continue
            new_path = posix_rel(root, p)
            if new_path != old_path:
                cur.execute("UPDATE entries SET file_path = ? WHERE file_path = ?", (new_path, old_path))
                cur.execute("UPDATE files SET path = ? WHERE path = ?", (new_path, old_path))
                updated += 1
        cur.execute("COMMIT")
    except Exception:
        cur.execute("ROLLBACK")
        raise
    finally:
        cur.close()
        conn.close()
    print(f"updated={updated} deleted={deleted}")

if __name__ == "__main__":
    main()
