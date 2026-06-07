<!-- mcp-name: io.github.CSOAI-ORG/meok-libp2p-agent-mesh-mcp -->
[![MCP Scorecard: 86/100](https://img.shields.io/badge/proofof.ai-86%2F100-5b21b6)](https://proofof.ai/scorecard/meok-libp2p-agent-mesh-mcp.html)

# Meok Libp2P Agent Mesh MCP
mcp-name: io.github.CSOAI-ORG/meok-libp2p-agent-mesh-mcp

# MEOK libp2p Agent Mesh MCP

[![MEOK AI Labs](https://img.shields.io/badge/MEOK-AI%20Labs-667eea)](https://meok.ai)
[![EU AI Act](https://img.shields.io/badge/EU%20AI%20Act-Compliant-22c55e)](https://councilof.ai)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-Install-3775a9)](https://pypi.org/project/meok_libp2p_agent_mesh_mcp/)

> MEOK libp2p Agent Mesh MCP — peer-to-peer agent discovery + addressing

MEOK libp2p Agent Mesh MCP — peer-to-peer agent discovery + addressing. PeerID + multiaddr + signed Agent Records + GossipSub topic derivation. The mesh substrate under A2A/ACP/AP2/x402. By MEOK AI Labs.

---

## 🚀 Quick Start

```bash
# Install via pip
pip install meok_libp2p_agent_mesh_mcp

# Or install via Smithery
npx -y @smithery/cli@latest install meok-libp2p-agent-mesh-mcp --client claude
```

## ✨ Features

- MCP protocol compliant
- Easy installation
- Well-documented API
- Production-ready
- Active maintenance

## 📖 Documentation

- [Full Documentation](https://docs.meok.ai/meok-libp2p-agent-mesh-mcp)
- [API Reference](https://api.meok.ai)
- [EU AI Act Compliance Guide](https://councilof.ai/compliance)

## 🛡️ Compliance

This MCP server is built with **EU AI Act compliance** built-in:

- ✅ Article 9 — Risk Management System
- ✅ Article 13 — Transparency & Instructions for Use
- ✅ Article 15 — Bias Detection & Testing
- ✅ Article 26 — FRIA Support (where applicable)
- ✅ Article 50 — AI Content Watermarking (where applicable)

Need help getting compliant? **[Book a free 15-min diagnostic →](https://cal.com/csoai/august-audit)**

## 🏢 Enterprise

Need custom development, SLA guarantees, or white-label deployment?

- **Pro:** $99/mo — Full MCP suite + EU AI Act tracking
- **Enterprise:** $499/mo — Custom dev + SLA + Dedicated support

[View Pricing →](https://councilof.ai/pricing) | [Contact Sales →](mailto:sales@csoai.org)

## 🤝 Part of the MEOK Ecosystem

This server is part of the **[MEOK AI Labs](https://meok.ai)** ecosystem — 300+ MCP servers for sovereign AI governance.

| Domain | Purpose |
|--------|---------|
| [councilof.ai](https://councilof.ai) | EU AI Act compliance marketplace |
| [safetyof.ai](https://safetyof.ai) | AI safety & monitoring |
| [meok.ai](https://meok.ai) | Sovereign AI platform |
| [cobolbridge.ai](https://cobolbridge.ai) | Legacy modernization |

## 📜 License

MIT © [CSOAI-ORG](https://github.com/CSOAI-ORG)

---

<p align="center">
  <sub>Built with 💜 by <a href="https://meok.ai">MEOK AI Labs</a> · UK Companies House 16939677</sub>
</p>
## Legal

Built by [MEOK AI Labs](https://meok.ai) — trading name of CSOAI LTD, UK Companies House 16939677.
Founder: Nicholas Templeman (`nicholas@meok.ai`).
License: MIT.

## Configuration

Add to your `claude_desktop_config.json` (Claude Desktop) or your MCP client config:

```json
{
  "mcpServers": {
    "meok-libp2p-agent-mesh-mcp": {
      "command": "uvx",
      "args": ["meok-libp2p-agent-mesh-mcp"]
    }
  }
}
```

Or: `pip install meok-libp2p-agent-mesh-mcp` then run the `meok-libp2p-agent-mesh-mcp` command (stdio transport).

## Examples

Once configured, ask your assistant, for example:
- "Use `mint_peer_id` to …"
- "Use `generate_peer_keypair` to …"
- "Use `compose_multiaddr` to …"
