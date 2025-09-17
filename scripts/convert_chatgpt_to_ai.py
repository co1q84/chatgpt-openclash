#!/usr/bin/env python3
"""Convert chatgpt.list rules into the Clash rule-set format."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

RULE_PREFIX_TYPES = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}


def parse_rules(lines: Iterable[str]) -> list[str]:
    """Parse rules from the chatgpt.list format into payload entries.

    Empty lines and comments are ignored. Duplicate entries are skipped while
    keeping the original order of the remaining rules.
    """

    entries: list[str] = []
    seen: set[str] = set()

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        try:
            rule_type, value = (part.strip() for part in line.split(",", 1))
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise ValueError(f"Invalid rule line: {raw_line!r}") from exc

        if not value:
            continue

        if rule_type in RULE_PREFIX_TYPES:
            entry = f"+.{value}"
        else:
            entry = value

        if entry not in seen:
            seen.add(entry)
            entries.append(entry)

    return entries


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / "chatgpt.list"
    target = repo_root / "ai.txt"

    payload_entries = parse_rules(source.read_text(encoding="utf-8").splitlines())

    output_lines = ["payload:"] + [f"  - '{entry}'" for entry in payload_entries]
    target.write_text("\n".join(output_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
