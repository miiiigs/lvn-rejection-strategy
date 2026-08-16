# LVN Rejection Strategy

This repository contains two TradingView Pine Script v6 strategy variants:

- [lvn_rejection_strategy.pine](/C:/dev/lvn-rejection-strategy/lvn_rejection_strategy.pine): premium-capable version with `use_bar_magnifier = true`
- [lvn_rejection_strategy_non_premium.pine](/C:/dev/lvn-rejection-strategy/lvn_rejection_strategy_non_premium.pine): non-premium-safe version with `use_bar_magnifier = false`

Both scripts are intended to keep the same core profile, LVN, entry, risk, and diagnostic logic. The only planned account-dependent difference is Bar Magnifier usage.

## 1. Strategy Overview

The strategy builds a custom fixed-range-style volume profile during:

- `18:00 -> 16:00`
- timezone: `America/New_York`
- default row count: `24`

Workflow:

1. Session N builds a completed profile.
2. At the end of Session N, the script freezes the profile high, low, row volumes, POC, and detected LVN zones.
3. Session N+1 trades only those frozen LVN zones.

The script is a `strategy()` study and is meant for Strategy Tester research, not passive chart annotation only.

## 2. Client Rules

Confirmed client-aligned behavior:

- Canonical chart timeframe: `1 minute`
- Canonical symbol for baseline validation: `CME_MINI:MNQ1!`
- No trading of developing current-session LVNs
- No lookahead
- LVNs are zones, not single lines
- Entries are touch-based only
- Longs enter from above at the LVN upper boundary
- Shorts enter from below at the LVN lower boundary

## 3. Recommended M1 Setup

Use this as the Milestone 1 baseline:

- Symbol: `CME_MINI:MNQ1!`
- Timeframe: `1 minute`
- Session: `18:00 -> 16:00 America/New_York`
- Rows: `24`
- LVN Method: `Client Threshold Valley`
- Threshold: `40%`
- Surrounding Rows Per Side: `2`
- Contrast Filter: `Off`
- LVN #1: `On`
- LVN #2-#10: `Off`
- Trade Longs: `On`
- Trade Shorts: `On`
- Freshness: `First Touch Only`
- Minimum Approach Distance: `0`
- Entry Session Filter: `Off`
- POC Filters: `Off`
- Risk Mode: `Fixed Points`
- SL: `5`
- TP: `10`
- Order Size: `1`
- Block New Entries Before Session End: `On`
- Entry Cutoff Minutes: `5`
- Show Volume Profile Histogram: `On`
- Show Debug Diagnostics: `On` during validation

These are baseline validation settings, not optimized settings.

## 4. Profile Settings

The profile engine:

- uses the completed `18:00 -> 16:00` session only
- stores row lows, row highs, and row volumes
- freezes the exact row-volume data used for:
  - POC selection
  - LVN detection
  - LVN ranking
  - histogram rendering

The current default allocation method is a transparent chart-bar overlap approximation:

- bar volume is distributed across touched rows in proportion to row overlap versus candle range
- zero-range candles are assigned to the row containing that price

The visible histogram is the latest frozen profile only. It is intentionally not drawn historically across every session by default, which keeps object usage stable and avoids chart clutter.

## 5. LVN Definition

Primary/default LVN method:

- `Client Threshold Valley`

Default interpretation:

- `30%` = strict
- `40%` = strong
- `50%` = moderate

Qualification concept:

- LVN average region volume must be less than or equal to the configured percentage of the surrounding average volume
- the LVN region must be bounded by higher-volume structure above and below
- adjacent qualifying rows are merged into a single LVN zone

Stored LVN diagnostics include:

- lower boundary
- upper boundary
- center
- region volume
- average region volume
- average above
- average below
- surrounding average
- depth ratio
- contrast ratio
- row span

Ranking is deterministic and prioritizes:

1. lower depth ratio
2. higher contrast ratio
3. wider qualifying region
4. lower price as final tie-breaker

`LVN #1` means the strongest qualifying LVN under the current normalized criteria. It does not mean the highest-price LVN or the first LVN encountered in price order.

## 6. Entry Logic

Baseline entry behavior:

- no candle confirmation
- long: approach from above, enter at LVN upper boundary
- short: approach from below, enter at LVN lower boundary
- `Minimum Approach Distance` remains configurable

Freshness modes:

- `First Touch Only`
- `One Trade Per LVN`
- `Allow Repeated Trades`

The script uses pending-order state so an LVN is not falsely consumed by same-bar price movement before the corresponding resting order actually existed.

## 7. Risk Modes

Supported risk modes:

- `Fixed Points`
- `LVN Boundary + R`

Fixed Points baseline:

- long: `SL = entry - 5`, `TP = entry + 10`
- short: `SL = entry + 5`, `TP = entry - 10`

Boundary + R:

