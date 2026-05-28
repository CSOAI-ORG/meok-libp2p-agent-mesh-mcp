# MEOK libp2p Agent Mesh MCP

> **Peer-to-peer agent discovery + addressing.** The mesh substrate under A2A, ACP, AP2 and x402. Mint a libp2p PeerID, compose multiaddrs, sign Agent Records, derive GossipSub topics — all without a central registry.

> 🧱 **Part of the MEOK A2A Substrate (£999/mo)** — combine with `meok-aaif-agent-card-mcp` for identity, `meok-ap2-mandate-mcp` for payments, and `agent-handoff-certified-mcp` for signed call-chain proofs.

## Why libp2p for agents

Every other agent protocol you've heard of — Google A2A, AAIF ACP, Stripe ACP, Coinbase x402, Google AP2 — is wire-agnostic. They all need an **addressing + transport** layer underneath. libp2p is the same stack IPFS, Ethereum, Filecoin, Polkadot and Optimism use. It gives you:

| Capability | What it solves for agents |
|---|---|
| `PeerID` (Ed25519) | Stable identity across IPs / hostnames |
| `multiaddr` (`/ip4/.../tcp/.../p2p/...`) | Wire-agnostic addressing — TCP / QUIC / WebRTC / WebSockets |
| Signed Agent Records | Tamper-evident "this agent claims these protocols at these addresses" |
| GossipSub topics | Pub/sub channel per agent category, no broker |
| DHT discovery | Find peers by PeerID without a central registry |
| Bootstrap nodes | The known anchor set (IPFS public + MEOK's `bootstrap.meok.ai`) |

## Quick start

```bash
pip install meok-libp2p-agent-mesh-mcp
# or
uvx meok-libp2p-agent-mesh-mcp
```

```python
from server import (
    generate_peer_keypair, compose_multiaddr,
    sign_agent_record, verify_agent_record,
    gossipsub_topic, normalise_protocol_id,
)

# 1. Mint identity
kp = generate_peer_keypair()
peer_id = kp["peer_id"]                    # 12D3KooW...

# 2. Compose your address
addr = compose_multiaddr("203.0.113.5", 4001, peer_id, transport="tcp")
# /ip4/203.0.113.5/tcp/4001/p2p/12D3KooW...

# 3. Sign an agent record
record = {
    "agent_id": "did:meok:my-agent",
    "addrs": [addr["multiaddr"]],
    "protocols": [normalise_protocol_id("agent", "1.0.0")["protocol_id"]],
    "metadata": {"category": "governance"},
}
signed = sign_agent_record(record, kp["private_key_b64"])

# 4. Verify on the other side
result = verify_agent_record(signed)
assert result["valid"]
```

## Tools exposed

- `mint_peer_id(public_key_b64)` — derive PeerID from an existing public key
- `generate_peer_keypair()` — fresh Ed25519 keypair + PeerID
- `compose_multiaddr(host, port, peer_id, transport)` — build an addressable multiaddr
- `parse_multiaddr(multiaddr)` — walk components into a dict
- `sign_agent_record(record, private_key_b64)` — produce signed Agent Record
- `verify_agent_record(signed_record)` — verify signature + return PeerID
- `gossipsub_topic(category, namespace)` — deterministic topic string
- `list_bootstrap_nodes()` — canonical bootstrap multiaddrs
- `normalise_protocol_id(name, version, namespace)` — libp2p protocol identifier
- `generate_agent_record_template()` — starter Record + next-steps guide

## How it composes with the rest of the MEOK fleet

```
            ┌──────────────────────────┐
            │ Agent want to send AP2   │
            │ payment + Stripe ACP     │
            │ checkout + signed audit  │
            └────────────┬─────────────┘
                         │
            ┌────────────▼────────────┐
            │  Protocol layer         │ ← meok-ap2-mandate-mcp
            │  (AP2 + ACP + x402)     │   meok-stripe-acp-checkout-mcp
            └────────────┬────────────┘   meok-coinbase-x402-receipt-mcp
                         │
            ┌────────────▼────────────┐
            │  Identity + Cards       │ ← meok-aaif-agent-card-mcp
            │                         │   meok-mcp-cardgen-mcp
            └────────────┬────────────┘
                         │
            ┌────────────▼────────────┐
            │  MESH SUBSTRATE         │ ← meok-libp2p-agent-mesh-mcp
            │  PeerID + multiaddr +   │
            │  GossipSub + signing    │
            └─────────────────────────┘
```

## Verify any signed Agent Record

Every signed Record carries an Ed25519 signature. Verify with this MCP, or at <https://meok.ai/verify>.

## Pricing

- Self-host: free (MIT)
- Starter: £29/mo — 1K signing ops/month, signed Record SLA
- Pro: £79/mo — 10K ops, bootstrap.meok.ai anchor inclusion
- A2A Substrate: £999/mo — bundled with all 12 A2A MCPs

<!-- BUY-LADDER:START -->

## 💸 Try MEOK in 30 seconds — instant buy ladder

| Tier | Price | What you get | Stripe |
|---|---|---|---|
| Smoke test | **£1** | Signed sample MCP-Hardening report + Article 50 PDF | <https://buy.stripe.com/dRmcN75ScdQS7oh1Uc8k90U> |
| Quick Kit | **£9** | EU AI Act Article 50 implementation guide (C2PA + EU-Icon) | <https://buy.stripe.com/cNi00la8s1460ZT0Q88k90V> |
| Founder Call | **£29** | 30-min 1-on-1 with the founder | <https://buy.stripe.com/8x228ta8s6oqbExaqI8k90W> |

> Refundable. UK Stripe — VAT-clean. Builds on the 81-MCP MEOK fleet.
> Verify any signed report at <https://meok.ai/verify>.

<!-- BUY-LADDER:END -->

## Legal

Built by [MEOK AI Labs](https://meok.ai) — trading name of CSOAI LTD, UK Companies House 16939677.
Founder: Nicholas Templeman (`nicholas@meok.ai`).
License: MIT.
