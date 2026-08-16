# LVN Rejection Strategy

This repository contains two TradingView Pine Script v6 strategy variants:

- [lvn_rejection_strategy.pine](/C:/dev/lvn-rejection-strategy/lvn_rejection_strategy.pine): premium-capable version with `use_bar_magnifier = true`
- [lvn_rejection_strategy_non_premium.pine](/C:/dev/lvn-rejection-strategy/lvn_rejection_strategy_non_premium.pine): non-premium-safe version with `use_bar_magnifier = false`

Both scripts share the same session logic, LVN methodology, entries, risk model, and visual diagnostics.

## Strategy

- Profile session: `18:00 -> 16:00 America/New_York`
- Default rows: `24`
- Workflow:
  - Build the custom volume-at-price profile during Session N
  - Freeze LVN zones when Session N ends
  - Trade only those frozen LVNs during Session N+1
- The strategy remains a `strategy()` script and is intended to generate real Strategy Tester trades.

## LVN Definition

Primary/default method: `Client Threshold Valley`

LVN = a low-volume price region whose average volume is less than or equal to a configurable percentage of the surrounding price-level average volume, and that region must be bounded by higher-volume structure above and below.

Defaults:

- `LVN Threshold (%) = 40`
- `30%` = strict
- `40%` = strong
- `50%` = moderate
- `Surrounding Rows Per Side = 2`

Exact surrounding-volume calculation:

- For a candidate row, the script averages the `surroundingRows` rows immediately below and the `surroundingRows` rows immediately above.
- For a merged multi-row LVN region, it averages the `surroundingRows` rows below the region and the `surroundingRows` rows above the region.
- The surrounding average used for qualification is `(averageBelow + averageAbove) / 2`.

Qualification rule:

- `candidateRegionAverageVolume <= surroundingAverage * (lvnThresholdPct / 100.0)`
- `averageBelow > candidateRegionAverageVolume`
- `averageAbove > candidateRegionAverageVolume`

This boundary check is meant to avoid classifying profile tails as valid LVNs.

## Region Merging And Ranking

- Adjacent qualifying rows are merged into a single LVN zone.
- Stored zone data includes:
  - lower boundary
  - upper boundary
  - center
  - average LVN volume
  - total LVN volume
  - surrounding average volume
  - depth ratio
  - row span

Ranking method:

1. lower depth ratio first
2. larger surrounding-volume contrast
3. wider LVN region
4. lower price as deterministic final tie-breaker

Depth ratio is `candidateRegionAverageVolume / surroundingAverage`.

Lower ratios represent deeper or stronger LVNs.

Legacy diagnostic methods are still available:

- `Local Minimum`
- `Relative to POC`
- `Neighbor Threshold`

## Entries

- From above -> long at the LVN upper boundary
- From below -> short at the LVN lower boundary
- No candlestick confirmation is required
- `Minimum Approach Distance` controls how far the prior settled price must be from the zone before a touch is considered eligible
- Competing entry orders share OCA cancellation so one fill cancels the rest

Per-rank controls remain available for `LVN #1` through `LVN #10`.

Additional directional controls:

- `Trade Longs`
- `Trade Shorts`

## Risk

Supported risk modes:

- `Fixed Points`
- `LVN Boundary + R`

Fixed Points:

- Long: `SL = entry - fixedSL`, `TP = entry + fixedTP`
- Short: `SL = entry + fixedSL`, `TP = entry - fixedTP`

LVN Boundary + R:

- Long stop: below the LVN lower boundary, optionally offset by `LVN Boundary Buffer`
- Short stop: above the LVN upper boundary, optionally offset by `LVN Boundary Buffer`
- Target uses the resulting risk distance times `Reward / Risk Multiple`
- Trades are rejected when risk is less than or equal to `syminfo.mintick`

## Backtesting And Reliability

- Start and end date filters are preserved
- New orders are not placed outside the active backtest window
- Pending entry orders are cancelled whenever conditions become invalid
- Frozen Session N levels are not recalculated using Session N+1 data
- Current-session developing profile data is not traded
- Session-start-mid-history cases are skipped defensively to avoid freezing partial profiles
- Zero-volume or unusable sessions are skipped without fabricating volume

## Visuals And Diagnostics

The scripts can display:

- frozen LVN zone upper and lower boundaries
- optional center line
- previous session POC
- session start and end markers
- active stop and target
- LVN labels with depth and surrounding-volume context

`Show Debug Diagnostics` is off by default and exposes profile-validation details such as frozen high and low, row height, POC row, detected LVN count, and top-zone metadata.

## Methodology Disclosure

These scripts use a custom volume-at-price implementation.

TradingView's built-in volume profiles use lower-timeframe data internally. The current implementation uses a chart-bar overlap approximation isolated behind profile-building functions so a lower-timeframe mode can be introduced later without changing the trade engine.

Detected levels may differ from TradingView's native Fixed Range Volume Profile.

Historical fills may also differ between the premium and non-premium variants because Bar Magnifier access and lower-timeframe historical detail are TradingView-plan dependent.

## Current Status

Client-defined LVN algorithm implemented and strategy strengthened, pending TradingView compilation, visual FRVP comparison, and backtest validation.
