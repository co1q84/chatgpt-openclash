# Shadowrocket Rules Design

## Goal

Generate three reusable Shadowrocket remote rule sets alongside the existing
OpenClash/Mihomo rule-provider files:

- `ai-shadowrocket.list` for AI services that should use a proxy.
- `proxy-shadowrocket.list` for common overseas services that should use a proxy.
- `direct-shadowrocket.list` for common mainland services that should use direct routing.

The files contain standard Shadowrocket `RULE-SET` entries without a routing
policy. The user selects `PROXY`, `DIRECT`, or another policy when adding the
remote rule set in Shadowrocket.

## Architecture

Keep one source and normalization pipeline for both clients:

```text
local .list files + external source URLs
                    |
            fetch, normalize, merge,
             preserve order, dedupe
                    |
          +---------+----------+
          |                    |
   OpenClash/Mihomo       Shadowrocket
   YAML payload files    plain RULE-SET files
```

Extend the existing Python generator rather than adding a second script or
parsing the generated YAML. Each rule group is built once and then rendered in
the two output formats. This keeps both clients synchronized and avoids
duplicated downloads or parsing behavior.

## Output Formats

The existing OpenClash/Mihomo files remain unchanged:

- `ai.txt`
- `proxy.txt`
- `direct.txt`

The new Shadowrocket files live in the repository root:

- `ai-shadowrocket.list`
- `proxy-shadowrocket.list`
- `direct-shadowrocket.list`

Shadowrocket rule sets contain one policy-free rule per line, for example:

```text
DOMAIN-SUFFIX,openai.com
DOMAIN,api.openai.com
DOMAIN-KEYWORD,openai
IP-CIDR,203.0.113.0/24,no-resolve
```

AI domain-provider entries such as `+.openai.com` are converted back to
`DOMAIN-SUFFIX,openai.com`. Plain AI domains become `DOMAIN,example.com`.
Classical proxy and direct entries retain their supported rule type and
parameters.

The Shadowrocket renderer only emits supported common rule types. Unsupported
source entries continue to be discarded during normalization rather than
producing invalid remote rules.

## Data Flow

For each group, the generator:

1. Reads locally maintained rules.
2. Downloads all configured external sources.
3. Normalizes source-specific syntax.
4. Merges local and external entries while preserving first-seen order.
5. Removes duplicates.
6. Writes the existing OpenClash/Mihomo output.
7. Writes the matching Shadowrocket output from the same normalized entries.

The generator remains deterministic: unchanged inputs produce byte-identical
outputs.

## Automation and Failure Handling

Continue using `.github/workflows/sync-upstream.yml` on its existing daily
schedule and manual trigger. The workflow runs the generator once, stages all
six generated files, and creates a commit only when at least one changes.

External download failures keep the current fail-fast behavior. If any source
cannot be fetched, generation exits before the workflow commits, preventing a
partial or silently truncated ruleset update.

## Documentation

Update `README.md` with:

- A description of the three Shadowrocket files.
- Raw GitHub URLs for adding them as remote `RULE-SET` entries.
- Instructions to assign `PROXY` to AI and overseas service rules and `DIRECT`
  to mainland service rules.
- The shared daily update behavior.

## Testing

Add focused tests that verify:

- AI `+.` entries convert to `DOMAIN-SUFFIX` rules.
- Plain AI entries convert to `DOMAIN` rules.
- Common classical types and optional parameters are preserved.
- Shadowrocket output contains neither `payload:` nor YAML quoting/indentation.
- Policies are not embedded in the generated rule sets.
- Duplicate rules preserve first-seen order.
- All three Shadowrocket files are generated from the same built entries as
  their OpenClash/Mihomo counterparts.
- Existing parser and generated-file behavior remains unchanged.

Verification runs the generator followed by the complete test suite.
