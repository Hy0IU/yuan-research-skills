#!/usr/bin/env python3
"""Create Idea skeletons and preserve architecture snapshots; no semantic edits."""

import argparse
import json
from pathlib import Path
import re
import sys


SKILL_DIR = Path(__file__).resolve().parents[1]


def outside_source(path):
    source = SKILL_DIR.parent
    if path == source or source in path.parents:
        raise ValueError("Use a research directory outside the Skill source repository.")


def create(project, title):
    outside_source(project)
    ideas = project / "ideas"
    index = ideas / "INDEX.md"
    if ideas.is_symlink() or not ideas.is_dir() or index.is_symlink() or not index.is_file():
        raise ValueError("Project needs a regular ideas/INDEX.md; initialize it with yuan-project-init first.")
    title = " ".join(title.split())
    slug = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", title).strip(" .")[:80].rstrip(" .")
    if not slug:
        raise ValueError("Provide a non-empty direction title usable as a directory name.")
    template = (SKILL_DIR / "assets/idea.md").read_text(encoding="utf-8")
    lock = ideas / ".yuan-create.lock"
    try:
        handle = lock.open("x", encoding="utf-8")
    except FileExistsError as error:
        raise ValueError(f"Creation lock exists; inspect the other operation before retrying: {lock}") from error
    try:
        with handle:
            handle.write("Idea creation in progress\n")
        numbers = [int(n) for n in re.findall(r"\bIDEA-(\d+)\b", index.read_text(encoding="utf-8"))]
        for child in ideas.iterdir():
            match = re.match(r"^IDEA-(\d+)(?:-|$)", child.name)
            if match:
                numbers.append(int(match.group(1)))
                if re.sub(r"^IDEA-\d+-", "", child.name) == slug:
                    raise ValueError(f"A direction with this directory title already exists: {child}")
        idea_id = f"IDEA-{max(numbers, default=0) + 1:03d}"
        target = ideas / f"{idea_id}-{slug}"
        body = template.replace("{{idea_id}}", idea_id).replace("{{title}}", title)
        target.mkdir()
        with (target / "idea.md").open("x", encoding="utf-8") as output:
            output.write(body)
        with (target / "decisions.md").open("x", encoding="utf-8") as output:
            output.write("# Decision History\n")
        (target / "experiments").mkdir()
    finally:
        lock.unlink()
    return {"ok": True, "idea_id": idea_id, "idea_dir": str(target), "index_update_required": True}


def snapshot(folder):
    if folder.is_symlink():
        raise ValueError("Idea directory must not be a symbolic link.")
    folder = folder.resolve()
    outside_source(folder)
    if folder.parent.name != "ideas" or not re.match(r"^IDEA-\d+-", folder.name):
        raise ValueError("Select a project ideas/IDEA-number-title directory.")
    source = folder / "idea.md"
    versions = folder / "versions"
    if source.is_symlink() or not source.is_file():
        raise ValueError("A regular idea.md is required.")
    if versions.is_symlink() or (versions.exists() and not versions.is_dir()):
        raise ValueError("The versions path must be a regular directory.")
    body = source.read_bytes()
    numbers = [int(m.group(1)) for p in versions.glob("v*.md") if (m := re.fullmatch(r"v(\d+)\.md", p.name))]
    number = max(numbers, default=0) + 1
    versions.mkdir(exist_ok=True)
    while True:
        target = versions / f"v{number:03d}.md"
        try:
            with target.open("xb") as output:
                output.write(body)
            break
        except FileExistsError:
            number += 1
    return {"ok": True, "snapshot": str(target), "bytes": len(body), "decision_link_required": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    new = subs.add_parser("create")
    new.add_argument("project_dir", type=Path)
    new.add_argument("--title", required=True)
    old = subs.add_parser("snapshot")
    old.add_argument("idea_dir", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "create":
            result = create(args.project_dir.expanduser().resolve(), args.title)
        else:
            result = snapshot(args.idea_dir.expanduser())
    except (OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
