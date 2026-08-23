# CRT Indicator v0.3 — Session Lifecycle + MNQ Controlled QA

## Build

Implemented the client's new daily lifecycle:

- Trading day: **18:00 through 16:59**
- Default timezone: **America/New_York**, configurable in the indicator
- 15m/30m C1 and C2 must belong to the same trading session
- A C2 confirming exactly at 17:00 is not allowed to start a new CRT
- No CRT remains active into the next trading day
- Historical/backtesting target-hit ranges remain available through the rest of their session
- Historical ranges stop at the 17:00 boundary so they do not visually extend into future sessions
- Live target-hit ranges disappear immediately in Auto mode
- Any remaining live range is removed at session end
- Always Keep / Always Hide remain available, but session expiry always prevents carryover

## Important historical/live behavior

For backtesting, historical drawings are kept as finite session-bounded objects. This is necessary so completed CRTs are still visible when reviewing old sessions.

For live trading, the active object is removed on a target hit in Auto mode and any surviving range is removed at the day boundary. After a future script reload, that old event can reconstruct as a historical, finite range for backtesting.

## Automated source regression

**20/20 checks passed.**

- PASS: **Pine v6** — Version declaration retained.
- PASS: **max_lines_count within Pine cap** — max_lines_count=500
- PASS: **max_boxes_count within Pine cap** — max_boxes_count=300
- PASS: **max_labels_count within Pine cap** — max_labels_count=300
- PASS: **18:00 session start** — Client start hour encoded.
- PASS: **17:00 exclusive boundary** — 16:59 is last in-session minute.
- PASS: **New York default** — Timezone remains configurable.
- PASS: **15m C1/C2 same-session gate** — Cross-session 15m pairs rejected.
- PASS: **30m C1/C2 same-session gate** — Cross-session 30m pairs rejected.
- PASS: **17:00 C2 confirmations rejected** — No new CRT starts after the trading day.
- PASS: **Session state stored per CRT** — Each CRT is bound to its source trading day.
- PASS: **Historical expiry state** — Historical ranges become finite at day end.
- PASS: **Live day-end removal** — Live ranges do not carry into next day.
- PASS: **Historical target-hit does not freeze at hit** — Retained historical ranges can continue through session end.
- PASS: **Confirmed 15m/30m offsets retained** — C1=[2], C2=[1].
- PASS: **Confirmed 4H SMA retained** — Non-repainting SMA architecture unchanged.
- PASS: **Rollback-safe event recreation retained** — Realtime activation design unchanged.
- PASS: **First post-confirmation target monitoring retained** — Activation bar remains target-eligible.
- PASS: **Deletion index-shift guard** — A removed array item is not accidentally reprocessed at the shifted index.
- PASS: **No invalid reverse step** — Pine-safe descending loop retained.

## John's MNQ 1-minute export

File: `CME_MINI_MNQ1!, 1.csv`

- Rows: **19,717**
- First timestamp: **2026-08-03 10:23:00-04:00**
- Last timestamp: **2026-08-21 16:59:00-04:00**
- Complete 18:00–16:59 sessions: **14**
- Minutes in each complete session: **1,380**
- Partial first session: **397 minutes**

### Session-scoped raw CRT pattern candidates

These counts intentionally exclude the 4H SMA filter because the export does not contain enough 4H history to warm up SMA200.

- 15m CRT pattern candidates: **436**
- 15m candidates hitting opposite-side target in the same session: **354**
- 15m candidates expiring without a same-session target hit: **82**
- 30m CRT pattern candidates: **225**
- 30m candidates hitting opposite-side target in the same session: **176**
- 30m candidates expiring without a same-session target hit: **49**

Every generated expected candidate:
- uses C1/C2 from the same session
- confirms before 17:00
- has a historical right edge at the session's 17:00 boundary

## 4H SMA validation limitation

This export contains only **89 4H windows**. A 200-period 4H SMA requires at least **200 completed 4H candles**, so this file cannot independently validate the full SMA200 filter.

The file is still excellent for:
- 15m/30m CRT pattern validation
- C1/C2 source-candle checks
- target-hit timing
- 18:00–16:59 session boundaries
- cross-session rejection
- day-end expiry behavior

A longer export can later complete the independent SMA200 comparison.

## Still requires TradingView

- Pine compilation of v0.3
- actual line/box rendering
- realtime target removal
- realtime 17:00 expiry
- comparison of visible TradingView events against these expected candidate rows

