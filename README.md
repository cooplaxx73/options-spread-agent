# Options Spread Agent

> **Status:** in development — phase 1 of 7. Nothing is implemented yet; this
> README describes what is being built. See the roadmap below.

An autonomous agent that finds, sizes, places and closes defined-risk options
spreads on the Alpaca **paper** trading API. It logs every decision it makes,
including every trade it refused to take and the specific rule that stopped it.

Paper trading only. No real money is involved at any point.

## The idea

Option prices contain a forecast of how much a stock will move, and that forecast
is systematically too high. Not because the market is wrong, but because option
buyers are paying for insurance, and insurance costs more than its expected payout.
This is the **variance risk premium**, and it persists because it is compensation
for real risk rather than a mistake anyone can arbitrage away.

The agent looks for cases where implied volatility is rich compared to the
underlying's actual recent movement, and sells a defined-risk spread against it.

## The design principle

**The component that proposes a trade does not get to approve it.**

A local Qwen model reads pre-computed market factors and emits a schema-validated
JSON proposal. A separate, deterministic Python layer — the referee — then
recalculates everything itself and checks it against fixed rules. It never reads
the model's reasoning and never trusts a number the model returned. If the two
disagree, the referee wins.

This is enforced structurally: `src/referee/` imports nothing from `src/agent/`.
The proposer cannot influence the approval step even in principle.

Second principle: **position size is never derived from model confidence.** A
language model's self-reported confidence reflects how confident the text sounds,
not any real likelihood. All sizing comes from factors computed in Python.

## What the agent does each cycle

Every 20 minutes during market hours:

```
0. RECONCILE   ask Alpaca what positions actually exist
1. MANAGE      close anything that hit its stop or its time limit
2. CAPACITY    stop here if already at the position limit
3. FETCH       option chains, price history, news headlines
4. SCORE       IV/RV ratio, bid-ask width, trend -> build candidate spreads
5. GATE        drop anything failing a hard rule
6. PROPOSE     the only AI step: pick one, write the thesis, screen the news
7. REFEREE     independently re-validate -> ACCEPT or REJECT with a reason
8. EXECUTE     submit the spread, and rest the profit-target close at the broker
9. LOG         one terminal line and one CSV row per decision, accepted or not
```

Steps 0–5 and 7–9 are ordinary Python. Step 6 is the only place a model is involved.

## Strategy rules

**Universe:** SPY, QQQ, AAPL — liquid chains only.

**Entry, all must hold:**

| Condition | Threshold |
|---|---|
| Implied vol ÷ 20-day realized vol | > 1.20 |
| Days to expiration | 30–45 |
| Bid/ask width, both legs | below liquidity gate |
| Earnings before expiry | none |
| Event risk in recent headlines | none flagged |
| Open positions | fewer than 3 |

**Structure:** short vertical credit spread. Short leg near 0.30 delta, long leg
5 points further out to cap the loss. Put spread when price is above the 50-day
average, call spread when below.

**Sizing:** the conviction score sets a risk budget of 1%, 2% or 3% of account
equity. Contract count is then `risk budget ÷ ((width − credit) × 100)`, rounded
down. A trade that sizes to zero contracts is rejected.

**Exit, whichever comes first:** 50% of maximum profit (this order rests at the
broker from the moment of entry), a loss of 2× the credit collected, or 21 days
to expiration regardless of P&L.

## Stack

| Layer | Choice |
|---|---|
| Broker | Alpaca paper (`paper-api.alpaca.markets`), options Level 3 |
| SDK | `alpaca-py` |
| Model | Qwen via Ollama, running locally |
| Maths | pandas |
| Scheduling | Windows Task Scheduler, market hours only |
| Output | Terminal log + CSV |

Alpaca's MCP server is used as a **development tool** for inspecting the account
while building. It is deliberately not part of the agent's runtime path.

## Setup

Not yet runnable. Setup instructions land with phase 1.

## Roadmap

- [ ] **1** — Alpaca connection, option chain fetching, one hardcoded spread
- [ ] **2** — Volatility, liquidity and trend calculations, with tests
- [ ] **3** — Qwen proposer with schema-constrained output, news event screen
- [ ] **4** — Referee rules, sizing, rejection logging, with tests
- [ ] **5** — Order execution, resting exits, startup reconciliation
- [ ] **6** — Position lifecycle, terminal formatting, CSV decision log
- [ ] **7** — Architecture docs, decision records, honest results write-up

## On results

A handful of trades over a few weeks proves the system runs correctly and respects
its own limits. It proves nothing about profitability — the sample is noise. Any
results published here will say so plainly.

## Attribution

Built with Claude Code as a pair programmer. The architecture, strategy design and
risk model are mine, and commits written with AI assistance carry a co-author
trailer.

## License

MIT
