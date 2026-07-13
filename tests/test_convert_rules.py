import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.convert_chatgpt_to_ai import (
    build_classical_entries,
    convert_ai_entries_to_shadowrocket,
    generate_files,
    merge_unique,
    parse_ai_source_entries,
    parse_classical_source_entries,
    parse_classical_rules,
    parse_rules,
    write_shadowrocket_rules,
)


def test_parse_rules_keeps_domain_provider_payload_order_and_deduplicates():
    lines = [
        "# comment",
        "",
        "DOMAIN-SUFFIX,openai.com",
        "DOMAIN-SUFFIX,openai.com",
        "DOMAIN,api.openai.com",
    ]

    assert parse_rules(lines) == ["+.openai.com", "+.api.openai.com"]


def test_parse_classical_rules_preserves_rule_type_and_deduplicates():
    lines = [
        "# comment",
        "",
        "DOMAIN-SUFFIX,google.com",
        "DOMAIN,android.chat.openai.com",
        "DOMAIN-KEYWORD,openai",
        "DOMAIN-SUFFIX,google.com",
    ]

    assert parse_classical_rules(lines) == [
        "DOMAIN-SUFFIX,google.com",
        "DOMAIN,android.chat.openai.com",
        "DOMAIN-KEYWORD,openai",
    ]


def test_parse_ai_source_entries_accepts_payload_and_classical_domain_rules():
    lines = [
        "payload:",
        "  - DOMAIN-SUFFIX,openai.com",
        "  - DOMAIN,ai.google.dev",
        "  - '+.claude.ai'",
        "  - plain.example.com",
        "  - DOMAIN-KEYWORD,openai",
        "  - IP-CIDR,24.199.123.28/32",
        "  - IP-ASN,20473",
    ]

    assert parse_ai_source_entries(lines) == [
        "+.openai.com",
        "ai.google.dev",
        "+.claude.ai",
        "plain.example.com",
    ]


def test_parse_classical_source_entries_accepts_payload_and_keeps_route_types():
    lines = [
        "payload:",
        "  - '+.bilibili.com'",
        "  - iqiyi.com",
        "  - DOMAIN-SUFFIX,youku.com",
        "  - DOMAIN-KEYWORD,douyin",
        "  - IP-CIDR,106.11.0.0/16,no-resolve",
        "  - PROCESS-NAME,ExampleApp",
    ]

    assert parse_classical_source_entries(lines) == [
        "DOMAIN-SUFFIX,bilibili.com",
        "DOMAIN,iqiyi.com",
        "DOMAIN-SUFFIX,youku.com",
        "DOMAIN-KEYWORD,douyin",
        "IP-CIDR,106.11.0.0/16,no-resolve",
    ]


def test_merge_unique_preserves_first_seen_order():
    assert merge_unique(
        ["+.openai.com", "+.claude.ai"],
        ["+.claude.ai", "+.gemini.google.com"],
    ) == ["+.openai.com", "+.claude.ai", "+.gemini.google.com"]


def test_convert_ai_entries_to_shadowrocket_uses_typed_rules():
    assert convert_ai_entries_to_shadowrocket(
        ["+.openai.com", "api.example.com"]
    ) == [
        "DOMAIN-SUFFIX,openai.com",
        "DOMAIN,api.example.com",
    ]


def test_write_shadowrocket_rules_uses_plain_policy_free_format(tmp_path):
    target = tmp_path / "rules.list"

    write_shadowrocket_rules(
        target,
        [
            "DOMAIN-SUFFIX,example.com",
            "IP-CIDR,203.0.113.0/24,no-resolve",
        ],
    )

    output = target.read_text(encoding="utf-8")
    assert output == (
        "DOMAIN-SUFFIX,example.com\n"
        "IP-CIDR,203.0.113.0/24,no-resolve\n"
    )
    assert "payload:" not in output
    assert "PROXY" not in output
    assert "DIRECT" not in output


def test_generate_files_writes_clash_and_shadowrocket_outputs(tmp_path):
    (tmp_path / "chatgpt.list").write_text(
        "DOMAIN-SUFFIX,openai.com\n", encoding="utf-8"
    )
    (tmp_path / "ai.sources.txt").write_text("", encoding="utf-8")
    (tmp_path / "proxy.list").write_text(
        "DOMAIN-SUFFIX,google.com\n", encoding="utf-8"
    )
    (tmp_path / "proxy.sources.txt").write_text("", encoding="utf-8")
    (tmp_path / "direct.list").write_text(
        "IP-CIDR,192.0.2.0/24,no-resolve\n", encoding="utf-8"
    )
    (tmp_path / "direct.sources.txt").write_text("", encoding="utf-8")

    generate_files(tmp_path)

    assert (tmp_path / "ai.txt").read_text(encoding="utf-8") == (
        "payload:\n  - '+.openai.com'\n"
    )
    assert (tmp_path / "ai-shadowrocket.list").read_text(encoding="utf-8") == (
        "DOMAIN-SUFFIX,openai.com\n"
    )
    assert (tmp_path / "proxy-shadowrocket.list").read_text(
        encoding="utf-8"
    ) == "DOMAIN-SUFFIX,google.com\n"
    assert (tmp_path / "direct-shadowrocket.list").read_text(
        encoding="utf-8"
    ) == "IP-CIDR,192.0.2.0/24,no-resolve\n"


