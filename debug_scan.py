from pathlib import Path
import yaml
from harbor.core.utils import iter_project_files
from harbor.core.git_utils import GitIgnoreMatcher
from pathspec import PathSpec

BASE = Path.cwd().resolve()
CFG_PATH = BASE / ".harbor" / "config.yaml"
TARGET = BASE / "harbor" / "core" / "index.py"

def load_config():
    if not CFG_PATH.exists():
        return ["**/*.py"], []
    data = yaml.safe_load(CFG_PATH.read_text(encoding="utf-8")) or {}
    code_roots = data.get("code_roots") or ["**/*.py"]
    exclude_paths = data.get("exclude_paths") or []
    return code_roots, exclude_paths

def read_gitignore_lines():
    gi = BASE / ".gitignore"
    if not gi.exists():
        return []
    lines = (gi.read_text(encoding="utf-8") or "").splitlines()
    out = []
    for raw in lines:
        s = (raw or "").strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    return out

def to_posix_rel(p: Path, base: Path):
    return p.resolve().relative_to(base).as_posix()

def eval_rules(rel_path: str, ordered_rules):
    decision = False
    last_rule = None
    for src, rule in ordered_rules:
        neg = rule.startswith("!")
        pat = rule[1:] if neg else rule
        spec = PathSpec.from_lines("gitwildmatch", [pat])
        if spec.match_file(rel_path):
            if neg:
                decision = False
                last_rule = (src, rule)
            else:
                decision = True
                last_rule = (src, rule)
    return decision, last_rule

def expand_dir_segments(rel_path: str):
    parts = rel_path.split("/")
    segs = []
    for i in range(len(parts) - 1):
        seg = "/".join(parts[: i + 1]) + "/"
        segs.append(seg)
    return segs

def eval_with_dirs(rel_path: str, ordered_rules):
    for seg in expand_dir_segments(rel_path):
        decision, last_rule = eval_rules(seg, ordered_rules)
        if decision:
            return True, last_rule
    return eval_rules(rel_path, ordered_rules)

def main():
    code_roots, exclude_paths = load_config()
    print("code_roots:", code_roots)
    print("exclude_paths:", exclude_paths)

    git_lines = read_gitignore_lines()
    print("gitignore_rules:", git_lines)

    ordered = [("gitignore", r) for r in git_lines] + [("config", r) for r in exclude_paths]
    matcher = GitIgnoreMatcher.from_root(cfg_excludes=exclude_paths)
    print("GitIgnoreMatcher_root:", str(matcher.root.resolve()))

    files = iter_project_files(code_roots, exclude_paths)
    print("iter_project_files_count:", len(files))
    sample = [to_posix_rel(p, BASE) for p in files[:20]]
    print("iter_project_files_sample:", sample)

    rel_target = to_posix_rel(TARGET, BASE)
    in_list = any(p.resolve() == TARGET.resolve() for p in files)
    print("testing_path:", rel_target)
    if in_list:
        print(f"{rel_target} ACCEPTED")
    else:
        rejected, rule = eval_with_dirs(rel_target, ordered)
        if rejected and rule:
            print(f"{rel_target} REJECTED by {rule[0]} rule: {rule[1]}")
        else:
            print(f"{rel_target} REJECTED (no matching rule)")

if __name__ == "__main__":
    main()
