#!/usr/bin/env python3
"""
Buy Pro: https://www.csoai.org/checkout

MEOK libp2p Agent Mesh MCP — peer-to-peer agent discovery + addressing
======================================================================

By MEOK AI Labs · https://meok.ai · MIT
<!-- mcp-name: io.github.CSOAI-ORG/meok-libp2p-agent-mesh-mcp -->

WHAT THIS DOES
--------------
libp2p is the peer-to-peer networking stack underneath IPFS, Ethereum,
Filecoin, Polkadot, Optimism, and (increasingly) decentralised agent
networks. It uses Ed25519/Secp256k1/RSA keypairs to derive a stable
`PeerID`, compose `multiaddr`s, sign agent records, and reach peers via
the Distributed Hash Table (DHT) or GossipSub.

This MCP exposes libp2p primitives so agents can:

- Mint a stable peer identity from an Ed25519 key
- Compose / parse multiaddrs (`/ip4/.../tcp/.../p2p/...`)
- Sign + verify agent records (analogous to libp2p IPNS records)
- Derive deterministic GossipSub topics per agent category
- Normalise libp2p protocol IDs (`/meok/agent/1.0.0` etc.)
- Return canonical bootstrap nodes
- Generate a starter Agent Record that other meshes can consume

This is the **mesh substrate** under A2A, ACP, AP2 and x402. Once an
agent has a PeerID + multiaddr, every other protocol becomes wire-
agnostic — agents can talk over WebRTC, QUIC, TCP, WebTransport, or the
relay-circuit fallback.

TOOLS
-----
- mint_peer_id(public_key_b64): derive a PeerID from an Ed25519 public key
- generate_peer_keypair(): mint a fresh Ed25519 PeerID (returns priv+pub+id)
- compose_multiaddr(host, port, peer_id, transport="tcp"): build a multiaddr
- parse_multiaddr(multiaddr): walk the components into a dict
- sign_agent_record(record, private_key_b64): produce a libp2p-style signed record
- verify_agent_record(signed_record, public_key_b64): verify a signed record
- gossipsub_topic(category, namespace="meok"): deterministic topic string
- list_bootstrap_nodes(): canonical bootstrap multiaddrs
- normalise_protocol_id(name, version): produce `/<namespace>/<name>/<vN.N.N>`
- generate_agent_record_template(): minimal Agent Record + signature stub

PRICING
-------
Free MIT self-host · £29/mo Starter · £79/mo Pro · A2A Substrate £999/mo.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# PeerID derivation
# ---------------------------------------------------------------------------

# libp2p PeerID for keys ≤ 42 bytes uses identity multihash + a 0x00 codec
# prefix and base58btc encoding. We follow the simplified path that all
# modern libp2p impls use for Ed25519 (Identity multihash; CIDv0-style b58
# encoding starting with "12D3KooW…").

ED25519_PUBKEY_LEN = 32
# libp2p protobuf "PublicKey" framing for Ed25519: type=Ed25519 (1) + data
# In protobuf binary, that is: 0x08, 0x01 (field 1 varint = 1) +
#                              0x12, 0x20 (field 2 len-delim, len=32) + 32 bytes
ED25519_PROTOBUF_PREFIX = b"\x08\x01\x12\x20"

BASE58_ALPHABET = (
    "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
)


def _b58encode(data: bytes) -> str:
    """Standard base58btc (Bitcoin alphabet) encode."""
    n = int.from_bytes(data, "big")
    out = ""
    while n > 0:
        n, r = divmod(n, 58)
        out = BASE58_ALPHABET[r] + out
    # Leading zero bytes → leading "1"s
    pad = 0
    for b in data:
        if b == 0:
            pad += 1
        else:
            break
    return "1" * pad + out


def _multihash_identity(payload: bytes) -> bytes:
    """Build an 'identity' multihash (code 0x00) wrapping payload."""
    return bytes([0x00, len(payload)]) + payload


def derive_peer_id(public_key_bytes: bytes) -> str:
    """Derive a PeerID string from an Ed25519 32-byte public key."""
    if len(public_key_bytes) != ED25519_PUBKEY_LEN:
        raise ValueError(
            f"Ed25519 public key must be 32 bytes, got {len(public_key_bytes)}"
        )
    framed = ED25519_PROTOBUF_PREFIX + public_key_bytes
    if len(framed) <= 42:
        mhash = _multihash_identity(framed)
    else:
        # SHA-256 path for larger keys (RSA-2048 etc.). Code 0x12, len 32.
        digest = hashlib.sha256(framed).digest()
        mhash = bytes([0x12, 0x20]) + digest
    return _b58encode(mhash)


# ---------------------------------------------------------------------------
# Multiaddr handling
# ---------------------------------------------------------------------------

VALID_TRANSPORTS = {"tcp", "udp", "quic", "quic-v1", "ws", "wss", "webrtc"}


def compose_multiaddr_str(host: str, port: int, peer_id: str | None = None,
                          transport: str = "tcp") -> str:
    if transport not in VALID_TRANSPORTS:
        raise ValueError(
            f"Unsupported transport {transport!r}; valid: {sorted(VALID_TRANSPORTS)}"
        )
    if not (1 <= port <= 65535):
        raise ValueError(f"Port out of range: {port}")
    # Detect IPv4 vs IPv6 vs DNS
    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host):
        host_seg = f"/ip4/{host}"
    elif ":" in host:
        host_seg = f"/ip6/{host}"
    else:
        host_seg = f"/dns4/{host}"
    addr = f"{host_seg}/{transport}/{port}"
    if peer_id:
        addr += f"/p2p/{peer_id}"
    return addr


def parse_multiaddr_str(multiaddr: str) -> dict[str, Any]:
    if not multiaddr.startswith("/"):
        raise ValueError("Multiaddr must start with '/'")
    parts = multiaddr.split("/")[1:]
    if len(parts) % 2 != 0:
        raise ValueError("Multiaddr components must come in protocol/value pairs")
    out: dict[str, Any] = {}
    for i in range(0, len(parts), 2):
        proto, value = parts[i], parts[i + 1]
        if proto in ("tcp", "udp"):
            out[proto] = int(value)
        else:
            out[proto] = value
    return out


# ---------------------------------------------------------------------------
# Agent record signing
# ---------------------------------------------------------------------------

@dataclass
class SignedAgentRecord:
    record: dict[str, Any]
    signature: str
    public_key: str
    signed_at: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "record": self.record,
            "signature": self.signature,
            "public_key": self.public_key,
            "signed_at": self.signed_at,
            "format": "meok-libp2p-agent-record/1.0",
        }


def _canonical_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


# ---------------------------------------------------------------------------
# Topic + protocol ID utilities
# ---------------------------------------------------------------------------

VALID_PROTO_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")


def normalise_protocol_id_str(name: str, version: str, namespace: str = "meok") -> str:
    if not VALID_PROTO_NAME.match(namespace):
        raise ValueError(f"Invalid namespace: {namespace!r}")
    if not VALID_PROTO_NAME.match(name):
        raise ValueError(f"Invalid protocol name: {name!r}")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"Version must be semver MAJOR.MINOR.PATCH, got {version!r}")
    return f"/{namespace}/{name}/{version}"


def gossipsub_topic_str(category: str, namespace: str = "meok") -> str:
    if not category:
        raise ValueError("category required")
    safe = re.sub(r"[^a-z0-9-]", "-", category.lower().strip())
    return f"/{namespace}/agents/{safe}/v1"


# Canonical libp2p bootstrap nodes — well-known + agent-mesh ready
BOOTSTRAP_NODES = [
    # IPFS public bootstrap nodes — work for libp2p generally
    "/dnsaddr/bootstrap.libp2p.io/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN",
    "/dnsaddr/bootstrap.libp2p.io/p2p/QmQCU2EcMqAqQPR2i9bChDtGNJchTbq5TbXJJ16u19uLTa",
    "/dnsaddr/bootstrap.libp2p.io/p2p/QmbLHAnMoJPWSCR5Zhtx6BHJX9KiKNN6tpvbUcqanj75Nb",
    "/dnsaddr/bootstrap.libp2p.io/p2p/QmcZf59bWwK5XFi76CZX8cbJ4BhTzzA3gU1ZjYZcYW3dwt",
    # Anchor for MEOK's own future bootstrap (DNS-only stub for now)
    "/dnsaddr/bootstrap.meok.ai",
]


# ---------------------------------------------------------------------------
# MCP wiring
# ---------------------------------------------------------------------------

mcp = FastMCP("meok-libp2p-agent-mesh")


@mcp.tool()
def mint_peer_id(public_key_b64: str) -> dict:
    """Derive a libp2p PeerID string from a base64-encoded Ed25519 public key."""
    key = base64.b64decode(public_key_b64)
    return {"peer_id": derive_peer_id(key), "key_type": "Ed25519", "key_bytes": len(key)}


@mcp.tool()
def generate_peer_keypair() -> dict:
    """Mint a fresh Ed25519 keypair + derived PeerID.

    Uses cryptography.hazmat for Ed25519. Returns base64 strings — handle
    the private_key like a secret (never log to public manifests).
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )
    from cryptography.hazmat.primitives import serialization

    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    pub_bytes = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    priv_bytes = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return {
        "private_key_b64": base64.b64encode(priv_bytes).decode(),
        "public_key_b64": base64.b64encode(pub_bytes).decode(),
        "peer_id": derive_peer_id(pub_bytes),
        "key_type": "Ed25519",
        "warning": "Keep private_key_b64 secret. Never publish in server.json.",
    }


