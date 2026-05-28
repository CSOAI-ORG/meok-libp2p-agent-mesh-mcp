"""Unit tests for meok-libp2p-agent-mesh-mcp."""
from __future__ import annotations

import base64
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from server import (  # noqa: E402
    derive_peer_id,
    compose_multiaddr_str,
    parse_multiaddr_str,
    gossipsub_topic_str,
    normalise_protocol_id_str,
    BOOTSTRAP_NODES,
    generate_peer_keypair,
    sign_agent_record,
    verify_agent_record,
    compose_multiaddr,
    parse_multiaddr,
    list_bootstrap_nodes,
    gossipsub_topic,
    normalise_protocol_id,
    generate_agent_record_template,
)


# ---------- PeerID ----------

def test_peer_id_starts_with_known_prefix():
    """Ed25519 PeerIDs (identity multihash, len<=42) start with '12D3KooW'."""
    kp = generate_peer_keypair()
    assert kp["peer_id"].startswith("12D3KooW"), kp["peer_id"]
    assert len(kp["peer_id"]) > 40
    assert kp["key_type"] == "Ed25519"


def test_peer_id_deterministic_from_public_key():
    pub = bytes(range(32))
    a = derive_peer_id(pub)
    b = derive_peer_id(pub)
    assert a == b


def test_peer_id_rejects_wrong_length():
    import pytest
    with pytest.raises(ValueError):
        derive_peer_id(b"\x00" * 16)


# ---------- Multiaddr ----------

def test_compose_multiaddr_ipv4_tcp():
    a = compose_multiaddr_str("203.0.113.5", 4001, "12D3KooWtest", "tcp")
    assert a == "/ip4/203.0.113.5/tcp/4001/p2p/12D3KooWtest"


def test_compose_multiaddr_dns_quic():
    a = compose_multiaddr_str("agent.example.com", 4002, None, "quic")
    assert a == "/dns4/agent.example.com/quic/4002"


def test_compose_multiaddr_rejects_bad_transport():
    import pytest
    with pytest.raises(ValueError):
        compose_multiaddr_str("203.0.113.5", 4001, "x", "carrier-pigeon")


def test_compose_multiaddr_rejects_bad_port():
    import pytest
    with pytest.raises(ValueError):
        compose_multiaddr_str("203.0.113.5", 99999, None, "tcp")


def test_parse_multiaddr_roundtrip():
    a = "/ip4/192.0.2.1/tcp/443/p2p/12D3KooWabc"
    parsed = parse_multiaddr_str(a)
    assert parsed["ip4"] == "192.0.2.1"
    assert parsed["tcp"] == 443
    assert parsed["p2p"] == "12D3KooWabc"


def test_parse_multiaddr_odd_components_rejected():
    import pytest
    with pytest.raises(ValueError):
        parse_multiaddr_str("/ip4/192.0.2.1/tcp")  # missing value


# ---------- Sign + verify ----------

def test_sign_verify_roundtrip():
    kp = generate_peer_keypair()
    rec = {"agent_id": "did:meok:test", "addrs": ["/dns4/x.example.com"], "v": 1}
    signed = sign_agent_record(rec, kp["private_key_b64"])
    assert signed["signature"]
    assert signed["public_key"] == kp["public_key_b64"]
    res = verify_agent_record(signed)
    assert res["valid"] is True
    assert res["peer_id"] == kp["peer_id"]


def test_verify_detects_tampered_record():
    kp = generate_peer_keypair()
    signed = sign_agent_record({"a": 1}, kp["private_key_b64"])
    signed["record"]["a"] = 999  # mutate
    res = verify_agent_record(signed)
    assert res["valid"] is False
    assert "signature" in res["reason"].lower()


def test_verify_missing_field():
    res = verify_agent_record({"record": {"a": 1}})  # no signature
    assert res["valid"] is False
    assert "missing" in res["reason"].lower()


# ---------- GossipSub topic ----------

def test_gossipsub_topic_deterministic():
    t1 = gossipsub_topic_str("Governance")
    t2 = gossipsub_topic_str("governance")
    # Case-normalized — both should produce the same lowered form
    assert t1 == t2 == "/meok/agents/governance/v1"


def test_gossipsub_topic_sanitises_special_chars():
    t = gossipsub_topic_str("EU AI Act")
    assert t == "/meok/agents/eu-ai-act/v1"


# ---------- Protocol id ----------

def test_protocol_id_well_formed():
    pid = normalise_protocol_id_str("agent", "1.0.0")
    assert pid == "/meok/agent/1.0.0"


def test_protocol_id_rejects_bad_semver():
    import pytest
    with pytest.raises(ValueError):
        normalise_protocol_id_str("agent", "1.0")


def test_protocol_id_rejects_bad_name():
    import pytest
    with pytest.raises(ValueError):
        normalise_protocol_id_str("Agent_Name", "1.0.0")  # uppercase / underscore


# ---------- Bootstrap + template ----------

def test_bootstrap_nodes_non_empty():
    assert len(BOOTSTRAP_NODES) >= 4
    # All start with `/`
    for addr in BOOTSTRAP_NODES:
        assert addr.startswith("/")


def test_list_bootstrap_nodes_tool():
    out = list_bootstrap_nodes()
    assert out["count"] == len(BOOTSTRAP_NODES)


def test_generate_template_has_required_keys():
    t = generate_agent_record_template()
    assert "record" in t
    assert "next_steps" in t
    assert t["record"]["agent_id"].startswith("did:")
    assert isinstance(t["record"]["protocols"], list)


# ---------- Tool wrappers ----------

def test_compose_multiaddr_tool_returns_string():
    out = compose_multiaddr("198.51.100.1", 4001, "12D3KooWxyz", "tcp")
    assert "/ip4/198.51.100.1/tcp/4001/p2p/12D3KooWxyz" == out["multiaddr"]


def test_parse_multiaddr_tool_dict_shape():
    out = parse_multiaddr("/ip4/1.2.3.4/tcp/5/p2p/Q1")
    assert out["ip4"] == "1.2.3.4"
    assert out["tcp"] == 5
    assert out["p2p"] == "Q1"
