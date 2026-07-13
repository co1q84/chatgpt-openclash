# ChatGPT OpenClash & Shadowrocket Rules

这个仓库维护三类 OpenClash/Mihomo 和 Shadowrocket 规则：

- `ai.txt`：AI 相关域名，走代理。
- `proxy.txt`：常用海外服务厂商域名，走代理。
- `direct.txt`：国内视频、银行、支付等域名，直连。

## 文件说明

- `chatgpt.list`：本地维护的 AI 补充规则。
- `ai.sources.txt`：外部 AI 规则源，每行一个 URL。
- `proxy.list`：本地维护的常用海外服务厂商代理补充规则。
- `proxy.sources.txt`：外部常用海外服务厂商规则源，每行一个 URL。
- `direct.list`：本地维护的电商、银行/支付、国内视频直连补充规则。
- `direct.sources.txt`：外部电商、银行/支付、国内视频规则源，每行一个 URL。
- `ai.txt` / `proxy.txt` / `direct.txt`：生成的 OpenClash/Mihomo 规则集。
- `ai-shadowrocket.list` / `proxy-shadowrocket.list` / `direct-shadowrocket.list`：生成的 Shadowrocket 远程 `RULE-SET` 规则集。
- `scripts/convert_chatgpt_to_ai.py`：拉取外部规则、合并本地规则、去重并统一生成两种客户端格式。
- `.github/workflows/sync-upstream.yml`：每天自动更新规则，也支持手动运行。

## OpenClash/Mihomo 引用

```yaml
rule-providers:
  ai:
    type: http
    behavior: domain
    url: "https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/ai.txt"
    path: ./ruleset/ai.yaml
    interval: 86400

  proxy:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/proxy.txt"
    path: ./ruleset/proxy.yaml
    interval: 86400

  direct:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/direct.txt"
    path: ./ruleset/direct.yaml
    interval: 86400

rules:
  - RULE-SET,ai,PROXY
  - RULE-SET,proxy,PROXY
  - RULE-SET,direct,DIRECT
```

建议把这三条规则放在 `reject`、`cn`、`direct` 等通用规则前面，避免 AI 和常用海外服务域名被误判成直连，也避免国内视频和银行域名绕远。

## Shadowrocket 引用

在 Shadowrocket 的配置规则中加入：

```text
RULE-SET,https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/ai-shadowrocket.list,PROXY
RULE-SET,https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/proxy-shadowrocket.list,PROXY
RULE-SET,https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/direct-shadowrocket.list,DIRECT
```

也可在 Shadowrocket 界面中逐个添加 Raw 链接：规则类型选择 `RULE-SET`，AI 和常用海外服务选择你的代理策略，国内常用服务选择 `DIRECT`。规则文件本身不绑定策略，因此也可替换 `PROXY` 为自己的代理组名称。

建议按 AI、常用海外服务、国内直连的顺序放置，并位于更宽泛的通用规则和最终规则之前。

## 自动更新

GitHub Action 会在北京时间每天 08:00 左右运行一次：

```bash
python3 scripts/convert_chatgpt_to_ai.py
```

如果上游规则或本地源文件导致任一 OpenClash/Mihomo 或 Shadowrocket 生成文件变化，Action 会自动提交并推送全部同步结果。也可以在 GitHub 页面手动运行：

`Actions -> Sync fork and update rulesets -> Run workflow`

要增加规则：

- AI 域名：加到 `chatgpt.list`，或把新的上游 URL 加到 `ai.sources.txt`。
- 代理域名：仅放常用海外服务厂商，例如 Google、YouTube、X/Twitter、GitHub、Telegram、Meta、Netflix、Spotify、Cloudflare、Notion、Vercel。规则加到 `proxy.list`，或把新的厂商级上游 URL 加到 `proxy.sources.txt`。不要加入 GFW、通用 proxy、`geolocation-!cn` 这类泛化源。
- 直连域名：仅放电商、银行/支付、国内视频，规则加到 `direct.list`，或把新的同类上游 URL 加到 `direct.sources.txt`。

## 本地生成

```bash
python3 scripts/convert_chatgpt_to_ai.py
```

生成后检查：

```bash
pytest tests/test_convert_rules.py -q
```
