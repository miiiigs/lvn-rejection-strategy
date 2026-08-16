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
- `Use Minimum LVN Contrast = Off`
- `Minimum Surrounding Volume Contrast = 1.25`

Exact surrounding-volume calculation:

- For a candidate row, the script averages the `surroundingRows` rows immediately below and the `surroundingRows` rows immediately above.
- For a merged multi-row LVN region, it averages the `surroundingRows` rows below the region and the `surroundingRows` rows above the region.
- The surrounding average used for qualification is `(averageBelow + averageAbove) / 2`.

Qualification rule:

- `candidateRegionAverageVolume <= surroundingAverage * (lvnThresholdPct / 100.0)`
- `averageBelow > candidateRegionAverageVolume`
- `averageAbove > candidateRegionAverageVolume`
- Optional contrast filter:
  - `surroundingAverage / candidateRegionAverageVolume >= minContrastRatio`

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
  - average volume above
  - average volume below
  - depth ratio
  - contrast ratio
  - row span

Ranking method:

1. lower depth ratio first
2. larger surrounding-volume contrast
3. wider LVN region
4. lower price as deterministic final tie-breaker

Depth ratio is `candidateRegionAverageVolume / surroundingAverage`.

Contrast ratio is `surroundingAverage / candidateRegionAverageVolume`.

Lower ratios represent deeper or stronger LVNs.
Higher contrast ratios represent stronger separation from surrounding volume.

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

Freshness / repeat controls:

- `First Touch Only`: the first eligible zone contact only consumes the LVN if a resting order was already active before that touch
- `One Trade Per LVN`: the LVN stays available until it actually produces a trade, then becomes disabled for the session
- `Allow Repeated Trades`: the LVN can re-arm after exit

Optional entry-window control:

- `Use Entry Session Filter`
- `Entry Session`
- `Block New Entries Before Session End`
- `Entry Cutoff Minutes`

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

Optional POC context filters:

- `Use Minimum Distance From POC`
- `Minimum Distance From POC`
- `Trade LVNs Above POC`
- `Trade LVNs Below POC`

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

- a frozen 24-row volume profile histogram built from the same row volumes used for LVN detection
- frozen LVN zone upper and lower boundaries
- optional center line
- previous session POC
- session start and end markers
- active stop and target
- LVN labels with depth, contrast, class, and surrounding-volume context

`Show Debug Diagnostics` is off by default and exposes profile-validation details such as frozen high and low, row height, POC row, detected LVN count, top-zone metadata, contrast-filter status, freshness mode, and active session or POC filters.

## Methodology Disclosure

These scripts use a custom volume-at-price implementation.

TradingView's built-in volume profiles use lower-timeframe data internally. The current implementation uses a chart-bar overlap approximation isolated behind profile-building functions so a lower-timeframe mode can be introduced later without changing the trade engine.

Detected levels may differ from TradingView's native Fixed Range Volume Profile.

Historical fills may also differ between the premium and non-premium variants because Bar Magnifier access and lower-timeframe historical detail are TradingView-plan dependent.

## Visual Profile Validation

To compare the custom profile against TradingView's native Fixed Range Volume Profile:

1. Enable `Show Volume Profile Histogram`.
2. Manually draw TradingView's Fixed Range Volume Profile over the same `18:00 -> 16:00 America/New_York` session.
3. Set TradingView FRVP to `24` rows.
4. Compare the custom histogram row-by-row against the FRVP shape.
5. Compare the POC row and the detected LVN zones.

Current visualization notes:

- The histogram uses the exact frozen row-volume array that also drives the strategy's LVNs.
- The most recent frozen profile is displayed next to the beginning of the following session and remains stationary once drawn.
- Row width is normalized by `rowVolume / maxRowVolume`, where `maxRowVolume` is typically the POC row volume.
- The POC row is highlighted separately and LVN rows are tinted so valleys are easier to compare visually.

Differences can still occur because the current custom engine uses chart-bar overlap allocation rather than TradingView's internal native FRVP methodology.

## Recommended First Validation Test

Use this baseline first:

- Symbol: `CME_MINI:MNQ1!`
- Timeframe: `1 minute`
- Rows: `24`
- LVN Method: `Client Threshold Valley`
- Threshold: `40%`
- Surrounding Rows: `2`
- Contrast Filter: `Off`
- LVN #1: `On`
- LVN #2-#10: `Off`
- Longs: `On`
- Shorts: `On`
- Freshness: `First Touch Only`
- Approach Distance: `0`
- Entry Session Filter: `Off`
- Risk: `Fixed Points`
- SL: `5`
- TP: `10`
- POC Filters: `Off`
- Order Size: `1`
- Debug: `On` during validation

Run separate tests for `LVN #1`, `LVN #2`, and `LVN #3` rather than enabling several ranks at once.

## Controlled Testing Checklist

- A. `LVN #1 only`, `40%`, `Fixed 5 / 10`
- B. `LVN #2 only`, `40%`, `Fixed 5 / 10`
- C. `LVN #3 only`, `40%`, `Fixed 5 / 10`
- D. `LVN #1 only`, `30%`
- E. `LVN #1 only`, `50%`
- F. `LVN #1`, `Fixed 5 / 10`
- G. `LVN #1`, `Boundary + 1.5R`

Only change one variable at a time between comparisons.

Record:

- Trade count
- Net P/L
- Win rate
- Profit factor
- Max drawdown
- Average trade

Do not treat a configuration as superior when the sample size is still very small.

## Current Status

Client-defined LVN algorithm implemented and strategy strengthened, pending TradingView compilation, visual FRVP comparison, and backtest validation.
