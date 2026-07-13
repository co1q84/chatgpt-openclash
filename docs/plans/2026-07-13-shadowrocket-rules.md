# Shadowrocket Rules Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Generate three policy-free Shadowrocket remote rule sets from the same normalized entries and daily workflow used for the existing OpenClash/Mihomo files.

**Architecture:** Build each AI, proxy, and direct entry collection once, then pass it to separate OpenClash/Mihomo and Shadowrocket renderers. The existing YAML payload format remains unchanged; the Shadowrocket renderer writes plain typed rules and converts AI domain-provider entries into `DOMAIN-SUFFIX` or `DOMAIN` rules.

**Tech Stack:** Python 3 standard library, pytest, GitHub Actions YAML, Markdown

---

### Task 1: Add Shadowrocket AI conversion and plain rule-set rendering

**Files:**
- Modify: `tests/test_convert_rules.py`
- Modify: `scripts/convert_chatgpt_to_ai.py:225-244`

**Step 1: Write the failing conversion and writer tests**

Extend the imports in `tests/test_convert_rules.py` and add:

```python
from scripts.convert_chatgpt_to_ai import (
    # existing imports...
    convert_ai_entries_to_shadowrocket,
    write_shadowrocket_rules,
)


def test_convert_ai_entries_to_shadowrocket_uses_typed_rules():
    assert convert_ai_entries_to_shadowrocket(
        ["+.openai.com", "api.example.com"]
    ) == [
        "DOMAIN-SUFFIX,openai.com",
        "DOMAIN,api.example.com",
    ]


def test_write_shadowrocket_rules_uses_plain_policy_free_format(tmp_path):
    target = tmp_path / "rules.list"

    write_shadowrocket_rules(
        target,
        [
            "DOMAIN-SUFFIX,example.com",
            "IP-CIDR,203.0.113.0/24,no-resolve",
        ],
    )

    assert target.read_text(encoding="utf-8") == (
        "DOMAIN-SUFFIX,example.com\n"
        "IP-CIDR,203.0.113.0/24,no-resolve\n"
    )
    assert "payload:" not in target.read_text(encoding="utf-8")
    assert "PROXY" not in target.read_text(encoding="utf-8")
    assert "DIRECT" not in target.read_text(encoding="utf-8")
```

**Step 2: Run the focused tests and verify they fail**

Run:

```bash
pytest tests/test_convert_rules.py::test_convert_ai_entries_to_shadowrocket_uses_typed_rules tests/test_convert_rules.py::test_write_shadowrocket_rules_uses_plain_policy_free_format -q
```

Expected: collection fails because the two new functions cannot be imported.

**Step 3: Implement the minimal converters and writer**

Add above `main()` in `scripts/convert_chatgpt_to_ai.py`:

```python
def convert_ai_entries_to_shadowrocket(entries: Iterable[str]) -> list[str]:
    rules: list[str] = []

    for entry in entries:
        if entry.startswith("+."):
            rules.append(f"DOMAIN-SUFFIX,{entry[2:]}")
        else:
            rules.append(f"DOMAIN,{entry}")

    return rules


def write_shadowrocket_rules(target: Path, entries: Iterable[str]) -> None:
    target.write_text("".join(f"{entry}\n" for entry in entries), encoding="utf-8")
```

Do not add policies or YAML headers to the Shadowrocket output.

**Step 4: Run the focused tests and verify they pass**

Run the command from Step 2.

Expected: `2 passed`.

**Step 5: Commit the tested renderer**

```bash
git add scripts/convert_chatgpt_to_ai.py tests/test_convert_rules.py
git commit -m "feat: add Shadowrocket rule rendering"
```

### Task 2: Generate all six files from one normalized build

**Files:**
- Modify: `tests/test_convert_rules.py`
- Modify: `scripts/convert_chatgpt_to_ai.py:230-244`
- Create: `ai-shadowrocket.list`
- Create: `proxy-shadowrocket.list`
- Create: `direct-shadowrocket.list`

**Step 1: Write a failing integration test for shared generation**

Import `generate_files` and add:

