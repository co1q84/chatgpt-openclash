# Shadowrocket Profile Conversion Implementation Plan

> **SUPERSEDED — DO NOT EXECUTE.** This document is retained only for history and contains legacy, non-minimal guidance. Use the [canonical minimal Shadowrocket profile design](../superpowers/specs/2026-07-14-minimal-shadowrocket-profile-design.md) and [canonical minimal Shadowrocket implementation plan](../superpowers/plans/2026-07-14-minimal-shadowrocket-profile.md) instead.

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the ignored local `路由.yaml` Mihomo profile with an ignored local `路由.conf` Shadowrocket profile that preserves its proxy groups and routing behavior while using GitHub-hosted Shadowrocket rule sets.

**Architecture:** Perform a one-time, in-memory conversion so secrets are never emitted in command output or copied into tracked files. Render a native Shadowrocket profile with `[General]`, `[Proxy]`, `[Proxy Group]`, and `[Rule]` sections, validate only structure and non-sensitive constants, then remove the old YAML after validation succeeds.

**Tech Stack:** Shadowrocket text profile syntax, shell structural assertions, Git ignore rules

---

> **Execution note:** Run this plan in the current workspace, not a worktree. Both
> the input and output are intentionally ignored local files, and the desired
> output must remain in the user's current workspace. Do not commit the local
> profile or `.gitignore` changes.

### Task 1: Protect the new local profile from Git

**Files:**
- Modify locally, do not commit: `.gitignore`
- Verify: `路由.yaml`

**Step 1: Confirm the source is present and ignored**

Run:

```bash
test -s 路由.yaml
git check-ignore -q 路由.yaml
```

Expected: both commands exit 0 without printing the file contents.

**Step 2: Add the destination to the existing local ignore changes**

Use `apply_patch` to append this line if it is not already present:

```gitignore
路由.conf
```

Do not stage or commit `.gitignore`; it already contains user-owned local
changes.

**Step 3: Verify the destination path is ignored**

Run:

```bash
git check-ignore -q 路由.conf
```

Expected: exit 0.

### Task 2: Render the Shadowrocket profile without exposing credentials

**Files:**
- Read locally without emitting: `路由.yaml`
- Create locally, do not commit: `路由.conf`

**Step 1: Extract sensitive values in memory**

Read `路由.yaml` through tool orchestration without appending the command result
to visible tool output. Extract these fields by their YAML context:

- Original subscription URL.
- `FALL_BOX`: server, port, cipher, password.
- `BOX_VISION`: server, port, UUID, network, flow, SNI, client fingerprint,
  Reality public key, and Reality short ID.

Abort if any required field is missing. Do not print field values.

**Step 2: Build the native Shadowrocket structure in memory**

Render this shape, substituting extracted values only in the local output:

```ini
# Shadowrocket local profile
# SECURITY: contains private proxy credentials; do not commit or share.
# Subscription currently returns HTTP 403. Replace/import it in Shadowrocket:
# SUBSCRIPTION_URL = <source subscription URL>

[General]
bypass-system = true
ipv6 = false
prefer-ipv6 = false
dns-server = 223.5.5.5, 119.29.29.29, 180.76.76.76
dns-direct-system = false
dns-direct-fallback-proxy = false
icmp-auto-reply = true
private-ip-answer = true
skip-proxy = 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.168.0.0/16, ::1/128, fc00::/7, fe80::/10, localhost, *.lan, *.local
bypass-tun = 239.255.255.250/32
hijack-dns = 8.8.8.8:53, 1.1.1.1:53

[Proxy]
FALL_BOX = ss, <server>, <port>, encrypt-method=<cipher>, password=<password>, udp-relay=true, chain=BEST_JC
BOX_VISION = vless, <server>, <port>, "<uuid>", transport=tcp, flow=xtls-rprx-vision, public-key="<public key>", short-id=<short id>, udp=true, over-tls=true, sni=<SNI>, fingerprint=<fingerprint>

[Proxy Group]
BEST_JC = url-test, regex=^((?!(限速|应急|测试)).)*$, url=https://www.gstatic.com/generate_204, interval=300, tolerance=50, timeout=5
BOX_FIRST = fallback, BOX_VISION, FALL_BOX, url=https://www.gstatic.com/generate_204, interval=300, timeout=5
PROXY = select, BOX_FIRST, FALL_BOX, BEST_JC

[Rule]
# rules inserted in Task 3
```

Use the Shadowrocket-native `chain` field to retain the existing proxy-pass
intent. The app import test remains authoritative for this field and the
Reality parameter names.

**Step 3: Create `路由.conf` through `apply_patch` orchestration**

Construct and apply the patch in memory. Do not return the patch text, source
text, or rendered profile as tool output. Return only a success marker and byte
count.

