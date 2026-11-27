#!/usr/bin/env python3
"""Fail when a change touches a locked path (rule G2, docs/DEV_WORKFLOW.md).

CI:         check_locked_paths.py --base <base-sha> --head <head-sha>
pre-commit: check_locked_paths.py --staged

The list of locked paths is read from the base revision (CI) or from HEAD
(pre-commit), never from the change under review, so a change cannot unlock
itself. Renames count as touching both the old and the new path.

An approved owner change passes when RESCUEVISION_LOCKED_CHANGE_APPROVED=1. CI sets it
only when the owner added the "owner-approved" label; locally the owner sets it
by hand. Agents must never set it (AGENTS.md, Never list).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

MANIFEST = ".github/locked-paths.txt"


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], check=False, capture_output=True, text=True)
    if result.returncode != 0:
        # Fail closed: an unreadable revision or manifest is a failure, never a pass.
        sys.exit(f"locked-paths: git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile(f"^{out}$")


def load_patterns(revision: str) -> list[re.Pattern[str]]:
    text = git("show", f"{revision}:{MANIFEST}")
    lines = (line.strip() for line in text.splitlines())
    patterns = [glob_to_regex(line) for line in lines if line and not line.startswith("#")]
    if not patterns:
        sys.exit(f"locked-paths: {MANIFEST} at {revision} lists no paths; refusing to pass")
    return patterns


def changed_paths(diff_args: list[str]) -> set[str]:
    paths: set[str] = set()
    for line in git("diff", "--name-status", "-M", *diff_args).splitlines():
        parts = line.split("\t")
        paths.update(parts[1:])  # rename and copy lines carry old and new paths
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()

    if args.staged:
        exists = subprocess.run(
            ["git", "cat-file", "-e", f"HEAD:{MANIFEST}"], check=False, capture_output=True
        )
        if exists.returncode != 0:
            # Only the commit that introduces the lock list itself reaches this branch.
            print(f"locked-paths: HEAD has no {MANIFEST} yet (bootstrap commit); not enforced")
            return 0
        patterns = load_patterns("HEAD")
        paths = changed_paths(["--cached"])
    elif args.base:
        patterns = load_patterns(args.base)
        paths = changed_paths([f"{args.base}...{args.head}"])
    else:
        parser.error("give --base <sha> or --staged")

    touched = sorted(p for p in paths if any(rx.match(p) for rx in patterns))
    if not touched:
        print("locked-paths: no locked path changed")
        return 0

    listing = "\n".join(f"  - {p}" for p in touched)
    if os.environ.get("RESCUEVISION_LOCKED_CHANGE_APPROVED") == "1":
        print(f"locked-paths: owner-approved change to:\n{listing}")
        return 0

    print(
        "locked-paths: this change touches files only the owner may change:\n"
        f"{listing}\n"
        "Agents: revert these files and describe the change you need in the PR text.\n"
        "Owner: add the 'owner-approved' label (CI) or set "
        "RESCUEVISION_LOCKED_CHANGE_APPROVED=1 (local).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