def test_sync_workflow_stages_all_generated_files():
    workflow = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "sync-upstream.yml"
    ).read_text(encoding="utf-8")

    assert (
        "git add ai.txt proxy.txt direct.txt "
        "ai-shadowrocket.list proxy-shadowrocket.list "
        "direct-shadowrocket.list"
    ) in workflow


def test_direct_rules_cover_mainland_video_services():
    direct_rules = (Path(__file__).resolve().parents[1] / "direct.list").read_text(
        encoding="utf-8"
    )

    expected_rules = [
        "DOMAIN-SUFFIX,bilibili.com",
        "DOMAIN-SUFFIX,douyin.com",
        "DOMAIN-SUFFIX,iqiyi.com",
        "DOMAIN-SUFFIX,youku.com",
        "DOMAIN-SUFFIX,mgtv.com",
        "DOMAIN-SUFFIX,kuaishou.com",
        "DOMAIN-SUFFIX,ixigua.com",
        "DOMAIN-SUFFIX,yangshipin.cn",
    ]

    for expected_rule in expected_rules:
        assert expected_rule in direct_rules


def test_direct_rules_cover_mainland_banking_services():
    direct_rules = (Path(__file__).resolve().parents[1] / "direct.list").read_text(
        encoding="utf-8"
    )

    expected_rules = [
        "DOMAIN-SUFFIX,icbc.com.cn",
        "DOMAIN-SUFFIX,ccb.com",
        "DOMAIN-SUFFIX,abchina.com",
        "DOMAIN-SUFFIX,boc.cn",
        "DOMAIN-SUFFIX,cmbchina.com",
        "DOMAIN-SUFFIX,unionpay.com",
        "DOMAIN-SUFFIX,alipay.com",
    ]

    for expected_rule in expected_rules:
        assert expected_rule in direct_rules


def test_direct_rules_cover_mainland_ecommerce_services():
    direct_rules = (Path(__file__).resolve().parents[1] / "direct.list").read_text(
        encoding="utf-8"
    )

    expected_rules = [
        "DOMAIN-SUFFIX,taobao.com",
        "DOMAIN-SUFFIX,tmall.com",
        "DOMAIN-SUFFIX,jd.com",
        "DOMAIN-SUFFIX,pinduoduo.com",
        "DOMAIN-SUFFIX,suning.com",
        "DOMAIN-SUFFIX,vip.com",
        "DOMAIN-SUFFIX,xiaohongshu.com",
        "DOMAIN-SUFFIX,dewu.com",
    ]

    for expected_rule in expected_rules:
        assert expected_rule in direct_rules


def test_proxy_rules_cover_common_overseas_service_vendors():
    proxy_rules = (Path(__file__).resolve().parents[1] / "proxy.list").read_text(
        encoding="utf-8"
    )

    expected_rules = [
        "DOMAIN-SUFFIX,google.com",
        "DOMAIN-SUFFIX,youtube.com",
        "DOMAIN-SUFFIX,x.com",
        "DOMAIN-SUFFIX,twitter.com",
        "DOMAIN-SUFFIX,github.com",
        "DOMAIN-SUFFIX,telegram.org",
        "DOMAIN-SUFFIX,facebook.com",
        "DOMAIN-SUFFIX,instagram.com",
        "DOMAIN-SUFFIX,netflix.com",
        "DOMAIN-SUFFIX,spotify.com",
        "DOMAIN-SUFFIX,cloudflare.com",
        "DOMAIN-SUFFIX,notion.so",
        "DOMAIN-SUFFIX,vercel.com",
    ]

    for expected_rule in expected_rules:
        assert expected_rule in proxy_rules


def test_build_classical_entries_supports_proxy_file_names(tmp_path, monkeypatch):
    (tmp_path / "proxy.list").write_text(
        "DOMAIN-SUFFIX,google.com\nDOMAIN-SUFFIX,x.com\n", encoding="utf-8"
    )
    (tmp_path / "proxy.sources.txt").write_text(
        "https://example.test/proxy.yaml\n", encoding="utf-8"
    )

    import scripts.convert_chatgpt_to_ai as converter

    monkeypatch.setattr(
        converter,
        "fetch_url",
        lambda url: "payload:\n  - DOMAIN-SUFFIX,youtube.com\n  - '+.github.com'\n",
    )

    assert build_classical_entries(tmp_path, "proxy.list", "proxy.sources.txt") == [
        "DOMAIN-SUFFIX,google.com",
        "DOMAIN-SUFFIX,x.com",
        "DOMAIN-SUFFIX,youtube.com",
        "DOMAIN-SUFFIX,github.com",
    ]
