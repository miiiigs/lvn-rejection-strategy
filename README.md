# LVN Rejection Strategy

This repository contains a first functional prototype of the TradingView strategy in `lvn_rejection_strategy.pine`.

- Build a custom volume profile for each completed `18:00-16:00` session in `America/New_York`.
- Freeze that session's LVNs at session end.
- Trade those frozen levels during the following session only.
- Use limit orders at the LVN center price so the backtest models "touch the level" more closely than close-of-bar entries.

## What this version includes

- Pine Script v6 `strategy()`
- Session-aware profile construction with timezone support
- Chart-bar overlap approximation into configurable profile rows
- Modular LVN detection with three selectable methods:
  - `Local Minimum`
  - `Relative to POC`
  - `Neighbor Threshold`
- Deterministic provisional LVN ranking by lowest profile-row volume
- Rank-based LVN enablement for LVN #1 through LVN #5
- Fixed-points stops/targets
- Provisional `LVN Boundary + R` stop/target mode
- One-position-at-a-time behavior
- Configurable repeated-touch handling
- Date-range filtering for order submission
- Visual LVN, POC, session, and active SL/TP plotting

## Important implementation notes

- The strategy isolates the "freeze previous session, trade next session" lifecycle so it can be changed later without rewriting the whole script.
- Directional approach is determined conservatively from the prior settled close, not from the current bar's full intrabar path. That avoids future-knowledge bias when deciding whether the market approached an LVN from above or below.
- The `Minimum Approach Distance` input only controls how far away the prior reference price must be before a resting LVN order is considered valid. It does not widen the LVN into a touch zone.
- Entry orders are assigned to a shared `strategy.oca.cancel` group so one filled LVN order can cancel the remaining pending LVN entries.
- `use_bar_magnifier = true` and `calc_on_order_fills = true` are enabled by default. TradingView still controls the final fidelity based on account tier, chart timeframe, and available lower-timeframe history.
- `backtest_fill_limits_assumption = 0` is explicit in the strategy declaration, which means the emulator assumes a limit fills when price reaches that level unless the user changes the strategy's limit-fill setting in TradingView.
- If the script first loads in the middle of a session, it skips freezing that first partial build rather than using incomplete profile data.
- Commission and slippage defaults are set in the `strategy()` declaration. TradingView users can still override them from the strategy's `Properties` tab.

## Known limits in this first version

- UI toggles are provided for LVN ranks `#1` through `#5`. The detection engine can rank more than five levels, but ranks above five are not individually toggleable yet.
- The LVN rank labels are a provisional volume-based ranking system, not a client-confirmed semantic ordering such as highest-price LVN, nearest above POC, or nearest below POC.
- The custom profile engine does not reproduce TradingView's native Fixed Range Volume Profile. It approximates volume-at-price by distributing each chart bar's volume across overlapping rows.
- The optional full horizontal histogram was intentionally deferred to keep the strategy core lean and resource-safe.
- Pine fills still depend on TradingView broker-emulator rules. On coarse chart timeframes, touch ordering can remain ambiguous even with bar magnifier enabled.
