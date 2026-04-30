# Service Proxy Rules Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a curated `proxy` ruleset for common non-AI overseas service vendors while preserving dedicated `ai` and `direct` rulesets.

**Architecture:** Reuse the existing parser and classical provider generator for `proxy.txt`. Add `proxy.list` for local stable supplements and `proxy.sources.txt` for vendor-level upstream sources. Keep broad GFW or generic proxy sources out of `proxy.sources.txt`.

**Tech Stack:** Python 3 standard library, pytest, Mihomo/OpenClash rule-provider YAML payloads.

---

### Task 1: Add Proxy Coverage Tests

**Files:**
- Modify: `tests/test_convert_rules.py`
- Create: `proxy.list`

**Step 1: Write the failing tests**

Add this import:

```python
from scripts.convert_chatgpt_to_ai import build_classical_entries
```

Add these tests:

```python
def test_proxy_rules_cover_common_overseas_service_vendors():
    proxy_rules = (Path(__file__).resolve().parents[1] / "proxy.list").read_text(
        encoding="utf-8"
    )

    expected_rules = [
        "DOMAIN-SUFFIX,google.com",
        "DOMAIN-SUFFIX,youtube.com",
        "DOMAIN-SUFFIX,x.com",
        "DOMAIN-SUFFIX,twitter.com",
        "DOMAIN-SUFFIX,github.com",
        "DOMAIN-SUFFIX,telegram.org",
        "DOMAIN-SUFFIX,facebook.com",
        "DOMAIN-SUFFIX,instagram.com",
        "DOMAIN-SUFFIX,netflix.com",
        "DOMAIN-SUFFIX,spotify.com",
        "DOMAIN-SUFFIX,cloudflare.com",
        "DOMAIN-SUFFIX,notion.so",
        "DOMAIN-SUFFIX,vercel.com",
    ]

    for expected_rule in expected_rules:
        assert expected_rule in proxy_rules
```

Optional focused generator test using temporary files:

```python
def test_build_classical_entries_supports_proxy_file_names(tmp_path, monkeypatch):
    (tmp_path / "proxy.list").write_text(
        "DOMAIN-SUFFIX,google.com\nDOMAIN-SUFFIX,x.com\n", encoding="utf-8"
    )
    (tmp_path / "proxy.sources.txt").write_text(
        "https://example.test/proxy.yaml\n", encoding="utf-8"
    )

    import scripts.convert_chatgpt_to_ai as converter

    monkeypatch.setattr(
        converter,
        "fetch_url",
        lambda url: "payload:\n  - DOMAIN-SUFFIX,youtube.com\n  - '+.github.com'\n",
    )

    assert build_classical_entries(
        tmp_path, "proxy.list", "proxy.sources.txt"
    ) == [
        "DOMAIN-SUFFIX,google.com",
        "DOMAIN-SUFFIX,x.com",
        "DOMAIN-SUFFIX,youtube.com",
        "DOMAIN-SUFFIX,github.com",
    ]
```

**Step 2: Run tests to verify failure**

Run:

```bash
pytest tests/test_convert_rules.py -q
```

Expected: fails because `proxy.list` does not exist and `build_classical_entries` is not imported yet.

---

### Task 2: Add Local Proxy Rules

**Files:**
- Create: `proxy.list`

**Step 1: Write the local vendor list**

Create `proxy.list` with scoped sections:

```text
# Local proxy rules. Keep this file scoped to common non-AI overseas service vendors.

# Google / YouTube / Android
DOMAIN-KEYWORD,google
DOMAIN-SUFFIX,google.com
DOMAIN-SUFFIX,google.com.hk
DOMAIN-SUFFIX,googleapis.com
DOMAIN-SUFFIX,gstatic.com
DOMAIN-SUFFIX,gvt1.com
DOMAIN-SUFFIX,gvt2.com
DOMAIN-SUFFIX,gvt3.com
DOMAIN-SUFFIX,ggpht.com
DOMAIN-SUFFIX,googleusercontent.com
DOMAIN-SUFFIX,googlevideo.com
DOMAIN-SUFFIX,youtube.com
DOMAIN-SUFFIX,youtu.be
DOMAIN-SUFFIX,ytimg.com
DOMAIN-SUFFIX,youtubei.googleapis.com
DOMAIN-SUFFIX,android.com
DOMAIN-SUFFIX,appspot.com
DOMAIN-SUFFIX,blogger.com
DOMAIN-SUFFIX,recaptcha.net
DOMAIN-SUFFIX,gmail.com
DOMAIN-SUFFIX,googlemail.com
DOMAIN-SUFFIX,dns.google

# Developer platforms and infrastructure
DOMAIN-SUFFIX,github.com
DOMAIN-SUFFIX,github.io
DOMAIN-SUFFIX,githubusercontent.com
DOMAIN-SUFFIX,githubassets.com
DOMAIN-SUFFIX,github.dev
DOMAIN-SUFFIX,gitlab.com
DOMAIN-SUFFIX,cloudflare.com
DOMAIN-SUFFIX,cloudflare-dns.com
DOMAIN-SUFFIX,workers.dev
DOMAIN-SUFFIX,vercel.app
DOMAIN-SUFFIX,vercel.com
DOMAIN-SUFFIX,jsdelivr.net
DOMAIN-SUFFIX,raw.githubusercontent.com
DOMAIN-KEYWORD,github

# Social / messaging / streaming / productivity
DOMAIN-SUFFIX,t.co
DOMAIN-SUFFIX,x.com
DOMAIN-SUFFIX,twitter.com
DOMAIN-SUFFIX,twimg.com
DOMAIN-SUFFIX,telegram.org
DOMAIN-SUFFIX,t.me
DOMAIN-SUFFIX,facebook.com
DOMAIN-SUFFIX,fbcdn.net
DOMAIN-SUFFIX,instagram.com
DOMAIN-SUFFIX,whatsapp.com
DOMAIN-SUFFIX,netflix.com
DOMAIN-SUFFIX,nflxvideo.net
DOMAIN-SUFFIX,spotify.com
DOMAIN-SUFFIX,notion.so
DOMAIN-SUFFIX,notion.site

# Microsoft / search
DOMAIN-KEYWORD,bing
DOMAIN-SUFFIX,live.com
```

