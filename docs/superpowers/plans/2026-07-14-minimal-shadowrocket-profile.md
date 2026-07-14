# Minimal Shadowrocket Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the ignored local `未竟.yaml` Mihomo profile into an ignored local `未竟.conf` Shadowrocket profile that preserves the current proxy-policy structure and routing intent without adding DNS or other advanced configuration.

**Architecture:** Perform a one-time, dependency-free conversion in memory so private values never appear in patches or terminal output. Render a native Shadowrocket profile atomically, validate its structure and public rule sources locally, then hand it to the user for the Shadowrocket-only import and connection checks.

**Tech Stack:** Python 3 standard library for secret-safe extraction and atomic rendering, Shadowrocket text profile syntax, shell assertions, Git ignore checks

## Global Constraints

- The source is the ignored local file `未竟.yaml`; the output is the ignored local file `未竟.conf`.
- Do not print, log, stage, commit, or push subscription tokens, passwords, UUIDs, Reality keys, complete private node URLs, or rendered proxy lines.
- Do not embed the current HTTP 403 subscription URL in `未竟.conf`; include only a non-secret comment explaining that a working subscription must be imported or substituted.
- Keep `未竟.yaml` after conversion. Source deletion is outside this plan and requires a successful Shadowrocket import plus a separate user request.
- Do not add DNS servers, fake IP, DNS interception, `force-remote-dns`, TUN tuning, sniffing, MITM, rewrites, scripts, listener ports, controller settings, or logging settings.
- The only `[General]` values are `bypass-system = true`, `ipv6 = false`, and `prefer-ipv6 = false`.
- Keep `BOX_VISION`, `FALL_BOX`, `BEST_JC`, `BOX_FIRST`, and `PROXY` as the exact proxy and group names.
- Treat `BOX_VISION` as the only verified minimal path until a working subscription is imported and both `BEST_JC` and the `FALL_BOX` chain pass app-level tests.
- Never commit `未竟.conf`. This implementation intentionally produces no tracked code change.

---

## File Map

- Read only: `未竟.yaml` — private Mihomo source profile.
- Create locally, ignored and untracked: `未竟.conf` — private native Shadowrocket profile.
- Read only: `.gitignore` — confirms both profile formats are ignored.
- Read only: `ai-shadowrocket.list`, `proxy-shadowrocket.list`, `direct-shadowrocket.list` — locally generated counterparts of the three repository-hosted remote rule sets.
- Read only: `docs/superpowers/specs/2026-07-14-minimal-shadowrocket-profile-design.md` — approved behavior and validation contract.

No tracked implementation file is created or modified.

---

### Task 1: Establish the Secret-Safe Preconditions

**Files:**
- Read: `未竟.yaml`
- Read: `.gitignore`
- Must not yet exist: `未竟.conf`

**Interfaces:**
- Consumes: the current workspace and approved specification.
- Produces: a verified precondition that the source exists, both paths are ignored, and no destination will be overwritten.

- [ ] **Step 1: Confirm the source exists without displaying it**

Run:

```bash
test -s 未竟.yaml
```

Expected: exit 0 with no output.

- [ ] **Step 2: Confirm Git ignores both private profile paths**

Run:

```bash
git check-ignore -q 未竟.yaml
git check-ignore -q 未竟.conf
! git ls-files --error-unmatch 未竟.yaml >/dev/null 2>&1
! git ls-files --error-unmatch 未竟.conf >/dev/null 2>&1
```

Expected: exit 0 with no profile tracked by Git.

- [ ] **Step 3: Refuse to overwrite an existing destination**

Run:

```bash
test ! -e 未竟.conf
```

Expected: exit 0. If the file already exists, stop and ask the user whether it should be preserved or replaced; do not rename, delete, or overwrite it.

- [ ] **Step 4: Record the non-sensitive repository baseline**

Run:

```bash
git status --short --branch
git log -1 --oneline
```

Expected: the approved spec and implementation-plan commits may make `main` ahead of `origin/main`; neither private profile appears because both are ignored.

There is no commit for this task because it changes no file.

---

### Task 2: Render the Native Shadowrocket Profile Atomically

**Files:**
- Read: `未竟.yaml`
- Create locally: `未竟.conf`

