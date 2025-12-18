import sqlite3
from pathlib import Path

def main():
    db_path = Path(".harbor") / "cache" / "harbor.db"
    root = Path.cwd().resolve().as_posix()
    print(f"db={db_path.as_posix()} root={root}")
    if not db_path.exists():
        print("harbor.db not found")
        return
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT path, last_modified, status FROM files ORDER BY last_modified DESC LIMIT 5")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if not rows:
        print("files table is empty")
        return
    for r in rows:
        p = r["path"]
        is_abs = Path(p).is_absolute()
        print(f"path={p} is_absolute={is_abs} status={r['status']} mtime={r['last_modified']}")

if __name__ == "__main__":
    main()
