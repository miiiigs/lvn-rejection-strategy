# CRT + FVG Automated QA Report

- File: `crt_fvg_indicator(4).pine`
- SHA-256: `882d3e51c3d05b282bbd504c1e2786a0170509d89a02fa98a28cfbeef6f2684c`
- Result: **PASS**
- Tests: **87/87 passed**
- Random fuzz cases: **200,000**
- MNQ rows: **19,717 1m bars**

## Category Summary

- Static source: 37/37 passed
- Deterministic logic: 17/17 passed
- Session: 12/12 passed
- Ownership: 6/6 passed
- Display modes: 4/4 passed
- Fill lifecycle: 3/3 passed
- Anchoring: 2/2 passed
- Randomized: 1/1 passed
- MNQ integration: 5/5 passed

## MNQ Raw FVG Cross-Check

- Session-valid 1m windows: 19,672
- Raw bullish 1m FVGs: 1,909
- Raw bearish 1m FVGs: 1,818
- Complete 5m bars: 3,943
- Session-valid 5m windows: 3,898
- Raw bullish 5m FVGs: 444
- Raw bearish 5m FVGs: 354

## Failed Tests

None.

## Limitations

- This environment cannot execute TradingView Pine Script or reproduce Pine realtime rollback directly.
- Static assertions verify the uploaded source text; behavioral tests use an independent Python reference model.
- The supplied MNQ CSV is too short to independently warm a 4H SMA200, so MNQ integration validates raw/session-scoped FVG behavior rather than full SMA-gated CRT ownership.

## Detailed Test Results

- [PASS] Static source: Pine v6
- [PASS] Static source: Indicator, not strategy
- [PASS] Static source: Object caps within TradingView limits
- [PASS] Static source: Session constants 18:00-17:00 boundary
- [PASS] Static source: Default timezone New York
- [PASS] Static source: CRT dual sweep rejection present
- [PASS] Static source: Bull CRT predicate exact structure
- [PASS] Static source: Bear CRT predicate exact structure
- [PASS] Static source: Minimum range equality passes
- [PASS] Static source: 4H confirmed SMA200 uses [1]
- [PASS] Static source: 15m confirmed offsets [2]/[1]
- [PASS] Static source: 30m confirmed offsets [2]/[1]
- [PASS] Static source: Bull FVG strict predicate
- [PASS] Static source: Bear FVG strict predicate
- [PASS] Static source: 1m FVG Candle A anchor time[2]
- [PASS] Static source: 1m confirmation is Candle C close
- [PASS] Static source: 5m lower-chart Candle A uses time[3]
- [PASS] Static source: 5m lower-chart Candle C uses [1]
- [PASS] Static source: FVG box left edge uses Candle A time
- [PASS] Static source: Confirmation time remains stored separately
- [PASS] Static source: Bullish FVG default green
- [PASS] Static source: Bearish FVG default red
- [PASS] Static source: CRT timeframe colors separated from FVG
- [PASS] Static source: FVG labels available and default off
- [PASS] Static source: Three FVG display modes present
- [PASS] Static source: Hidden FVGs not added to display arrays
- [PASS] Static source: Metrics recorded independently of display creation
- [PASS] Static source: Most Recent fully removes prior display record
- [PASS] Static source: FVG fill predicates exact
- [PASS] Static source: Native FVG blocks retroactive Candle C fill
- [PASS] Static source: Lower-chart 5m permits activation-bar fill
- [PASS] Static source: CRT lifecycle runs before FVG processing
- [PASS] Static source: Owner must match direction/session and precede FVG
- [PASS] Static source: Owner selection scans newest to oldest
- [PASS] Static source: FVG A/B/C same-session guard
- [PASS] Static source: No invalid descending by -1 loop
- [PASS] Static source: Comparison table exposes eligible CRT denominator
- [PASS] Deterministic logic: Bull CRT canonical positive
- [PASS] Deterministic logic: Bull CRT rejects C2 high above C1
- [PASS] Deterministic logic: Bull CRT rejects close equal C1 low
- [PASS] Deterministic logic: Bull CRT rejects close equal C1 high
- [PASS] Deterministic logic: Bull CRT rejects dual sweep
- [PASS] Deterministic logic: Bear CRT canonical positive
- [PASS] Deterministic logic: Bear CRT rejects C2 low below C1
- [PASS] Deterministic logic: Bear CRT rejects close equal C1 low
- [PASS] Deterministic logic: Bear CRT rejects close equal C1 high
- [PASS] Deterministic logic: Bull FVG strict positive
- [PASS] Deterministic logic: Bull FVG equality rejected
- [PASS] Deterministic logic: Bear FVG strict positive
- [PASS] Deterministic logic: Bear FVG equality rejected
- [PASS] Deterministic logic: Bull FVG partial fill stays active
- [PASS] Deterministic logic: Bull FVG full fill triggers
- [PASS] Deterministic logic: Bear FVG partial fill stays active
- [PASS] Deterministic logic: Bear FVG full fill triggers
- [PASS] Session: 17:59 outside session
- [PASS] Session: 18:00 inside session
- [PASS] Session: 23:59 inside session
- [PASS] Session: 00:00 inside prior session
- [PASS] Session: 16:59 inside session
- [PASS] Session: 17:00 outside session
- [PASS] Session: DST spring 16:59 inside
- [PASS] Session: DST spring 17:00 outside
- [PASS] Session: DST fall 16:59 inside
- [PASS] Session: DST fall 17:00 outside
- [PASS] Session: 00:00 and prior-day 18:00 share session key
- [PASS] Session: Next 18:00 starts new session key
- [PASS] Ownership: Newest eligible same-direction CRT owns FVG
- [PASS] Ownership: Completed CRT cannot own FVG
- [PASS] Ownership: Direction mismatch cannot own FVG
- [PASS] Ownership: CRT confirmation must strictly precede FVG
- [PASS] Ownership: Bull CRT target hit same bar blocks FVG ownership
- [PASS] Ownership: Bear CRT target hit same bar blocks FVG ownership
- [PASS] Display modes: First: 150 events -> 150 metrics / 1 display
- [PASS] Display modes: Most Recent: 150 events -> latest only
- [PASS] Display modes: All: 150 events cap 100 -> latest 100 displays
- [PASS] Display modes: First is independent per 1m/5m stream
- [PASS] Fill lifecycle: Native 1m cannot fill on creation bar
- [PASS] Fill lifecycle: Native 1m can fill next bar
- [PASS] Fill lifecycle: Lower-chart confirmed 5m can fill activation bar
- [PASS] Anchoring: 1m A start is 2 bars before C, confirmation at C close
- [PASS] Anchoring: 5m lower-chart A starts 15m before confirmation
- [PASS] Randomized: CRT/FVG mutual-exclusion and invariant fuzzing — 200,000 randomized candle pairs/triples; 0 invariant violations
- [PASS] MNQ integration: CSV has monotonic 1m data
- [PASS] MNQ integration: OHLC validity
- [PASS] MNQ integration: Raw 1m data contains both bullish and bearish FVGs
- [PASS] MNQ integration: Raw 5m data contains both bullish and bearish FVGs
- [PASS] MNQ integration: No cross-session FVG windows included