**Interfaces:**
- Consumes: the exact `FALL_BOX` and `BOX_VISION` fields in the `proxies` section of `未竟.yaml`.
- Produces: an ignored mode-`0600` UTF-8 `未竟.conf` with `[General]`, `[Proxy]`, `[Proxy Group]`, and `[Rule]` sections.

- [ ] **Step 1: Run the dependency-free in-memory converter**

Run the complete program below from the repository root. It reads private values, validates their shapes, writes the destination through a temporary file, and emits only a non-sensitive success marker.

```bash
python3 - <<'PY'
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

source = Path("未竟.yaml")
target = Path("未竟.conf")

if target.exists():
    raise SystemExit("destination already exists; refusing to overwrite")

text = source.read_text(encoding="utf-8")

try:
    proxy_section = text.split("\nproxies:\n", 1)[1].split(
        "\nproxy-groups:\n", 1
    )[0]
except IndexError as exc:
    raise SystemExit("required proxies/proxy-groups boundary not found") from exc


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value.split(" #", 1)[0].rstrip()


def named_block(section: str, expected_name: str) -> str:
    matches = list(
        re.finditer(r"(?m)^  - name:\s*([^\n#]+?)\s*$", section)
    )
    for index, match in enumerate(matches):
        if unquote(match.group(1)) != expected_name:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
        return section[match.start():end]
    raise SystemExit(f"required proxy name missing: {expected_name}")


def scalar(block: str, key: str) -> str:
    match = re.search(
        rf"(?m)^\s{{4,}}{re.escape(key)}:\s*(.+?)\s*$",
        block,
    )
    if not match:
        raise SystemExit(f"required field missing: {key}")
    value = unquote(match.group(1))
    if not value:
        raise SystemExit(f"required field empty: {key}")
    return value


fall_block = named_block(proxy_section, "FALL_BOX")
vision_block = named_block(proxy_section, "BOX_VISION")

fall = {
    "server": scalar(fall_block, "server"),
    "port": scalar(fall_block, "port"),
    "cipher": scalar(fall_block, "cipher"),
    "password": scalar(fall_block, "password"),
}
vision = {
    "server": scalar(vision_block, "server"),
    "port": scalar(vision_block, "port"),
    "uuid": scalar(vision_block, "uuid"),
    "network": scalar(vision_block, "network"),
    "flow": scalar(vision_block, "flow"),
    "sni": scalar(vision_block, "servername"),
    "fingerprint": scalar(vision_block, "client-fingerprint"),
    "public_key": scalar(vision_block, "public-key"),
    "short_id": scalar(vision_block, "short-id"),
}

for port in (fall["port"], vision["port"]):
    if not port.isdigit() or not 1 <= int(port) <= 65535:
        raise SystemExit("proxy port is outside 1..65535")
if not re.fullmatch(
    r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}",
    vision["uuid"],
):
    raise SystemExit("BOX_VISION UUID has an invalid shape")
if vision["network"] != "tcp":
    raise SystemExit("BOX_VISION network must remain tcp")
if vision["flow"] != "xtls-rprx-vision":
    raise SystemExit("BOX_VISION flow must remain xtls-rprx-vision")
if not fall["cipher"].startswith("2022-blake3-"):
    raise SystemExit("FALL_BOX must remain a Shadowsocks 2022 cipher")
if not re.fullmatch(r"[A-Za-z0-9_-]+", vision["public_key"]):
    raise SystemExit("BOX_VISION Reality public key has an invalid shape")
if not re.fullmatch(r"[0-9a-fA-F]+", vision["short_id"]):
    raise SystemExit("BOX_VISION Reality short ID has an invalid shape")

profile = f'''# Shadowrocket local profile converted from 未竟.yaml
# SECURITY: contains private proxy credentials; do not commit or share.
# The current airport subscription returns HTTP 403.
# Import or substitute a working subscription before using BEST_JC/FALL_BOX.

[General]
bypass-system = true
ipv6 = false
prefer-ipv6 = false

[Proxy]
FALL_BOX = ss, {fall['server']}, {fall['port']}, encrypt-method={fall['cipher']}, password={fall['password']}, udp-relay=true, chain=BEST_JC
BOX_VISION = vless, {vision['server']}, {vision['port']}, "{vision['uuid']}", transport=tcp, flow={vision['flow']}, public-key="{vision['public_key']}", short-id={vision['short_id']}, udp=true, over-tls=true, sni={vision['sni']}, fingerprint={vision['fingerprint']}

[Proxy Group]
BEST_JC = url-test, policy-regex-filter=^(?!(?:BOX_VISION|FALL_BOX)$)(?!.*(?:限速|应急|测试)).+$, url=https://www.gstatic.com/generate_204, interval=300, tolerance=50, timeout=5
BOX_FIRST = fallback, BOX_VISION, FALL_BOX, url=https://www.gstatic.com/generate_204, interval=300, timeout=5
PROXY = select, BOX_FIRST, FALL_BOX, BEST_JC

[Rule]
RULE-SET,https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/ai-shadowrocket.list,PROXY
RULE-SET,https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/proxy-shadowrocket.list,PROXY
RULE-SET,https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/direct-shadowrocket.list,DIRECT
RULE-SET,https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Lan/Lan.list,DIRECT
AND,((SRC-IP-CIDR,192.168.100.186/32),(DST-PORT,1000-63000)),DIRECT
DOMAIN-SUFFIX,pingbox.top,DIRECT
DOMAIN-SUFFIX,msgbox.top,DIRECT
DOMAIN-SUFFIX,cdn-apple.com,DIRECT
DOMAIN-SUFFIX,aaplimg.com,DIRECT
DOMAIN-SUFFIX,mzstatic.com,DIRECT
DOMAIN-SUFFIX,apple.com,DIRECT
DOMAIN-SUFFIX,icloud.com,DIRECT
DOMAIN-SUFFIX,icloud-content.com,DIRECT
RULE-SET,https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/ChinaMax/ChinaMax.list,DIRECT
GEOIP,CN,DIRECT,no-resolve
FINAL,PROXY
'''

for section in ("General", "Proxy", "Proxy Group", "Rule"):
    if profile.count(f"[{section}]") != 1:
        raise SystemExit(f"invalid section count: {section}")

required_prefixes = (
    "FALL_BOX = ss,",
    "BOX_VISION = vless,",
    "BEST_JC = url-test, policy-regex-filter=",
    "BOX_FIRST = fallback, BOX_VISION, FALL_BOX,",
    "PROXY = select, BOX_FIRST, FALL_BOX, BEST_JC",
)
for prefix in required_prefixes:
    if not any(line.startswith(prefix) for line in profile.splitlines()):
        raise SystemExit(f"required profile structure missing: {prefix.split(' =')[0]}")

if "BEST_JC = url-test, regex=" in profile:
    raise SystemExit("legacy BEST_JC regex option key found")

banned_patterns = (
    r"(?m)^(?:port:|socks-port:|tun:|sniffer:|dns:|proxy-providers:|proxies:|proxy-groups:|rule-providers:|rules:)",
    r"(?m)(?:^|,)GEOSITE,",
    r"(?m)(?:^|,)MATCH,",
    r"force-remote-dns",
    r"(?m)^(?:dns-server|hijack-dns|always-real-ip|fallback-dns-server)\s*=",
)
for pattern in banned_patterns:
    if re.search(pattern, profile):
        raise SystemExit("out-of-scope or Mihomo-only setting found")

rule_markers = (
    "ai-shadowrocket.list,PROXY",
    "proxy-shadowrocket.list,PROXY",
    "direct-shadowrocket.list,DIRECT",
    "/Lan/Lan.list,DIRECT",
    "AND,((SRC-IP-CIDR,192.168.100.186/32),(DST-PORT,1000-63000)),DIRECT",
    "DOMAIN-SUFFIX,cdn-apple.com,DIRECT",
    "/ChinaMax/ChinaMax.list,DIRECT",
    "GEOIP,CN,DIRECT,no-resolve",
    "FINAL,PROXY",
)
positions = [profile.index(marker) for marker in rule_markers]
if positions != sorted(positions):
    raise SystemExit("routing rules are out of order")

active_lines = [
    line.strip()
    for line in profile.splitlines()
    if line.strip() and not line.lstrip().startswith("#")
]
if active_lines[-1] != "FINAL,PROXY":
    raise SystemExit("FINAL,PROXY is not the last active line")

fd, temporary_name = tempfile.mkstemp(
    prefix=".未竟.conf.", suffix=".tmp", dir=target.parent
)
temporary = Path(temporary_name)
try:
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(profile)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary, 0o600)
    os.replace(temporary, target)
finally:
    temporary.unlink(missing_ok=True)

print("rendered and structurally validated 未竟.conf")
PY
```

