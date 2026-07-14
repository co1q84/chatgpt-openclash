# Minimal Shadowrocket Profile Design

## Goal

Convert the ignored local Mihomo profile `未竟.yaml` into an ignored local
Shadowrocket profile named `未竟.conf`. The first delivery preserves the current
proxy-policy structure and routing intent while using the Shadowrocket rule
lists published by this repository on GitHub.

The result is deliberately minimal. DNS, fake IP, TUN tuning, sniffing, MITM,
rewrites, scripts, local listener ports, controller settings, and other
Mihomo-specific runtime options are outside this delivery.

## Chosen Approach

Generate a native Shadowrocket text profile instead of relying on partial Clash
YAML compatibility. The profile has four sections:

```text
[General]
[Proxy]
[Proxy Group]
[Rule]
```

`[General]` contains only these non-DNS settings:

```ini
bypass-system = true
ipv6 = false
prefer-ipv6 = false
```

It does not introduce DNS servers, DNS interception, remote-DNS flags, or
fake-IP behavior.

### Alternatives Rejected

1. Import the Clash YAML directly. This is smaller mechanically but does not
   reliably translate Mihomo providers, Reality fields, proxy chaining, or
   remote rule providers.
2. Import nodes manually and generate only routing rules. This has a smaller
   configuration surface but fails the requirement to reproduce the current
   proxy policies in the converted profile.

## Security Boundary

- `未竟.yaml` and `未竟.conf` contain private proxy material and remain ignored
  by Git.
- No subscription token, password, UUID, Reality key, or complete node URL may
  be copied into this design, tests, terminal output, commits, or chat messages.
- Conversion must keep sensitive values in memory and write them only to the
  ignored destination profile.
- `未竟.yaml` is retained until `未竟.conf` passes structural checks and an app
  import test. Deleting the source is not part of the initial conversion unless
  the user requests it after successful import.

## Current Subscription Constraint

The subscription configured under the current Mihomo proxy provider returns
HTTP 403 when checked from this environment. The conversion therefore treats it
as a replace-later value instead of claiming that subscription-backed nodes are
available.

The destination profile includes a non-secret warning comment explaining that a
working subscription must be imported or substituted in Shadowrocket. It keeps
the `BEST_JC` group structure so eligible nodes can be selected after that
subscription is restored.

Until then:

- `BOX_VISION` is the usable local primary path.
- `BEST_JC` has no guaranteed eligible subscription nodes.
- `FALL_BOX` is structurally present but is not claimed to work because its
  upstream chain depends on `BEST_JC`.
- The usable minimal path is `PROXY -> BOX_FIRST -> BOX_VISION`.

## Proxy Definitions

Translate the two local proxies into Shadowrocket-native definitions without
changing their connection parameters:

- `BOX_VISION`: VLESS over TCP with Reality, XTLS Vision, UDP, SNI, public key,
  short ID, and client fingerprint preserved.
- `FALL_BOX`: Shadowsocks 2022 with UDP preserved and `BEST_JC` retained as its
  upstream proxy chain.

Shadowrocket app import and connection tests are authoritative for the exact
serialization of Reality and proxy-chain fields.

## Proxy Groups

Preserve the current group names, types, order, and health-test intent:

| Group | Shadowrocket type | Members and behavior |
| --- | --- | --- |
| `BEST_JC` | `url-test` | Select imported subscription nodes with a regex that excludes names containing `限速`, `应急`, or `测试`, and excludes the two local node names to avoid a proxy-chain cycle. Test `https://www.gstatic.com/generate_204` every 300 seconds with a 50 ms tolerance. |
| `BOX_FIRST` | `fallback` | Try `BOX_VISION` first, then `FALL_BOX`, testing `https://www.gstatic.com/generate_204` every 300 seconds. |
| `PROXY` | `select` | Offer `BOX_FIRST`, `FALL_BOX`, and `BEST_JC` in that order. |

The group design must prevent `BEST_JC` from selecting `FALL_BOX`; otherwise
`FALL_BOX -> BEST_JC -> FALL_BOX` would form a cycle.

## Routing Rules

