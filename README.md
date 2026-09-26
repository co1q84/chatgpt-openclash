# ChatGPT OpenClash & Shadowrocket Rules

这个仓库维护三类 OpenClash/Mihomo 和 Shadowrocket 规则：

- `ai.txt`：AI 相关域名，走代理。
- `proxy.txt`：常用海外服务厂商域名，走代理。
- `direct.txt`：国内视频、银行、支付及华为手机/鸿蒙系统服务等域名，直连。

## 文件说明

- `chatgpt.list`：本地维护的 AI 补充规则。
- `ai.sources.txt`：外部 AI 规则源，每行一个 URL。
- `proxy.list`：本地维护的常用海外服务厂商代理补充规则。
- `proxy.sources.txt`：外部常用海外服务厂商规则源，每行一个 URL。
- `direct.list`：本地维护的电商、银行/支付、国内视频、华为手机/鸿蒙系统服务直连补充规则。
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

## 参考源与兼容范围

新增 [LingJingMaster/Shadowrocket-Rules](https://github.com/LingJingMaster/Shadowrocket-Rules) 作为补充源：

| 上游文件 | 本项目归类 | 处理方式 |
| --- | --- | --- |
| `AI.list` | `ai.sources.txt` | 提取精确域名和域名后缀，保留 `behavior: domain` 接口 |
| `Google.list` | `proxy.sources.txt` | 保留域名、关键词及 IP 规则；IPv6 网段统一为 `IP-CIDR6` |

沿用已有 AI 转换边界：上游 AI 的关键词与 IP 规则不进入 `ai.txt` 或 `ai-shadowrocket.list`，不把关键词错误扩大为域名后缀。两个客户端仍使用同一份 AI 域名集合。

这里只合并规则集，不导入上游完整配置中的 DNS、HTTPDNS 拦截、MITM、重写、地区策略组或兜底策略。Apple、邮件、香港银行及券商需要单独决定出口，暂不并入现有分类。新增源的 MIT 许可见 [第三方许可](THIRD_PARTY_NOTICES.md)。

## 国内应用加载慢时怎么检查

目标是让国内请求使用本地出口和合适的国内 DNS，同时保留海外服务的代理分流。规则集只决定路由，不会自动修改客户端的 DNS、运行模式或其他规则。

1. 确认客户端使用规则模式。选了全局代理时，这里的 `DIRECT` 分流可能不会生效。
2. 在同一网络下，对比关闭代理和开启规则模式时的同一个操作；查看慢请求的域名、命中规则和最终出口。命中 `PROXY` / `MATCH` / `FINAL` 的国内请求，先补精确直连例外；已经命中 `DIRECT` 的请求，继续核对 DNS 耗时和解析结果。
3. 精确直连例外放在本项目 AI / proxy 规则之前；本项目 `direct` 集合和通用中国域名集放在泛化海外规则与兜底规则之前。仅靠 `GEOIP,CN` 无法覆盖使用境外 CDN 的国内服务；也不要为了变快直接把所有未知流量改成直连。
4. 国内直连域名优先使用当前网络的系统 DNS 或可达的国内 DNS。Mihomo 可用 `nameserver-policy` 按域名分配解析器，并用 `direct-nameserver` 指定直连出口解析器，具体以 [Mihomo DNS 文档](https://wiki.metacubex.one/config/dns/) 为准。Stash 和 Shadowrocket 应使用各自支持的设置，不能直接照搬 Mihomo 字段。
5. 如果另用了 HTTPDNS 拦截规则，检查慢请求是否被拒绝。参考源专门将微信 HTTPDNS 前置直连；本项目未启用此拦截，也不建议在没有请求记录时整套加入。Fake-IP 兼容问题同样应针对具体域名验证，再添加例外。

每次只改一个因素，重连后复测同一操作。新增规则源不代表已经解决手机上的加载慢，仍需要客户端请求记录和实测确认。

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
- 直连域名：仅放电商、银行/支付、国内视频、华为手机/鸿蒙系统服务，规则加到 `direct.list`，或把新的同类上游 URL 加到 `direct.sources.txt`。

## 本地生成

```bash
python3 scripts/convert_chatgpt_to_ai.py
```

生成后检查：

```bash
pytest tests/test_convert_rules.py -q
```