Expected:

```text
rendered and structurally validated 未竟.conf
```

No proxy value or rendered proxy line is printed.

- [ ] **Step 2: Confirm atomic cleanup and private permissions**

Run:

```bash
test -s 未竟.conf
! find . -maxdepth 1 -name '.未竟.conf.*.tmp' -print -quit | grep -q .
test "$(stat -f '%Lp' 未竟.conf)" = "600"
```

Expected: exit 0 with no temporary file and mode `0600`.

There is no commit for this task. `未竟.conf` must stay ignored and untracked.

---

### Task 3: Validate the Profile and Public Rule Sources

**Files:**
- Verify locally: `未竟.conf`
- Verify remotely: five public GitHub Raw rule-set URLs
- Regression test: `tests/test_convert_rules.py`

**Interfaces:**
- Consumes: the rendered `未竟.conf` from Task 2.
- Produces: structural, ordering, remote-availability, regression, and Git-safety evidence without exposing private values.

- [ ] **Step 1: Verify sections, public names, and terminal rule**

Run:

```bash
for section in General Proxy 'Proxy Group' Rule; do
  test "$(rg -c "^\\[$section\\]$" 未竟.conf)" -eq 1
done
rg -q '^FALL_BOX = ss,' 未竟.conf
rg -q '^BOX_VISION = vless,' 未竟.conf
rg -q '^BEST_JC = url-test, policy-regex-filter=' 未竟.conf
! rg -q '^BEST_JC = url-test, regex=' 未竟.conf
rg -q '^BOX_FIRST = fallback, BOX_VISION, FALL_BOX,' 未竟.conf
rg -q '^PROXY = select, BOX_FIRST, FALL_BOX, BEST_JC$' 未竟.conf
test "$(awk 'NF && $1 !~ /^#/ {last=$0} END {print last}' 未竟.conf)" = 'FINAL,PROXY'
```