```python
def test_generate_files_writes_clash_and_shadowrocket_outputs(tmp_path):
    (tmp_path / "chatgpt.list").write_text(
        "DOMAIN-SUFFIX,openai.com\n", encoding="utf-8"
    )
    (tmp_path / "ai.sources.txt").write_text("", encoding="utf-8")
    (tmp_path / "proxy.list").write_text(
        "DOMAIN-SUFFIX,google.com\n", encoding="utf-8"
    )
    (tmp_path / "proxy.sources.txt").write_text("", encoding="utf-8")
    (tmp_path / "direct.list").write_text(
        "IP-CIDR,192.0.2.0/24,no-resolve\n", encoding="utf-8"
    )
    (tmp_path / "direct.sources.txt").write_text("", encoding="utf-8")

    generate_files(tmp_path)

    assert (tmp_path / "ai.txt").read_text(encoding="utf-8") == (
        "payload:\n  - '+.openai.com'\n"
    )
    assert (tmp_path / "ai-shadowrocket.list").read_text(encoding="utf-8") == (
        "DOMAIN-SUFFIX,openai.com\n"
    )
    assert (tmp_path / "proxy-shadowrocket.list").read_text(
        encoding="utf-8"
    ) == "DOMAIN-SUFFIX,google.com\n"
    assert (tmp_path / "direct-shadowrocket.list").read_text(
        encoding="utf-8"
    ) == "IP-CIDR,192.0.2.0/24,no-resolve\n"
```

**Step 2: Run the integration test and verify it fails**

Run:

```bash
pytest tests/test_convert_rules.py::test_generate_files_writes_clash_and_shadowrocket_outputs -q
```

Expected: collection fails because `generate_files` does not exist.

**Step 3: Refactor generation to build each group once**

Replace the current `main()` body with a testable `generate_files()` plus a thin entry point:

```python
def generate_files(repo_root: Path) -> None:
    ai_entries = build_ai_entries(repo_root)
    proxy_entries = build_classical_entries(
        repo_root, "proxy.list", "proxy.sources.txt"
    )
    direct_entries = build_classical_entries(
        repo_root, "direct.list", "direct.sources.txt"
    )

    write_payload(repo_root / "ai.txt", ai_entries)
    write_payload(repo_root / "proxy.txt", proxy_entries)
    write_payload(repo_root / "direct.txt", direct_entries)

    write_shadowrocket_rules(
        repo_root / "ai-shadowrocket.list",
        convert_ai_entries_to_shadowrocket(ai_entries),
    )
    write_shadowrocket_rules(
        repo_root / "proxy-shadowrocket.list", proxy_entries
    )
    write_shadowrocket_rules(
        repo_root / "direct-shadowrocket.list", direct_entries
    )


def main() -> None:
    generate_files(Path(__file__).resolve().parents[1])
```

This is the required synchronization point: no output path calls a builder a
second time.

**Step 4: Run the integration test and full unit suite**

Run:

```bash
pytest tests/test_convert_rules.py::test_generate_files_writes_clash_and_shadowrocket_outputs -q
pytest tests/test_convert_rules.py -q
```

Expected: the focused test passes, then the entire file passes with no
regressions.

**Step 5: Generate the repository outputs**

Run:

```bash
python3 scripts/convert_chatgpt_to_ai.py
```

Expected: the three existing `.txt` files are regenerated and the three new
`*-shadowrocket.list` files are created with non-empty, policy-free typed rules.

**Step 6: Check generated format and idempotence**

Run:

```bash
head -n 5 ai-shadowrocket.list proxy-shadowrocket.list direct-shadowrocket.list
rg -n "^(payload:|[[:space:]]+-|'|.*,(PROXY|DIRECT)$)" *-shadowrocket.list
git diff --exit-code ai.txt proxy.txt direct.txt
python3 scripts/convert_chatgpt_to_ai.py
git diff --exit-code ai-shadowrocket.list proxy-shadowrocket.list direct-shadowrocket.list
```

Expected: the file heads show typed rules; `rg` prints nothing; existing Clash
outputs have no format regression; the second generation produces no further
changes.

**Step 7: Commit shared generation and generated files**

```bash
git add scripts/convert_chatgpt_to_ai.py tests/test_convert_rules.py ai-shadowrocket.list proxy-shadowrocket.list direct-shadowrocket.list
git commit -m "feat: generate Shadowrocket rule sets"
```

### Task 3: Include Shadowrocket outputs in daily automation

**Files:**
- Modify: `.github/workflows/sync-upstream.yml:68-76`
- Modify: `tests/test_convert_rules.py`

**Step 1: Write a failing workflow coverage test**

Add:

