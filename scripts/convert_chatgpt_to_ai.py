#!/usr/bin/env python3
"""Convert local Clash list rules into Mihomo/OpenClash rule-provider files."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen

RULE_PREFIX_TYPES = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
CLASSICAL_RULE_TYPES = {
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "IP-CIDR",
    "IP-CIDR6",
    "IP-ASN",
}
AI_SOURCE_URLS_FILE = "ai.sources.txt"


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


def parse_classical_rules(lines: Iterable[str]) -> list[str]:
    """Parse Clash rules into classical rule-provider payload entries.

    Empty lines and comments are ignored. Duplicate rules are skipped while
    keeping the original order of the remaining rules.
    """

    entries: list[str] = []
    seen: set[str] = set()

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line not in seen:
            seen.add(line)
            entries.append(line)

    return entries


def normalize_ai_source_entry(entry: str) -> str | None:
    entry = entry.strip().strip("'\"")
    if not entry:
        return None

    if entry.startswith("+."):
        return entry

    if "," not in entry:
        return entry

    rule_type, raw_value = (part.strip() for part in entry.split(",", 1))
    value = raw_value.split(",", 1)[0].strip()
    if not value:
        return None

    if rule_type == "DOMAIN-SUFFIX":
        return f"+.{value}"
    if rule_type == "DOMAIN":
        return value

    return None


def parse_ai_source_entries(lines: Iterable[str]) -> list[str]:
    entries: list[str] = []
    seen: set[str] = set()

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or line == "payload:":
            continue

        if line.startswith("- "):
            line = line[2:].strip()

        entry = normalize_ai_source_entry(line)
        if entry is None or entry in seen:
            continue

        seen.add(entry)
        entries.append(entry)

    return entries


def normalize_classical_source_entry(entry: str) -> str | None:
    entry = entry.strip().strip("'\"")
    if not entry:
        return None

    if entry.startswith("+."):
        return f"DOMAIN-SUFFIX,{entry[2:]}"

    if "," not in entry:
        return f"DOMAIN,{entry}"

    rule_type = entry.split(",", 1)[0].strip()
    if rule_type in CLASSICAL_RULE_TYPES:
        return entry

    return None


def parse_classical_source_entries(lines: Iterable[str]) -> list[str]:
    entries: list[str] = []
    seen: set[str] = set()

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or line == "payload:":
            continue

        if line.startswith("- "):
            line = line[2:].strip()

        entry = normalize_classical_source_entry(line)
        if entry is None or entry in seen:
            continue

        seen.add(entry)
        entries.append(entry)

    return entries


def merge_unique(*entry_groups: Iterable[str]) -> list[str]:
    entries: list[str] = []
    seen: set[str] = set()

    for group in entry_groups:
        for entry in group:
            if entry not in seen:
                seen.add(entry)
                entries.append(entry)

    return entries


def read_source_urls(path: Path) -> list[str]:
    if not path.exists():
        return []

    urls: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#"):
            urls.append(line)

    return urls


def fetch_url(url: str) -> str:
    request = Request(url, headers={"User-Agent": "chatgpt-openclash-rule-sync"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def build_ai_entries(repo_root: Path) -> list[str]:
    local_entries = parse_rules(
        (repo_root / "chatgpt.list").read_text(encoding="utf-8").splitlines()
    )
    source_entries: list[str] = []

    for url in read_source_urls(repo_root / AI_SOURCE_URLS_FILE):
        source_text = fetch_url(url)
        source_entries.extend(parse_ai_source_entries(source_text.splitlines()))

    return merge_unique(local_entries, source_entries)


def build_classical_entries(
    repo_root: Path, local_source_name: str, source_urls_name: str
) -> list[str]:
    local_entries = parse_classical_rules(
        (repo_root / local_source_name).read_text(encoding="utf-8").splitlines()
    )
    source_entries: list[str] = []

    for url in read_source_urls(repo_root / source_urls_name):
        source_text = fetch_url(url)
        source_entries.extend(parse_classical_source_entries(source_text.splitlines()))

    return merge_unique(local_entries, source_entries)


def write_payload(target: Path, entries: Iterable[str]) -> None:
    output_lines = ["payload:"] + [f"  - '{entry}'" for entry in entries]
    target.write_text("\n".join(output_lines) + "\n", encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    write_payload(repo_root / "ai.txt", build_ai_entries(repo_root))
    write_payload(
        repo_root / "proxy.txt",
        build_classical_entries(repo_root, "proxy.list", "proxy.sources.txt"),
    )
    write_payload(
        repo_root / "direct.txt",
        build_classical_entries(repo_root, "direct.list", "direct.sources.txt"),
    )


if __name__ == "__main__":
    main()