**Step 4: Verify the four sections and proxy names without printing values**

Run:

```bash
test -s 路由.conf
for section in General Proxy 'Proxy Group' Rule; do
  test "$(rg -c "^\\[$section\\]$" 路由.conf)" -eq 1
done
rg -q '^FALL_BOX = ss,' 路由.conf
rg -q '^BOX_VISION = vless,' 路由.conf
rg -q '^BEST_JC = url-test,' 路由.conf
rg -q '^BOX_FIRST = fallback,' 路由.conf
rg -q '^PROXY = select,' 路由.conf
```

Expected: all commands exit 0 and print no credentials.

### Task 3: Add the equivalent Shadowrocket routing rules

**Files:**
- Modify locally, do not commit: `路由.conf`

**Step 1: Add the GitHub-backed rules in original order**

Replace the placeholder under `[Rule]` with:

```ini
# AI / LLM and common overseas services: proxy first
RULE-SET,https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/ai-shadowrocket.list,PROXY,force-remote-dns
RULE-SET,https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/proxy-shadowrocket.list,PROXY,force-remote-dns

# Mainland e-commerce, banking/payment, and video services: direct
RULE-SET,https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/direct-shadowrocket.list,DIRECT

# Private domains and LAN networks: direct
RULE-SET,https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Lan/Lan.list,DIRECT

# Preserve local custom routing
AND,((SRC-IP-CIDR,192.168.100.186/32),(DST-PORT,1000-63000)),DIRECT
DOMAIN-SUFFIX,pingbox.top,DIRECT
DOMAIN-SUFFIX,msgbox.top,DIRECT

# Apple system and CDN traffic: direct
DOMAIN-SUFFIX,cdn-apple.com,DIRECT
DOMAIN-SUFFIX,aaplimg.com,DIRECT
DOMAIN-SUFFIX,mzstatic.com,DIRECT
DOMAIN-SUFFIX,apple.com,DIRECT
DOMAIN-SUFFIX,icloud.com,DIRECT
DOMAIN-SUFFIX,icloud-content.com,DIRECT

# Mainland fallback: domains, then IPs
RULE-SET,https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/ChinaMax/ChinaMax.list,DIRECT
GEOIP,CN,DIRECT,no-resolve

# Everything else: proxy
FINAL,PROXY
```

**Step 2: Validate remote URLs without printing their content**

Run HTTP status checks for the five public Raw URLs. Use labels rather than
printing full URLs or downloaded rule contents.

Expected: each URL returns HTTP 200.

**Step 3: Verify rule order and terminal rule**

Use a non-secret parser or line-number assertions to confirm this order:

```text
ai-shadowrocket < proxy-shadowrocket < direct-shadowrocket < Lan < custom AND
< Apple rules < ChinaMax < GEOIP CN < FINAL
```

Run:

```bash
test "$(awk 'NF && $1 !~ /^#/ {last=$0} END {print last}' 路由.conf)" = 'FINAL,PROXY'
```

Expected: exit 0.

### Task 4: Remove the old YAML only after validation

**Files:**
- Delete locally: `路由.yaml`
- Preserve locally: `路由.conf`

**Step 1: Run the complete structural safety check**

Run checks that do not display profile lines:

```bash
test -s 路由.conf
git check-ignore -q 路由.conf
! git ls-files --error-unmatch 路由.conf >/dev/null 2>&1
! rg -q '^(port:|socks-port:|tun:|sniffer:|dns:|proxy-providers:|proxies:|proxy-groups:|rule-providers:|rules:)' 路由.conf
! rg -q '(^|,)MATCH,' 路由.conf
! rg -q 'GEOSITE,' 路由.conf
```

Expected: exit 0.

**Step 2: Delete the ignored source YAML**

After all checks pass, remove `路由.yaml` and verify:

```bash
test ! -e 路由.yaml
test -s 路由.conf
```

Expected: both commands exit 0.

**Step 3: Confirm no sensitive artifact is staged or tracked**

Run:

```bash
git status --short
git diff --cached --name-only
```

Expected: `.gitignore` may remain modified locally; neither `路由.yaml` nor
`路由.conf` appears as staged or untracked output.

**Step 4: Hand off for app-level validation**

Report the absolute local path to `路由.conf`, the structural checks performed,
and these two manual follow-ups:

1. Replace/import the subscription in Shadowrocket and confirm `BEST_JC`
   populates eligible nodes.
2. Import the profile and test `BOX_VISION` Reality plus `FALL_BOX` proxy-pass;
   adjust fields in the app if the installed Shadowrocket version normalizes
   parameter names differently.

Do not commit or push anything after creating the sensitive local profile.