```python
def test_sync_workflow_stages_all_generated_files():
    workflow = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "sync-upstream.yml"
    ).read_text(encoding="utf-8")

    assert (
        "git add ai.txt proxy.txt direct.txt "
        "ai-shadowrocket.list proxy-shadowrocket.list "
        "direct-shadowrocket.list"
    ) in workflow
```

**Step 2: Run the focused test and verify it fails**

Run:

```bash
pytest tests/test_convert_rules.py::test_sync_workflow_stages_all_generated_files -q
```

Expected: FAIL because the workflow stages only the existing three files.

**Step 3: Extend the workflow staging command**

Change the commit step to:

```yaml
      - name: Commit updated ruleset
        run: |
          git add ai.txt proxy.txt direct.txt ai-shadowrocket.list proxy-shadowrocket.list direct-shadowrocket.list
          if ! git diff --cached --quiet; then
            git commit -m "chore: sync upstream and update rulesets"
          fi
```

Keep the existing schedule, manual trigger, generation command, and conditional
commit behavior unchanged.

**Step 4: Run the focused test and full unit suite**

Run:

```bash
pytest tests/test_convert_rules.py::test_sync_workflow_stages_all_generated_files -q
pytest tests/test_convert_rules.py -q
```

Expected: both commands pass.

**Step 5: Commit the automation update**

```bash
git add .github/workflows/sync-upstream.yml tests/test_convert_rules.py
git commit -m "ci: update Shadowrocket rules daily"
```

### Task 4: Document Shadowrocket remote rule usage

**Files:**
- Modify: `README.md:1-81`

**Step 1: Update the repository overview and file list**

Explain that the repository now serves both OpenClash/Mihomo and Shadowrocket.
List the three new generated files and state that all six outputs share the
same sources and daily generation process.

**Step 2: Add a Shadowrocket usage section**

Document these policy-free remote rules:

```text
RULE-SET,https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/ai-shadowrocket.list,PROXY
RULE-SET,https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/proxy-shadowrocket.list,PROXY
RULE-SET,https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/direct-shadowrocket.list,DIRECT
```

Also explain the UI equivalent: add each Raw URL as a `RULE-SET`, select the
desired proxy policy for AI/overseas rules, and select `DIRECT` for mainland
rules. Note that these rules should precede broader catch-all rules.

**Step 3: Update automation and local generation descriptions**

Replace language that mentions only the three Clash outputs with language that
covers both formats. Keep the existing daily time and manual workflow path.

**Step 4: Review Markdown and links**

Run:

```bash
rg -n "shadowrocket|Shadowrocket|RULE-SET" README.md
git diff --check
```

Expected: README lists all files and three Shadowrocket Raw URLs; whitespace
validation passes.

**Step 5: Commit documentation**

```bash
git add README.md
git commit -m "docs: add Shadowrocket rule usage"
```

### Task 5: Final verification

**Files:**
- Verify: `scripts/convert_chatgpt_to_ai.py`
- Verify: `tests/test_convert_rules.py`
- Verify: `.github/workflows/sync-upstream.yml`
- Verify: `README.md`
- Verify: `ai-shadowrocket.list`
- Verify: `proxy-shadowrocket.list`
- Verify: `direct-shadowrocket.list`

**Step 1: Run the complete tests**

```bash
pytest -q
```

Expected: all tests pass.

**Step 2: Regenerate all outputs**

```bash
python3 scripts/convert_chatgpt_to_ai.py
```

Expected: exit code 0.

**Step 3: Validate generated Shadowrocket structure**

```bash
test -s ai-shadowrocket.list
test -s proxy-shadowrocket.list
test -s direct-shadowrocket.list
rg -n "^(payload:|[[:space:]]+-|'|.*,(PROXY|DIRECT)$)" *-shadowrocket.list
```

Expected: all files are non-empty and `rg` returns exit code 1 with no matches.

**Step 4: Confirm deterministic generation and inspect scope**

```bash
git status --short
git diff --check
python3 scripts/convert_chatgpt_to_ai.py
git status --short
```

Expected: the second generation does not change tracked outputs; only the
pre-existing user-owned `.gitignore` change, if still present, remains outside
the feature commits.

**Step 5: Review recent commits**

```bash
git log --oneline -7
```

Expected: separate commits exist for the renderer, shared generation,
automation, documentation, design, and implementation plan.