- long stop: below LVN lower boundary minus buffer
- short stop: above LVN upper boundary plus buffer
- target: risk distance multiplied by `Reward / Risk Multiple`

Debug mode reports active entry, stop, target, risk points, reward points, actual R, and fixed-risk validation where applicable.

## 8. Freshness Modes

Meaning of each repeat-touch mode:

- `First Touch Only`: the first legitimate eligible touch consumes the LVN
- `One Trade Per LVN`: the LVN remains valid until it actually produces one filled trade
- `Allow Repeated Trades`: the LVN can re-arm after exit under the existing session logic

## 9. Native FRVP Comparison

Use `Native FRVP Comparison Mode = On` for Milestone 1 profile validation. This mode is presentation-only and does not alter calculations.

When enabled, the script emphasizes:

- frozen histogram
- prior POC
- frozen profile high and low
- LVN zones
- session boundaries
- row diagnostics table

It also reduces entry and active trade visual clutter.

Recommended comparison procedure:

1. Open the chart on `CME_MINI:MNQ1!` at `1 minute`.
2. Keep the script session at `18:00 -> 16:00 America/New_York`.
3. Set both the script and TradingView FRVP to `24` rows.
4. Compare the same completed session.
5. Check:
   - profile high
   - profile low
   - row boundaries
   - overall shape
   - POC location
   - major HVNs
   - major LVNs
   - LVN zone boundaries

Debug mode now exposes validation fields such as:

- source session date
- source session start and end timestamps
- frozen high and low
- profile range
- row height
- maximum row volume
- POC row and price
- rendered row count
- profile volume sum
- source session volume
- volume delta
- volume conservation error percentage
- configuration fingerprint

`Show Row Diagnostics` adds a 24-row table with:

- row
- low
- high
- volume
- `% of POC`
- LVN flag
- depth
- contrast

## 10. Baseline Backtest Procedure

Run the following controlled sequence.

### Phase A — Profile Validation

Do not judge profitability yet.

Compare the custom histogram against native FRVP across multiple completed sessions and record:

- POC match
- profile shape similarity
- major HVN similarity
- major LVN similarity

### Phase B — Entry Validation

Use `LVN #1 only` and inspect at least `20` trades manually.

Verify:

- source session
- LVN geometry
- direction
- entry boundary
- first-touch state
- stop
- target
- session cutoff behavior

### Phase C — Rank Comparison

Run separately:

- `LVN #1 only`
- `LVN #2 only`
- `LVN #3 only`
- `LVN #4 only`
- `LVN #5 only`

### Phase D — Threshold Comparison

For supported ranks, compare:

- `30%`
- `40%`
- `50%`

### Phase E — Direction Comparison

Compare:

- `Long only`
- `Short only`
- `Both`

### Phase F — Risk Comparison

Compare:

- `Fixed 5 / 10`
- `Boundary + 1.5R`

Change only one independent variable at a time between test runs.

For each meaningful run, record:

- total trades
- win rate
- net P/L
- profit factor
- maximum drawdown
- average trade
- average winner
- average loser
- LVN rank
- direction
- threshold
- risk mode

## 11. Controlled Optimization Procedure

Optimization should start only after:

1. session anchoring is confirmed
2. 24-row boundaries are correct
3. profile volume is conserved
4. the custom profile broadly resembles native FRVP
5. LVNs match the client definition
6. first-touch and risk behavior are verified

Profitability is not a Milestone 1 acceptance criterion. Correctness and reproducible comparative research are.

## 12. Non-Premium Limitations

The non-premium script is the active validation version.

Important constraints:

- `use_bar_magnifier = false`
- historical intrabar sequencing still follows TradingView broker-emulator assumptions
- same-bar entry/exit behavior may differ from premium testing because TradingView plan access changes fill detail

Use the `1 minute` chart as the canonical baseline to reduce ambiguity without requiring Bar Magnifier.

## 13. Known Differences Vs TradingView Native FRVP

This project uses a custom volume-at-price implementation.

It is designed to approximate the client's TradingView Fixed Range Volume Profile workflow, but it is not guaranteed to reproduce TradingView's internal FRVP calculations exactly.

Potential differences can still come from:

- native TradingView lower-timeframe aggregation internals
- row-boundary handling differences
- session anchor mismatches
- missing bars or holiday/weekend session structure
- broker-emulator and plan-dependent fill assumptions

## Sample Size Guidance

Use these as practical research guidelines:

- `< 20 trades`: insufficient for meaningful comparison
- `20-50`: preliminary only
- `50-100`: more useful but still limited
- `100+`: better basis for comparison

These are not strict statistical guarantees. They are decision-making guardrails for structured testing.

## Current Status

Milestone 1 M1 validation build prepared with profile-conservation diagnostics, native-FRVP comparison tools, and controlled backtest configuration. Trading logic remains subject to final on-chart visual and historical validation.
