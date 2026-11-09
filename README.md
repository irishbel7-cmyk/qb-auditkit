# qb-auditkit

On-chain audit toolkit for BSC/EVM treasuries and token distributions — built from real first-come bounty audit work (FlapJax Q88/Q92 treasury forensics, 2026).

## What it does

- **Treasury transfer extraction** — scan a block window and pull every transfer out of a treasury address (RPC-range extraction with automatic chunking: 50k blocks per chunk on public archive nodes).
- **First-BNB-funder tracing** — for each recipient, binary-search the exact block where they first held BNB (`eth_getBalance` binary search), then `trace_transaction` to identify the funder. Detects treasury-linked self-funding.
- **Activity proof** — nonce, balance, and code checks to classify wallets (independent operator vs. dormant vs. contract).

## Why

First-come token distributions are a common attack surface: fresh wallets get funded minutes before the window opens, then claim everything. This kit turns a manual forensic process (block scans + balance binary search + internal traces) into a repeatable CLI flow.

## Files

| File | Purpose |
|---|---|
| `extract_transfers.py` | Block-range transfer extraction with chunked RPC |
| `funder_trace.py` | Binary-search first-BNB block + trace funder |
| `wallet_profile.py` | Nonce/balance/code classification for a wallet |
| `rpc.py` | Rate-limit-aware JSON-RPC client with rotation (publicnode / Zan / 48.club / Tatum) |

## Requirements

- Python 3.10+
- An archive-capable RPC endpoint (free tiers work: publicnode, Zan, 48.club; Tatum for old blocks at 5 req/min)

```bash
python3 extract_transfers.py --address 0xTREASURY --from 132000000 --to 132192000
python3 funder_trace.py --recipient 0xWALLET --rpc https://bsc-mainnet.gateway.tatum.io
python3 wallet_profile.py --address 0xWALLET
```

## Honest status

Early-stage, single-maintainer project. Battle-tested logic (it produced a published audit: https://dpaste.org/zjJNs), but not yet packaged for pip. Roadmap: CLI packaging, multi-chain (Base), report generation.

## License

MIT
