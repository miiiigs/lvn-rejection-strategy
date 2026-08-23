# CRT Indicator v0.2 Build Notes

## Client lifecycle implemented

- **Auto: History Keep / Live Hide** (default): historical target hits are retained for review/backtesting; a target hit on the live realtime bar removes the range.
- **Always Keep**: completed ranges are retained everywhere. Useful for Bar Replay/backtesting.
- **Always Hide**: completed ranges are removed everywhere.

When a completed range is retained, its right edge freezes on the target-hit bar instead of extending indefinitely.
Completed retained ranges can optionally be dimmed and their label receives `• HIT` for readability.

## Important Pine behavior

In Auto mode, a range removed live can reappear after chart/script reload because the previously live bar is then historical. That is intentional and matches the client's request to preserve completed ranges for historical/backtesting review.

## Preserved without modification

- 15m / 30m CRT predicates
- dual-sweep rejection
- Candle 1 minimum-range filter
- confirmed `[2]/[1]` MTF source candles
- confirmed 4H SMA200 filter
- rollback-safe realtime CRT recreation
- first post-confirmation target-hit handling

## Automated static regression

**16/16 checks passed.**

No static regression failures detected.


Pine compilation and TradingView runtime validation still require TradingView.