Expected: exit 0 without printing profile contents.

- [ ] **Step 2: Verify excluded configuration stays excluded**

Run:

```bash
! rg -q '^(port:|socks-port:|tun:|sniffer:|dns:|proxy-providers:|proxies:|proxy-groups:|rule-providers:|rules:)' 未竟.conf
! rg -q '(^|,)GEOSITE,' 未竟.conf
! rg -q '(^|,)MATCH,' 未竟.conf
! rg -q 'force-remote-dns' 未竟.conf
! rg -q '^(dns-server|hijack-dns|always-real-ip|fallback-dns-server)\s*=' 未竟.conf
```

Expected: exit 0; no Mihomo-only or DNS configuration is present.

- [ ] **Step 3: Verify rule order using public markers only**

Run:

```bash
python3 - <<'PY'
from pathlib import Path

text = Path("未竟.conf").read_text(encoding="utf-8")
markers = (
    "ai-shadowrocket.list,PROXY",
    "proxy-shadowrocket.list,PROXY",
    "direct-shadowrocket.list,DIRECT",
    "/Lan/Lan.list,DIRECT",
    "AND,((SRC-IP-CIDR,192.168.100.186/32),(DST-PORT,1000-63000)),DIRECT",
    "DOMAIN-SUFFIX,cdn-apple.com,DIRECT",
    "/ChinaMax/ChinaMax.list,DIRECT",
    "GEOIP,CN,DIRECT,no-resolve",
    "FINAL,PROXY",
)
positions = [text.index(marker) for marker in markers]
if positions != sorted(positions):
    raise SystemExit("rule order validation failed")
print("rule order valid")
PY
```

Expected:

```text
rule order valid
```

- [ ] **Step 4: Check all public remote rule sources by label**

Run in `zsh`:

