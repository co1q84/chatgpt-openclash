# Service Proxy Rules Design

## Goal

Restore the ruleset model to three explicit routing groups:

- `ai.txt` for AI services that should use the proxy.
- `proxy.txt` for common non-AI overseas service vendors that usually need a proxy to work reliably.
- `direct.txt` for mainland e-commerce, banking/payment, and video services that should use direct routing.

## Scope

`proxy` is a curated vendor collection, not a broad catch-all foreign-domain ruleset. It should include services such as Google, YouTube, X/Twitter, GitHub, Telegram, Meta, Netflix, Spotify, Cloudflare, Notion, and Vercel when those services are useful for normal daily use.

The proxy source list should avoid broad sources such as generic GFW or full proxy lists because those would turn `proxy` into a general overseas routing group.

## Architecture

The existing generator already supports AI domain payloads and classical rule-provider payloads. Extend the current `main()` flow to generate a third classical provider:

```text
proxy.list + proxy.sources.txt -> proxy.txt
```

`ai.txt` keeps using domain behavior and is ordered before `proxy.txt` in OpenClash/Mihomo examples. `proxy.txt` and `direct.txt` use classical behavior so they can preserve `DOMAIN`, `DOMAIN-SUFFIX`, `DOMAIN-KEYWORD`, and IP route rules from upstream vendor sources.

## Files

- `proxy.list`: local proxy supplements for stable common vendor domains.
- `proxy.sources.txt`: vendor-level upstream rule sources, one URL per line.
- `proxy.txt`: generated proxy provider payload.
- `scripts/convert_chatgpt_to_ai.py`: generate `proxy.txt` alongside `ai.txt` and `direct.txt`.
- `tests/test_convert_rules.py`: assert proxy source parsing and key local proxy coverage.
- `README.md`: document the three-rule model and usage order.

## Rule Order

Recommended routing order:

```yaml
rules:
  - RULE-SET,ai,PROXY
  - RULE-SET,proxy,PROXY
  - RULE-SET,direct,DIRECT
```

`ai` stays first so AI services are handled by the dedicated AI provider. `proxy` follows for common overseas services. `direct` remains scoped to mainland services and should stay before broader direct or China rules in a user's full configuration.

## Testing

Add focused tests for:

- Generator support for building `proxy.txt` from `proxy.list` and `proxy.sources.txt`.
- Local proxy rules covering representative common services: Google, YouTube, X/Twitter, GitHub, Telegram, Meta, Netflix, Spotify, Cloudflare, Notion, and Vercel.
- Existing direct and AI parser behavior remaining unchanged.

Run:

```bash
python3 scripts/convert_chatgpt_to_ai.py
pytest tests/test_convert_rules.py -q
```
