# ChatGPT OpenClash Rules

这个仓库只维护两类 OpenClash/Mihomo 规则：

- `ai.txt`：AI 相关域名，走代理。
- `direct.txt`：国内视频、银行、支付等域名，直连。

## 文件说明

- `chatgpt.list`：本地维护的 AI 补充规则。
- `ai.sources.txt`：外部 AI 规则源，每行一个 URL。
- `direct.list`：本地维护的电商、银行/支付、国内视频直连补充规则。
- `direct.sources.txt`：外部电商、银行/支付、国内视频规则源，每行一个 URL。
- `scripts/convert_chatgpt_to_ai.py`：拉取外部规则、合并本地规则、去重并生成 `ai.txt` 和 `direct.txt`。
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

  direct:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/direct.txt"
    path: ./ruleset/direct.yaml
    interval: 86400

rules:
  - RULE-SET,ai,PROXY
  - RULE-SET,direct,DIRECT
```

建议把这两条规则放在 `reject`、`cn`、`direct` 等通用规则前面，避免 AI 域名被误判成直连，也避免国内视频和银行域名绕远。

## 自动更新

GitHub Action 会在北京时间每天 08:00 左右运行一次：

```bash
python3 scripts/convert_chatgpt_to_ai.py
```

如果上游规则或本地源文件导致 `ai.txt` / `direct.txt` 变化，Action 会自动提交并推送更新。也可以在 GitHub 页面手动运行：

`Actions -> Sync fork and update rulesets -> Run workflow`

要增加规则：

- AI 域名：加到 `chatgpt.list`，或把新的上游 URL 加到 `ai.sources.txt`。
- 直连域名：仅放电商、银行/支付、国内视频，规则加到 `direct.list`，或把新的同类上游 URL 加到 `direct.sources.txt`。

## 本地生成

```bash
python3 scripts/convert_chatgpt_to_ai.py
```

生成后检查：

```bash
pytest tests/test_convert_rules.py -q
```