@mcp.tool()
def compose_multiaddr(host: str, port: int, peer_id: str | None = None,
                      transport: str = "tcp") -> dict:
    """Build a libp2p multiaddr string from components."""
    return {"multiaddr": compose_multiaddr_str(host, port, peer_id, transport)}


@mcp.tool()
def parse_multiaddr(multiaddr: str) -> dict:
    """Parse a multiaddr string into a {protocol: value} dict."""
    return parse_multiaddr_str(multiaddr)


@mcp.tool()
def sign_agent_record(record: dict, private_key_b64: str) -> dict:
    """Produce a signed libp2p-style Agent Record.

    Signs `record` with the given Ed25519 private key. Returns a signed
    envelope including the verifying public key + derived PeerID.
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )
    from cryptography.hazmat.primitives import serialization

    priv_bytes = base64.b64decode(private_key_b64)
    priv = Ed25519PrivateKey.from_private_bytes(priv_bytes)
    pub = priv.public_key()
    pub_bytes = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    payload = _canonical_bytes(record)
    signature = priv.sign(payload)

    return SignedAgentRecord(
        record=record,
        signature=base64.b64encode(signature).decode(),
        public_key=base64.b64encode(pub_bytes).decode(),
        signed_at=int(time.time()),
    ).as_dict() | {"peer_id": derive_peer_id(pub_bytes)}


@mcp.tool()
def verify_agent_record(signed_record: dict) -> dict:
    """Verify a signed Agent Record.

    Returns ``valid: True`` on success, else ``valid: False`` + reason.
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PublicKey,
    )
    from cryptography.exceptions import InvalidSignature

    try:
        record = signed_record["record"]
        signature = base64.b64decode(signed_record["signature"])
        public_key = base64.b64decode(signed_record["public_key"])
    except KeyError as e:
        return {"valid": False, "reason": f"missing field {e}"}
    except Exception as e:  # pragma: no cover
        return {"valid": False, "reason": f"decode error: {e}"}

    pub = Ed25519PublicKey.from_public_bytes(public_key)
    payload = _canonical_bytes(record)
    try:
        pub.verify(signature, payload)
        return {
            "valid": True,
            "peer_id": derive_peer_id(public_key),
            "verified_at": int(time.time()),
        }
    except InvalidSignature:
        return {"valid": False, "reason": "signature does not match record"}


