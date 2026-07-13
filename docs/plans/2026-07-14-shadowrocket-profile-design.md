# Shadowrocket Profile Conversion Design

## Goal

Convert the local, sensitive `路由.yaml` Mihomo configuration into an importable
Shadowrocket profile named `路由.conf`. Preserve the original proxy selection and
routing intent while replacing the three project rule providers with the
Shadowrocket rule sets hosted in this repository on GitHub.

The resulting profile remains local. It contains credentials and must not be
committed or pushed.

## Safety Boundary

- Keep the existing subscription URL as a comment because it currently returns
  HTTP 403. The user will replace it with a working Shadowrocket subscription.
- Preserve local proxy credentials in `路由.conf` only.
- Add `路由.conf` to the local ignore rules before creating it.
- Never copy subscription tokens, passwords, UUIDs, or Reality keys into design
  documents, tests, command output, commits, or chat responses.
- Delete the untracked `路由.yaml` only after `路由.conf` has been created and
  validated.

## Chosen Approach

Use Shadowrocket's native text profile format rather than relying on its partial
Clash YAML compatibility. Build four sections:

```text
[General]
[Proxy]
[Proxy Group]
[Rule]
```

Mihomo-only keys such as `external-controller`, `tun`, `sniffer`, `fake-ip`,
`proxy-providers`, `rule-providers`, and `GEOSITE` are removed or replaced with
Shadowrocket-native equivalents.

## General Settings

Translate the compatible intent of the current profile:

- Keep IPv6 disabled.
- Keep system bypass and private/LAN bypass behavior.
- Use the existing mainland DNS resolver choices.
- Keep DNS hijacking for common public DNS endpoints.
- Use `force-remote-dns` on the AI and overseas remote rule sets to preserve the
  intent of resolving proxied services remotely.

Shadowrocket owns the iOS VPN tunnel, so the Mihomo TUN device, controller,
sniffer, and fake-IP implementation details are not copied.

## Proxies and Groups

Convert the two locally defined proxies into Shadowrocket proxy definitions:

- `FALL_BOX`: Shadowsocks 2022, UDP enabled, retaining the intent to use
  `BEST_JC` as its upstream proxy chain.
- `BOX_VISION`: VLESS over TCP with Reality, XTLS Vision, UDP, SNI, public key,
  short ID, and browser fingerprint settings preserved.

Keep the original group structure:

- `BEST_JC`: URL test across subscription nodes, excluding names containing
  the existing throttled/emergency/test keywords.
- `BOX_FIRST`: fallback in the original `BOX_VISION`, then `FALL_BOX` order.
- `PROXY`: selectable group containing `BOX_FIRST`, `FALL_BOX`, and `BEST_JC`.

The inaccessible subscription URL remains in a warning comment. After the user
adds or replaces the subscription in Shadowrocket, `BEST_JC` uses a regex-based
group to select eligible subscription nodes.

## Rule Mapping

Preserve the original top-to-bottom routing semantics:

1. AI services use `PROXY` through the repository's
   `ai-shadowrocket.list` GitHub Raw URL, with remote DNS forced.
2. Common overseas services use `PROXY` through
   `proxy-shadowrocket.list`, with remote DNS forced.
3. Curated mainland services use `DIRECT` through
   `direct-shadowrocket.list`.
4. Private domains and LAN networks use the Shadowrocket-specific upstream
   `Lan.list`.
5. Preserve the custom source-IP and destination-port logical direct rule.
6. Preserve the two custom direct domains.
7. Preserve all existing Apple and Apple CDN direct suffix rules.
8. Replace `GEOSITE,cn` with the Shadowrocket-specific upstream
   `ChinaMax.list`.
9. Keep `GEOIP,CN,DIRECT,no-resolve`.
10. Replace Mihomo's `MATCH,PROXY` with Shadowrocket's `FINAL,PROXY`.

## Validation

Validate the local profile without exposing its values:

- `路由.conf` exists, is non-empty, and `路由.yaml` no longer exists.
- `[General]`, `[Proxy]`, `[Proxy Group]`, and `[Rule]` each occur once.
- The three repository Raw URLs, the LAN URL, and the ChinaMax URL are present.
- Required local proxy and proxy group names are present.
- Routing rules appear in the designed order and end with `FINAL,PROXY`.
- No Mihomo YAML section keys or Clash provider references remain.
- Git confirms `路由.conf` is ignored and no sensitive profile is staged or
  tracked.

Because Shadowrocket is not available in this environment, the final handoff
must note that the file has been structurally validated but still requires an
import test in the Shadowrocket app, especially for the proxy-chain and Reality
node fields.
