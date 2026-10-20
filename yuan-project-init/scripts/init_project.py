#!/usr/bin/env python3
"""Initialize a research workspace using only the Python standard library."""

import argparse
import json
from pathlib import Path
import sys


SKILL_DIR = Path(__file__).resolve().parents[1]
BEGIN = "<!-- yuan-research:begin -->"
END = "<!-- yuan-research:end -->"
SKILLS = {
    "paper_skill": "yuan-paper-explainer",
    "mechanism_skill": "yuan-mechanism-builder",
    "idea_skill": "yuan-idea-explorer",
}


def project_block(skills_root):
    text = (SKILL_DIR / "assets/AGENTS.md.template").read_text(encoding="utf-8")
    for key, name in SKILLS.items():
        path = skills_root / name / "SKILL.md"
        if not path.is_file():
            raise ValueError(f"Required Skill not found: {path}")
        text = text.replace("{{" + key + "}}", str(path))
    return f"{BEGIN}\n{text.rstrip()}\n{END}\n"


def make_plan(root, skills_root):
    if root == skills_root or skills_root in root.parents:
        raise ValueError("Choose a research workspace outside the Skill source directory.")
    block = project_block(skills_root)
    directories = (root, root / "references", root / "mechanisms", root / "ideas")
    files = {
        root / "AGENTS.md": block,
        root / "research-context.md": (SKILL_DIR / "assets/research-context.md").read_text(encoding="utf-8"),
        root / "ideas/INDEX.md": (SKILL_DIR / "assets/ideas-index.md").read_text(encoding="utf-8"),
    }
    plan = []
    warnings = []
    # Inspect every managed path before writing anything.
    for path in directories:
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError(f"Directory path conflict: {path}")
        plan.append((path, "directory", "preserve" if path.exists() else "create", None))
    for path, content in files.items():
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError(f"File path conflict: {path}")
        action = "create"
        if path.exists():
            action = "preserve"
            if path.name == "AGENTS.md":
                current = path.read_text(encoding="utf-8")
                begins, ends = current.count(BEGIN), current.count(END)
                if begins == ends == 0:
                    action = "append"
                    content = ("\n\n" if current and not current.endswith("\n") else "\n" if current else "") + block
                elif begins != 1 or ends != 1 or current.index(BEGIN) > current.index(END):
                    raise ValueError(f"Invalid yuan-research markers in {path}; preserve and review this file.")
                else:
                    existing = current[current.index(BEGIN):current.index(END) + len(END)]
                    if existing != block.rstrip():
                        warnings.append("Existing project instructions differ from this template; preserved for review.")
        plan.append((path, "file", action, content))
    return plan, warnings


def initialize(root, skills_root, dry_run=False):
    plan, warnings = make_plan(root, skills_root)
    if not dry_run:
        for path, kind, action, content in plan:
            if action == "preserve":
                continue
            if kind == "directory":
                path.mkdir(parents=True, exist_ok=True)
            else:
                # Exclusive creation never replaces an existing research file.
                with path.open("a" if action == "append" else "x", encoding="utf-8") as handle:
                    handle.write(content)
    return {
        "ok": True,
        "project_dir": str(root),
        "dry_run": dry_run,
        "items": [{"path": str(p), "kind": k, "action": a} for p, k, a, _ in plan],
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init", help="Create missing project structure; preserve existing content.")
    init.add_argument("project_dir", type=Path)
    init.add_argument("--skills-root", type=Path, default=SKILL_DIR.parent)
    init.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = initialize(args.project_dir.expanduser().resolve(), args.skills_root.expanduser().resolve(), args.dry_run)
    except (OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