@mcp.tool()
def gossipsub_topic(category: str, namespace: str = "meok") -> dict:
    """Derive a deterministic GossipSub topic for an agent category."""
    return {"topic": gossipsub_topic_str(category, namespace)}


@mcp.tool()
def list_bootstrap_nodes() -> dict:
    """Return canonical libp2p bootstrap multiaddrs + the MEOK anchor."""
    return {"bootstrap_nodes": BOOTSTRAP_NODES, "count": len(BOOTSTRAP_NODES)}


@mcp.tool()
def normalise_protocol_id(name: str, version: str, namespace: str = "meok") -> dict:
    """Compose a libp2p protocol identifier `/<namespace>/<name>/<version>`."""
    return {"protocol_id": normalise_protocol_id_str(name, version, namespace)}


@mcp.tool()
def generate_agent_record_template() -> dict:
    """Return a minimal Agent Record an agent can fill + sign for mesh discovery."""
    return {
        "record": {
            "agent_id": "did:meok:your-agent-handle",
            "addrs": [
                "/dns4/your-host.example.com/tcp/4001/p2p/YOUR_PEER_ID",
                "/dnsaddr/your-host.example.com",
            ],
            "protocols": [
                "/meok/agent/1.0.0",
                "/meok/policy-enforcement/1.0.0",
            ],
            "metadata": {
                "name": "Your Agent",
                "category": "governance",
                "owner": "your-org",
                "homepage": "https://example.com/your-agent",
                "license": "MIT",
            },
            "ttl_seconds": 3600,
        },
        "next_steps": [
            "1. Generate keypair: generate_peer_keypair()",
            "2. Sign the record: sign_agent_record(record, private_key_b64)",
            "3. Publish the signed record to bootstrap nodes",
            "4. Subscribe to gossipsub_topic(category) to hear peers",
        ],
    }


def main() -> None:  # pragma: no cover
    """Entry point for `meok-libp2p-agent-mesh-mcp` script."""
    mcp.run()


if __name__ == "__main__":  # pragma: no cover
    main()