```bash
urls=(
  'https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/ai-shadowrocket.list'
  'https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/proxy-shadowrocket.list'
  'https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/direct-shadowrocket.list'
  'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Lan/Lan.list'
  'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/ChinaMax/ChinaMax.list'
)
labels=(ai proxy direct lan china)
for i in {1..5}; do
  code=$(curl -L -sS -o /dev/null -w '%{http_code}' "${urls[$i]}")
  test "$code" = "200"
  printf '%s %s\n' "${labels[$i]}" "$code"
done
```

Expected:

```text
ai 200
proxy 200
direct 200
lan 200
china 200
```

- [ ] **Step 5: Run the repository regression tests**

Run:

```bash
python3 -m pytest tests/test_convert_rules.py -q
```

Expected:

```text
14 passed
```

- [ ] **Step 6: Confirm Git safety and preserve the source**

Run:

```bash
test -s 未竟.yaml
test -s 未竟.conf
git check-ignore -q 未竟.yaml
git check-ignore -q 未竟.conf
! git ls-files --error-unmatch 未竟.conf >/dev/null 2>&1
! git diff --cached --name-only | rg -q '^(未竟\.yaml|未竟\.conf)$'
git status --short --branch
```

Expected: exit 0; the source still exists, the destination is ignored and untracked, and neither private profile is staged.

There is no commit for this task because the only new artifact is private.

---

### Task 4: Complete the Shadowrocket App Acceptance Gate

**Files:**
- Import locally: absolute path to `未竟.conf`
- Preserve locally: `未竟.yaml`

**Interfaces:**
- Consumes: the structurally validated profile from Task 3.
- Produces: user-confirmed app compatibility for the primary path, plus an explicit record of the subscription-dependent checks that remain deferred.

- [ ] **Step 1: Hand off the absolute destination path without showing contents**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
print(Path("未竟.conf").resolve())
PY
```

Expected: one absolute path ending in `/未竟.conf`.

- [ ] **Step 2: Import and inspect the profile in Shadowrocket**

The user performs these checks in the app:

1. Import `未竟.conf` and confirm no syntax error is reported.
2. Confirm `BOX_VISION` and `FALL_BOX` are visible.
3. Confirm `BEST_JC`, `BOX_FIRST`, and `PROXY` are visible.
4. Confirm the five remote rule resources download without an error.

Expected: all items are present. If Reality or proxy-chain parameters are normalized or rejected, record the exact app error and adjust only those fields; do not broaden the profile scope.

- [ ] **Step 3: Verify the currently usable primary path**

In Shadowrocket, select `PROXY -> BOX_FIRST`, connect, and confirm the selected member is `BOX_VISION`. Test an ordinary overseas HTTPS destination and inspect the request log.

Expected: the request succeeds through `BOX_VISION`.

- [ ] **Step 4: Verify representative routing decisions**

Use the Shadowrocket request log to check:

1. One AI domain matches the AI remote rule set and uses `PROXY`.
2. One common overseas service matches the proxy remote rule set and uses `PROXY`.
3. One curated mainland service matches the direct remote rule set and uses `DIRECT`.
4. One private LAN destination uses `DIRECT`.
5. An unmatched overseas destination reaches `FINAL,PROXY`.

Expected: all five decisions match the configured policies.

- [ ] **Step 5: Record the subscription-dependent deferred checks**

Do not mark `BEST_JC` or `FALL_BOX` operational in this delivery. The handoff must state that these checks require a replacement subscription:

1. Import or substitute a working subscription in Shadowrocket.
2. Confirm `BEST_JC` includes eligible subscription nodes.
3. Confirm it excludes node names containing `限速`, `应急`, or `测试` and excludes `BOX_VISION` and `FALL_BOX`.
4. Confirm `BEST_JC` performs URL testing.
5. Confirm `FALL_BOX` connects through the `BEST_JC` upstream chain.

Expected: these are explicitly deferred, not silently reported as passing.

- [ ] **Step 6: Finish without deleting or committing private files**

Report:

- automated checks that passed;
- Shadowrocket checks that passed;
- the known 403 subscription limitation;
- deferred `BEST_JC` and `FALL_BOX` checks;
- confirmation that `未竟.yaml` remains intact and `未竟.conf` remains ignored.

Do not run `git add`, `git commit`, `git push`, or delete either private profile.
