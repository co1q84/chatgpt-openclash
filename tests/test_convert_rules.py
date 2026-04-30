import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.convert_chatgpt_to_ai import (
    merge_unique,
    parse_ai_source_entries,
    parse_classical_source_entries,
    parse_classical_rules,
    parse_rules,
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
        "  - PROCESS-NAME,Spotify",
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
