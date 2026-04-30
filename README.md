# Chaptgpt分流规则

因Chatgpt香港节点不支持，所以独立创建了一份openclash分流规则

基础规则：ACL4SSR_Online_Full 全分组重度用户使用(与Github同步)  致谢：ACL4SSR

使用方法(到openclash配置文件处更新订阅链接)

    https://api.dler.io/sub?target=clash&new_name=true&url=你的订阅链接(需要使用URL编码，)&config=https%3A%2F%2Fraw.githubusercontent.com%2Fwgetnz%2Fchatgpt%2Fmain%2FFull.ini
    
控制面板中，Chatgpt选择节点选择，节点选择选择除中国地区（包含香港）的其他节点即可

如果更新规则后，仍提示地区不可用，请清除浏览器数据


如果发现新的域名,请提交Issues.


# 注意事项
## 自定义规则自动集成

这个仓库现在把规则分成三层：

- `proxy.list`：强制代理规则源，保留 `DOMAIN`、`DOMAIN-SUFFIX`、`DOMAIN-KEYWORD` 等 Clash 规则类型。
- `direct.list`：强制直连规则源。
- `ai.sources.txt`：外部 AI 规则源 URL。GitHub Action 会定时拉取这些源，自动合并到 `ai.txt`。

`chatgpt.list` 仍然作为你自己的 AI 规则补充源。如果外部源漏了某个域名，直接加到 `chatgpt.list`；如果找到更好的公共 AI 规则源，把 URL 加到 `ai.sources.txt`。

GitHub Action `.github/workflows/sync-upstream.yml` 会每天运行一次，也可以在 GitHub 的 **Actions -> Sync fork and update rulesets -> Run workflow** 手动运行。它会执行：

```bash
python3 scripts/convert_chatgpt_to_ai.py
```

并自动生成 OpenClash/Mihomo `rule-provider` 可引用的文件：

- `proxy.txt`
- `direct.txt`
- `ai.txt`

在 OpenClash/Mihomo 配置里可以这样引用：

```yaml
rule-providers:
  custom-proxy:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/proxy.txt"
    path: ./ruleset/custom-proxy.yaml
    interval: 86400

  custom-direct:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/direct.txt"
    path: ./ruleset/custom-direct.yaml
    interval: 86400

rules:
  - RULE-SET,ai,PROXY
  - RULE-SET,custom-proxy,PROXY
  - RULE-SET,custom-direct,DIRECT
```

其中 `ai` 对应：

```yaml
  ai:
    type: http
    behavior: domain
    url: "https://raw.githubusercontent.com/co1q84/chatgpt-openclash/main/ai.txt"
    path: ./ruleset/ai.yaml
    interval: 86400
```

建议把 `ai` 和 `custom-proxy` 放在 `reject`、`cn`、`direct` 等通用规则前面，避免 OpenAI/Google/GitHub 这类域名被后面的规则误判成直连。

1. fake-ip模式存在解析异常,目前未查明原因，请使用Redir-Host 兼容 模式（fake-ip偶尔会出现状况）

2. chatgpt 的网站启用了 http3 ，基于 quic ，基于 udp 如果出现还不能指定节点的情况，请开启UDP 代理，就算开启了 UDP 代理，因为 V2RAY 不支持 http3 的域名嗅探，所以基于域名的路由规则就失效了。不要全局，要不就只能基于 geoip 来。当然，最简单的办法还是把浏览器的 http3 支持给关了：（重要）

```csharp
    chrome://flags/#enable-quic
    edge://flags/#enable-quic
```
    
降级成 http1/2 就能让域名路由规则生效了。

订阅连接为 https://acl4ssr-sub.github.io/  接口,若担心安全问题，建议开启本地订阅，修改参数为 config=https%3A%2F%2Fraw.githubusercontent.com%2Fwgetnz%2Fchatgpt%2Fmain%2FFull.ini 即可，也可fork本项目，自行修改


tips:

出现openAI支付绑卡失败的，可以试试这样操作：路由器上openclash使用日本节点,开启udp模式，本机电脑装上warp+，warp+会自动连接到日本的warp+节点，再绑卡支付，账单选日本区域即可。


分流规则是互联网公共服务的域名和IP地址汇总，所有数据均收集自互联网公开信息，不代表我们支持或使用这些服务。

请通过【中华人民共和国 People's Republic of China】合法的互联网出入口信道访问规则中的地址，并确保在使用过程中符合相关法律法规