Rules keep the original top-to-bottom intent. The three repository-owned rule
sets use their Shadowrocket-specific generated files:

```text
https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/ai-shadowrocket.list
https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/proxy-shadowrocket.list
https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/direct-shadowrocket.list
```

Private-network and mainland-domain fallbacks use the Shadowrocket rule lists
maintained by `blackmatrix7/ios_rule_script`:

```text
https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Lan/Lan.list
https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/ChinaMax/ChinaMax.list
```

The resulting order is:

1. Repository AI rule set -> `PROXY`.
2. Repository common-overseas rule set -> `PROXY`.
3. Repository curated-mainland rule set -> `DIRECT`.
4. LAN and private-network rule set -> `DIRECT`.
5. Preserve the existing custom source-IP and destination-port logical rule ->
   `DIRECT`.
6. Preserve the existing two custom direct-domain suffixes -> `DIRECT`.
7. Preserve the existing Apple and Apple-CDN direct suffixes -> `DIRECT`.
8. Shadowrocket mainland-domain rule set -> `DIRECT`.
9. `GEOIP,CN,DIRECT,no-resolve`.
10. `FINAL,PROXY`.

No rule receives `force-remote-dns` in this delivery because DNS behavior is
explicitly out of scope.

## Format Mapping

Mihomo-only structures are removed or replaced as follows:

| Mihomo input | Shadowrocket output |
| --- | --- |
| `proxies` | `[Proxy]` |
| `proxy-groups` | `[Proxy Group]` |
| `rule-providers` plus `RULE-SET` names | Full remote URLs in `[Rule]` |
| `GEOSITE,cn` | Remote `ChinaMax.list` rule set |
| `GEOIP,LAN` and private providers | Remote `Lan.list` rule set |
| `MATCH,PROXY` | `FINAL,PROXY` |
| `dialer-proxy: BEST_JC` | Shadowrocket upstream proxy chain targeting `BEST_JC` |
| DNS, TUN, sniffer, controller, ports | Omitted |

## Failure Handling

- Abort conversion if any required local-node field is missing; do not produce
  a partially credentialed node definition.
- Keep `未竟.yaml` untouched if rendering or structural validation fails.
- Report remote-rule download failures by rule-set label without printing
  private profile contents.
- Treat a successful text render as structural success only. Reality,
  Shadowsocks 2022, regex membership, and proxy chaining require validation in
  the installed Shadowrocket app.
- Do not represent `BEST_JC` or `FALL_BOX` as operational until a working
  subscription is available and the chain passes an app connection test.

## Validation

### Automated structural checks

- `未竟.conf` exists, is non-empty, ignored, and untracked.
- `[General]`, `[Proxy]`, `[Proxy Group]`, and `[Rule]` each occur once.
- Both proxy names and all three group names occur in the correct sections.
- Group order and membership match this design.
- All five public remote-rule URLs return HTTP 200.
- Rule order matches the ten routing stages above.
- The last active rule is exactly `FINAL,PROXY`.
- No Mihomo section key, named rule provider, `GEOSITE`, or `MATCH` remains.
- No DNS server, fake-IP, TUN, sniffer, MITM, rewrite, or script configuration is
  introduced.
- Neither sensitive profile is staged or tracked.

### Manual Shadowrocket checks

1. Import `未竟.conf` without a syntax error.
2. Confirm both local nodes and all three proxy groups are visible.
3. Select `PROXY -> BOX_FIRST` and verify `BOX_VISION` connects.
4. Confirm the five remote rule sets download successfully.
5. Use Shadowrocket request logs to verify representative AI and overseas
   domains use `PROXY`, while representative curated mainland and LAN targets
   use `DIRECT`.
6. After importing a working subscription, confirm `BEST_JC` contains eligible
   nodes, excludes the three configured name patterns and the two local node
   names, and performs URL testing.
7. Only after step 6 passes, verify `FALL_BOX` through the `BEST_JC` proxy chain.

## Deliverables

- Local ignored profile: `未竟.conf`.
- No tracked code or generated rule-set changes are needed for the minimal
  conversion.
- A short handoff listing the automated checks and remaining Shadowrocket app
  checks, without exposing credentials.