**Step 2: Run focused tests**

Run:

```bash
pytest tests/test_convert_rules.py::test_proxy_rules_cover_common_overseas_service_vendors -q
```

Expected: passes.

---

### Task 3: Add Vendor-Level Proxy Sources

**Files:**
- Create: `proxy.sources.txt`

**Step 1: Create source list**

Create `proxy.sources.txt`:

```text
# Common overseas service vendor sources merged into proxy.txt by scripts/convert_chatgpt_to_ai.py.
# Keep one URL per line. Sources can be payload YAML or Clash list-style rules.
# Do not add broad GFW or generic proxy lists here.

https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Google/Google.yaml
https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/YouTube/YouTube.yaml
https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/GitHub/GitHub.yaml
https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Telegram/Telegram.yaml
https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Twitter/Twitter.yaml
https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Facebook/Facebook.yaml
https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Netflix/Netflix.yaml
https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Spotify/Spotify.yaml
```

**Step 2: Check broad sources are absent**

Run:

```bash
rg "gfw|Loyalsoldier.*/proxy" proxy.sources.txt
```

Expected: no matches.

---

### Task 4: Generate Proxy Provider

**Files:**
- Modify: `scripts/convert_chatgpt_to_ai.py`
- Create: `proxy.txt`

**Step 1: Update generator**

In `main()`, add:

```python
    write_payload(
        repo_root / "proxy.txt",
        build_classical_entries(repo_root, "proxy.list", "proxy.sources.txt"),
    )
```

Place it after `ai.txt` generation and before `direct.txt` generation.

**Step 2: Run generator**

Run:

```bash
python3 scripts/convert_chatgpt_to_ai.py
```

Expected: `proxy.txt` is created with `payload:` and quoted classical rules.

**Step 3: Spot-check generated output**

Run:

```bash
rg "DOMAIN-SUFFIX,(google.com|youtube.com|x.com|github.com|telegram.org|netflix.com|spotify.com)" proxy.txt
```

Expected: matches for representative services.

---

### Task 5: Update README

**Files:**
- Modify: `README.md`

**Step 1: Document three rulesets**

Update the introduction to list:

```markdown
- `ai.txt`: AI related domains, routed through proxy.
- `proxy.txt`: common non-AI overseas service vendors, routed through proxy.
- `direct.txt`: mainland video, banking/payment, and e-commerce domains, routed direct.
```

**Step 2: Update file descriptions**

Add descriptions for:

```markdown
- `proxy.list`: local common overseas service vendor proxy supplements.
- `proxy.sources.txt`: vendor-level overseas service rule sources, one URL per line.
```

**Step 3: Update OpenClash/Mihomo example**

Add provider:

```yaml
  proxy:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/proxy.txt"
    path: ./ruleset/proxy.yaml
    interval: 86400
```

Add rule:

```yaml
  - RULE-SET,proxy,PROXY
```

Keep order: `ai`, `proxy`, `direct`.

**Step 4: Update maintenance notes**

Document that `proxy.sources.txt` should only contain vendor-level rules and must not include broad GFW or generic proxy lists.

---

### Task 6: Full Verification

**Files:**
- Test: all changed files

**Step 1: Run generator**

Run:

```bash
python3 scripts/convert_chatgpt_to_ai.py
```

Expected: exits 0.

**Step 2: Run tests**

Run:

```bash
pytest tests/test_convert_rules.py -q
```

Expected: all tests pass.

**Step 3: Inspect git diff**

Run:

```bash
git diff -- README.md scripts/convert_chatgpt_to_ai.py tests/test_convert_rules.py proxy.list proxy.sources.txt proxy.txt
```

Expected: only the scoped three-ruleset changes are present.

**Step 4: Commit implementation**

Run:

```bash
git add README.md scripts/convert_chatgpt_to_ai.py tests/test_convert_rules.py proxy.list proxy.sources.txt proxy.txt
git commit -m "feat: add curated proxy ruleset"
```
