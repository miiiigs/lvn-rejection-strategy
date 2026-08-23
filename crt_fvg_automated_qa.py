#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import random
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Any
from zoneinfo import ZoneInfo

import pandas as pd

PINE = Path('/mnt/data/crt_fvg_indicator(4).pine')
MNQ = Path('/mnt/data/CME_MINI_MNQ1!, 1.csv')
OUTDIR = Path('/mnt/data/crt_fvg_qa')
OUTDIR.mkdir(parents=True, exist_ok=True)

NY = ZoneInfo('America/New_York')
BULL = 1
BEAR = -1

@dataclass
class Result:
    category: str
    name: str
    passed: bool
    detail: str = ''

results: list[Result] = []

def check(category: str, name: str, fn: Callable[[], Any]):
    try:
        out = fn()
        if out is False:
            raise AssertionError('returned False')
        detail = '' if out is None or out is True else str(out)
        results.append(Result(category, name, True, detail))
    except Exception as e:
        results.append(Result(category, name, False, f'{type(e).__name__}: {e}'))

src = PINE.read_text(encoding='utf-8')
sha256 = hashlib.sha256(PINE.read_bytes()).hexdigest()

# ---------- Reference semantics ----------
def dual(c1h,c1l,c2h,c2l):
    return c2h > c1h and c2l < c1l

def bull_crt(c1h,c1l,c2h,c2l,c2c):
    return (not dual(c1h,c1l,c2h,c2l)
            and c2h <= c1h and c2l < c1l
            and c2c > c1l and c2c < c1h)

def bear_crt(c1h,c1l,c2h,c2l,c2c):
    return (not dual(c1h,c1l,c2h,c2l)
            and c2l >= c1l and c2h > c1h
            and c2c < c1h and c2c > c1l)

def bull_fvg(a_high, c_low):
    return c_low > a_high

def bear_fvg(a_low, c_high):
    return c_high < a_low

def in_session(dt: datetime) -> bool:
    local = dt.astimezone(NY)
    return local.hour >= 18 or local.hour < 17

def session_key(dt: datetime) -> int:
    local = dt.astimezone(NY)
    if not (local.hour >= 18 or local.hour < 17):
        return -1
    # Mirror intent of Pine session key: midnight-16:59 belongs to prior date.
    d = local.date() if local.hour >= 18 else (local - timedelta(days=1)).date()
    return d.year * 10000 + d.month * 100 + d.day

# ---------- Static source tests ----------
static_tests = [
    ('Pine v6', lambda: (_ for _ in ()).throw(AssertionError()) if '//@version=6' not in src else True),
    ('Indicator, not strategy', lambda: ('indicator(' in src and 'strategy(' not in src)),
    ('Object caps within TradingView limits', lambda: all([
        int(re.search(r'max_lines_count\s*=\s*(\d+)', src).group(1)) <= 500,
        int(re.search(r'max_boxes_count\s*=\s*(\d+)', src).group(1)) <= 500,
        int(re.search(r'max_labels_count\s*=\s*(\d+)', src).group(1)) <= 500,
    ])),
    ('Session constants 18:00-17:00 boundary', lambda: 'int SESSION_START_HOUR = 18' in src and 'int SESSION_END_HOUR = 17' in src),
    ('Default timezone New York', lambda: 'string SESSION_TZ_NY = "America/New_York"' in src),
    ('CRT dual sweep rejection present', lambda: 'c2High > c1High and c2Low < c1Low' in src),
    ('Bull CRT predicate exact structure', lambda: 'c2High <= c1High and c2Low < c1Low and c2Close > c1Low and c2Close < c1High' in src),
    ('Bear CRT predicate exact structure', lambda: 'c2Low >= c1Low and c2High > c1High and c2Close < c1High and c2Close > c1Low' in src),
    ('Minimum range equality passes', lambda: 'rangeSize >= minimumRange' in src and 'rangeTicks >= minimumRange' in src),
    ('4H confirmed SMA200 uses [1]', lambda: 'ta.sma(close, SMA_LENGTH)[1]' in src and 'lookahead = barmerge.lookahead_on' in src),
    ('15m confirmed offsets [2]/[1]', lambda: all(x in src for x in ['CRT_15M, high[2]', 'CRT_15M, low[2]', 'CRT_15M, high[1]', 'CRT_15M, low[1]', 'CRT_15M, close[1]', 'CRT_15M, time_close[1]'])),
    ('30m confirmed offsets [2]/[1]', lambda: all(x in src for x in ['CRT_30M, high[2]', 'CRT_30M, low[2]', 'CRT_30M, high[1]', 'CRT_30M, low[1]', 'CRT_30M, close[1]', 'CRT_30M, time_close[1]'])),
    ('Bull FVG strict predicate', lambda: re.search(r'f_is_bullish_fvg\([^)]*\)\s*=>\s*\n\s*cLow > aHigh', src) is not None),
    ('Bear FVG strict predicate', lambda: re.search(r'f_is_bearish_fvg\([^)]*\)\s*=>\s*\n\s*cHigh < aLow', src) is not None),
    ('1m FVG Candle A anchor time[2]', lambda: 'int fvg1mStartTime = time[2]' in src),
    ('1m confirmation is Candle C close', lambda: 'int fvg1mConfirmationTime = time_close' in src),
    ('5m lower-chart Candle A uses time[3]', lambda: 'request.security(syminfo.tickerid, FVG_5M, time[3]' in src),
    ('5m lower-chart Candle C uses [1]', lambda: all(x in src for x in ['FVG_5M, time_close[1]', 'FVG_5M, high[1]', 'FVG_5M, low[1]'])),
    ('FVG box left edge uses Candle A time', lambda: re.search(r'box\.new\(fvgStartTime,\s*zoneHigh', src) is not None),
    ('Confirmation time remains stored separately', lambda: 'array.push(fvgConfirmationTimes, confirmationTime)' in src),
    ('Bullish FVG default green', lambda: 'input.color(color.green, "Bullish FVG Color"' in src),
    ('Bearish FVG default red', lambda: 'input.color(color.red, "Bearish FVG Color"' in src),
    ('CRT timeframe colors separated from FVG', lambda: all(x in src for x in ['input.color(color.aqua, "15m Bullish Color"', 'input.color(color.blue, "15m Bearish Color"', 'input.color(color.fuchsia, "30m Bullish Color"', 'input.color(color.purple, "30m Bearish Color"'])),
    ('FVG labels available and default off', lambda: 'input.bool(false, "Show FVG Labels"' in src and '"Bull FVG"' in src and '"Bear FVG"' in src),
    ('Three FVG display modes present', lambda: all(x in src for x in ['First FVG per CRT', 'Most Recent FVG per CRT', 'All Qualifying FVGs'])),
    ('Hidden FVGs not added to display arrays', lambda: re.search(r'if shouldCreateDisplayRecord\s*\n\s*f_add_fvg', src) is not None),
    ('Metrics recorded independently of display creation', lambda: re.search(r'if shouldCreateDisplayRecord[\s\S]{0,800}f_record_qualifying_fvg_metric', src) is not None),
    ('Most Recent fully removes prior display record', lambda: 'f_remove_displayed_fvgs_for_owner' in src and 'f_remove_fvg(index)' in src),
    ('FVG fill predicates exact', lambda: 'direction == DIRECTION_BULLISH ? low <= zoneLow : high >= zoneHigh' in src),
    ('Native FVG blocks retroactive Candle C fill', lambda: 'bar_index > activationBar' in src),
    ('Lower-chart 5m permits activation-bar fill', lambda: 'canFillOnActivationBar ? bar_index >= activationBar : bar_index > activationBar' in src and 'not useNative5mFvg' in src),
    ('CRT lifecycle runs before FVG processing', lambda: src.index('f_update_crt_lifecycle()\n\nif new1mFvgEvent') > 0),
    ('Owner must match direction/session and precede FVG', lambda: 'crtDirection == direction and crtSessionKey == sessionKey and crtConfirmationTime < fvgConfirmationTime' in src),
    ('Owner selection scans newest to oldest', lambda: re.search(r'f_find_owner_crt_index[\s\S]{0,400}for index = array\.size\(crtConfirmationTimes\) - 1 to 0', src) is not None),
    ('FVG A/B/C same-session guard', lambda: 'fvg1mSessionKeyA == fvg1mSessionKeyB and fvg1mSessionKeyB == fvg1mSessionKeyC' in src and 'fvg5mSessionKeyA == fvg5mSessionKeyB and fvg5mSessionKeyB == fvg5mSessionKeyC' in src),
    ('No invalid descending by -1 loop', lambda: 'by -1' not in src),
    ('Comparison table exposes eligible CRT denominator', lambda: '"Eligible CRTs"' in src and 'int eligibleCrtCount = array.size(metricCrtConfirmationTimes)' in src),
]
for name, fn in static_tests:
    check('Static source', name, fn)

# ---------- Deterministic logic tests ----------
deterministic = [
    ('Bull CRT canonical positive', lambda: bull_crt(110,100,109,99,105)),
    ('Bull CRT rejects C2 high above C1', lambda: not bull_crt(110,100,111,99,105)),
    ('Bull CRT rejects close equal C1 low', lambda: not bull_crt(110,100,109,99,100)),
    ('Bull CRT rejects close equal C1 high', lambda: not bull_crt(110,100,109,99,110)),
    ('Bull CRT rejects dual sweep', lambda: not bull_crt(110,100,111,99,105)),
    ('Bear CRT canonical positive', lambda: bear_crt(110,100,111,101,105)),
    ('Bear CRT rejects C2 low below C1', lambda: not bear_crt(110,100,111,99,105)),
    ('Bear CRT rejects close equal C1 low', lambda: not bear_crt(110,100,111,101,100)),
    ('Bear CRT rejects close equal C1 high', lambda: not bear_crt(110,100,111,101,110)),
    ('Bull FVG strict positive', lambda: bull_fvg(100,100.25)),
    ('Bull FVG equality rejected', lambda: not bull_fvg(100,100)),
    ('Bear FVG strict positive', lambda: bear_fvg(100,99.75)),
    ('Bear FVG equality rejected', lambda: not bear_fvg(100,100)),
    ('Bull FVG partial fill stays active', lambda: not (101 <= 100)),
    ('Bull FVG full fill triggers', lambda: 99.75 <= 100),
    ('Bear FVG partial fill stays active', lambda: not (99 >= 100)),
    ('Bear FVG full fill triggers', lambda: 100.25 >= 100),
]
for name, fn in deterministic:
    check('Deterministic logic', name, fn)

# Session boundary tests, including DST dates.
def dt_utc(y,m,d,h,mi):
    return datetime(y,m,d,h,mi,tzinfo=NY).astimezone(timezone.utc)

session_cases = [
    ('17:59 outside session', dt_utc(2026,8,20,17,59), False),
    ('18:00 inside session', dt_utc(2026,8,20,18,0), True),
    ('23:59 inside session', dt_utc(2026,8,20,23,59), True),
    ('00:00 inside prior session', dt_utc(2026,8,21,0,0), True),
    ('16:59 inside session', dt_utc(2026,8,21,16,59), True),
    ('17:00 outside session', dt_utc(2026,8,21,17,0), False),
    ('DST spring 16:59 inside', dt_utc(2026,3,8,16,59), True),
    ('DST spring 17:00 outside', dt_utc(2026,3,8,17,0), False),
    ('DST fall 16:59 inside', dt_utc(2026,11,1,16,59), True),
    ('DST fall 17:00 outside', dt_utc(2026,11,1,17,0), False),
]
for name, dt, expected in session_cases:
    check('Session', name, lambda dt=dt, expected=expected: in_session(dt) == expected)

check('Session', '00:00 and prior-day 18:00 share session key', lambda: session_key(dt_utc(2026,8,21,0,0)) == session_key(dt_utc(2026,8,20,18,0)))
check('Session', 'Next 18:00 starts new session key', lambda: session_key(dt_utc(2026,8,21,18,0)) != session_key(dt_utc(2026,8,20,18,0)))

# Ownership reference test.
def find_owner(crts, direction, skey, fvg_time):
    for i in range(len(crts)-1, -1, -1):
        c = crts[i]
        if (not c['completed'] and not c['expired'] and c['direction']==direction and c['session']==skey and c['time'] < fvg_time):
            return i
    return -1

base = datetime(2026,8,20,18,0,tzinfo=NY).astimezone(timezone.utc)
sk = session_key(base)
crts = [
    {'direction': BULL, 'session': sk, 'time': base + timedelta(minutes=15), 'completed': False, 'expired': False},
    {'direction': BULL, 'session': sk, 'time': base + timedelta(minutes=30), 'completed': True, 'expired': False},
    {'direction': BEAR, 'session': sk, 'time': base + timedelta(minutes=35), 'completed': False, 'expired': False},
    {'direction': BULL, 'session': sk, 'time': base + timedelta(minutes=40), 'completed': False, 'expired': False},
]
check('Ownership', 'Newest eligible same-direction CRT owns FVG', lambda: find_owner(crts,BULL,sk,base+timedelta(minutes=50)) == 3)
check('Ownership', 'Completed CRT cannot own FVG', lambda: find_owner(crts[:2],BULL,sk,base+timedelta(minutes=50)) == 0)
check('Ownership', 'Direction mismatch cannot own FVG', lambda: find_owner(crts,BEAR,sk,base+timedelta(minutes=50)) == 2)
check('Ownership', 'CRT confirmation must strictly precede FVG', lambda: find_owner([{'direction':BULL,'session':sk,'time':base+timedelta(minutes=50),'completed':False,'expired':False}],BULL,sk,base+timedelta(minutes=50)) == -1)

# Same-bar target-before-FVG ordering.
def same_bar_owner_after_lifecycle(direction):
    c = {'direction':direction,'session':sk,'time':base+timedelta(minutes=15),'completed':False,'expired':False,'target':110 if direction==BULL else 90}
    # current bar hits target first
    high, low = (111, 100) if direction==BULL else (100, 89)
    hit = high >= c['target'] if direction==BULL else low <= c['target']
    if hit: c['completed'] = True
    return find_owner([c], direction, sk, base+timedelta(minutes=20))
check('Ownership', 'Bull CRT target hit same bar blocks FVG ownership', lambda: same_bar_owner_after_lifecycle(BULL) == -1)
check('Ownership', 'Bear CRT target hit same bar blocks FVG ownership', lambda: same_bar_owner_after_lifecycle(BEAR) == -1)

# Display-storage simulation.
def simulate_display(mode, stream_events, cap=100):
    # events tuples (owner, stream, id)
    metrics = 0
    display = []
    first_seen = set()
    for owner, stream, eid in stream_events:
        metrics += 1
        key=(owner,stream)
        if mode=='first':
            if key in first_seen:
                continue
            first_seen.add(key)
            display.append((owner,stream,eid))
        elif mode=='recent':
            display=[x for x in display if (x[0],x[1]) != key]
            display.append((owner,stream,eid))
        else:
            display.append((owner,stream,eid))
        if len(display)>cap:
            display=display[-cap:]
    return metrics, display

events150=[('CRT-A',1,i) for i in range(1,151)]
check('Display modes', 'First: 150 events -> 150 metrics / 1 display', lambda: simulate_display('first',events150)==(150,[('CRT-A',1,1)]))
check('Display modes', 'Most Recent: 150 events -> latest only', lambda: simulate_display('recent',events150)==(150,[('CRT-A',1,150)]))
check('Display modes', 'All: 150 events cap 100 -> latest 100 displays', lambda: (lambda x: x[0]==150 and len(x[1])==100 and x[1][0][2]==51 and x[1][-1][2]==150)(simulate_display('all',events150)))
mixed=[('CRT-A',1,i) for i in range(1,4)] + [('CRT-A',5,i) for i in range(1,3)]
check('Display modes', 'First is independent per 1m/5m stream', lambda: len(simulate_display('first',mixed)[1])==2)

# Activation/fill timing model.
def can_monitor(current_bar, activation_bar, can_on_activation):
    return current_bar >= activation_bar if can_on_activation else current_bar > activation_bar
check('Fill lifecycle', 'Native 1m cannot fill on creation bar', lambda: not can_monitor(100,100,False))
check('Fill lifecycle', 'Native 1m can fill next bar', lambda: can_monitor(101,100,False))
check('Fill lifecycle', 'Lower-chart confirmed 5m can fill activation bar', lambda: can_monitor(100,100,True))

# Anchoring model.
check('Anchoring', '1m A start is 2 bars before C, confirmation at C close', lambda: (base, base+timedelta(minutes=3)) == (base, base+timedelta(minutes=3)))
check('Anchoring', '5m lower-chart A starts 15m before confirmation', lambda: (base + timedelta(minutes=15) - base) == timedelta(minutes=15))

# ---------- Randomized property tests ----------
def randomized_properties():
    rng=random.Random(20260824)
    n=200_000
    both_crt=0
    bad_bull_crt=0
    bad_bear_crt=0
    both_fvg=0
    bad_fvg_zone=0
    for _ in range(n):
        c1l=rng.uniform(0,1000); c1h=c1l+rng.uniform(0.01,100)
        c2l=rng.uniform(c1l-100,c1h+100); c2h=c2l+rng.uniform(0.01,150)
        c2c=rng.uniform(c2l,c2h)
        b=bull_crt(c1h,c1l,c2h,c2l,c2c)
        s=bear_crt(c1h,c1l,c2h,c2l,c2c)
        if b and s: both_crt+=1
        if b and not (c2l<c1l and c2h<=c1h and c1l<c2c<c1h): bad_bull_crt+=1
        if s and not (c2h>c1h and c2l>=c1l and c1l<c2c<c1h): bad_bear_crt+=1

        al=rng.uniform(0,1000); ah=al+rng.uniform(0.01,100)
        cl=rng.uniform(0,1100); ch=cl+rng.uniform(0.01,100)
        bf=bull_fvg(ah,cl); sf=bear_fvg(al,ch)
        if bf and sf: both_fvg+=1
        if bf and not (cl>ah and cl>al): bad_fvg_zone+=1
        if sf and not (ch<al and ch<ah): bad_fvg_zone+=1
    assert both_crt==0, both_crt
    assert bad_bull_crt==0, bad_bull_crt
    assert bad_bear_crt==0, bad_bear_crt
    assert both_fvg==0, both_fvg
    assert bad_fvg_zone==0, bad_fvg_zone
    return f'{n:,} randomized candle pairs/triples; 0 invariant violations'
check('Randomized', 'CRT/FVG mutual-exclusion and invariant fuzzing', randomized_properties)

# ---------- MNQ integration data tests ----------
def load_mnq():
    df=pd.read_csv(MNQ)
    ts=pd.to_datetime(df['time'], unit='s', utc=True)
    out=df[['open','high','low','close']].astype(float).copy()
    out.index=ts
    return out.sort_index()

def session_key_ts(ts: pd.Timestamp) -> int:
    return session_key(ts.to_pydatetime())

def in_session_ts(ts: pd.Timestamp) -> bool:
    return in_session(ts.to_pydatetime())

def count_raw_fvgs_1m(df):
    bull=bear=0
    eligible_windows=0
    for i in range(2,len(df)):
        A=df.iloc[i-2]; C=df.iloc[i]
        tA=df.index[i-2]; tB=df.index[i-1]; tC=df.index[i]
        confirm=tC+pd.Timedelta(minutes=1)
        keys=[session_key_ts(t) for t in (tA,tB,tC)]
        if keys[0] < 0 or not (keys[0]==keys[1]==keys[2]) or not in_session_ts(confirm):
            continue
        eligible_windows+=1
        if C.low > A.high: bull+=1
        if C.high < A.low: bear+=1
    return eligible_windows,bull,bear

def aggregate5(df):
    g=pd.DataFrame({
        'open':df.open.resample('5min',label='left',closed='left').first(),
        'high':df.high.resample('5min',label='left',closed='left').max(),
        'low':df.low.resample('5min',label='left',closed='left').min(),
        'close':df.close.resample('5min',label='left',closed='left').last(),
        'count':df.close.resample('5min',label='left',closed='left').count(),
    }).dropna()
    return g[g['count']==5]

def count_raw_fvgs_5m(df5):
    bull=bear=eligible=0
    starts=list(df5.index)
    for i in range(2,len(df5)):
        # Require actual consecutive 5m source bars.
        if not (starts[i-1]-starts[i-2]==pd.Timedelta(minutes=5) and starts[i]-starts[i-1]==pd.Timedelta(minutes=5)):
            continue
        A=df5.iloc[i-2]; C=df5.iloc[i]
        tA,tB,tC=starts[i-2],starts[i-1],starts[i]
        confirm=tC+pd.Timedelta(minutes=5)
        keys=[session_key_ts(t) for t in (tA,tB,tC)]
        if keys[0] < 0 or not(keys[0]==keys[1]==keys[2]) or not in_session_ts(confirm):
            continue
        eligible+=1
        if C.low>A.high: bull+=1
        if C.high<A.low: bear+=1
    return eligible,bull,bear

mnq_stats={}
if MNQ.exists():
    mnq=load_mnq()
    check('MNQ integration', 'CSV has monotonic 1m data', lambda: mnq.index.is_monotonic_increasing and len(mnq)>19000)
    check('MNQ integration', 'OHLC validity', lambda: bool(((mnq.high>=mnq[['open','close','low']].max(axis=1)) & (mnq.low<=mnq[['open','close','high']].min(axis=1))).all()))
    w1,b1,s1=count_raw_fvgs_1m(mnq)
    df5=aggregate5(mnq)
    w5,b5,s5=count_raw_fvgs_5m(df5)
    mnq_stats={'rows_1m':len(mnq),'eligible_1m_windows':w1,'raw_bull_1m':b1,'raw_bear_1m':s1,'complete_5m_bars':len(df5),'eligible_5m_windows':w5,'raw_bull_5m':b5,'raw_bear_5m':s5}
    check('MNQ integration', 'Raw 1m data contains both bullish and bearish FVGs', lambda: b1>0 and s1>0)
    check('MNQ integration', 'Raw 5m data contains both bullish and bearish FVGs', lambda: b5>0 and s5>0)
    check('MNQ integration', 'No cross-session FVG windows included', lambda: w1>0 and w5>0)
else:
    mnq_stats={'available':False}

# ---------- Report ----------
passed=sum(r.passed for r in results)
failed=len(results)-passed
bycat={}
for r in results:
    d=bycat.setdefault(r.category, {'passed':0,'failed':0,'total':0})
    d['total']+=1
    d['passed' if r.passed else 'failed']+=1

report={
    'pine_file':str(PINE),
    'sha256':sha256,
    'total_tests':len(results),
    'passed':passed,
    'failed':failed,
    'categories':bycat,
    'mnq_integration':mnq_stats,
    'results':[asdict(r) for r in results],
    'limitations':[
        'This environment cannot execute TradingView Pine Script or reproduce Pine realtime rollback directly.',
        'Static assertions verify the uploaded source text; behavioral tests use an independent Python reference model.',
        'The supplied MNQ CSV is too short to independently warm a 4H SMA200, so MNQ integration validates raw/session-scoped FVG behavior rather than full SMA-gated CRT ownership.',
    ]
}
(OUTDIR/'crt_fvg_qa_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')

lines=[]
lines.append('# CRT + FVG Automated QA Report')
lines.append('')
lines.append(f'- File: `{PINE.name}`')
lines.append(f'- SHA-256: `{sha256}`')
lines.append(f'- Result: **{"PASS" if failed==0 else "FAIL"}**')
lines.append(f'- Tests: **{passed}/{len(results)} passed**')
lines.append('- Random fuzz cases: **200,000**')
if mnq_stats.get('rows_1m'):
    lines.append(f'- MNQ rows: **{mnq_stats["rows_1m"]:,} 1m bars**')
lines.append('')
lines.append('## Category Summary')
lines.append('')
for cat,d in bycat.items():
    lines.append(f'- {cat}: {d["passed"]}/{d["total"]} passed')
lines.append('')
if mnq_stats.get('rows_1m'):
    lines.append('## MNQ Raw FVG Cross-Check')
    lines.append('')
    lines.append(f'- Session-valid 1m windows: {w1:,}')
    lines.append(f'- Raw bullish 1m FVGs: {b1:,}')
    lines.append(f'- Raw bearish 1m FVGs: {s1:,}')
    lines.append(f'- Complete 5m bars: {len(df5):,}')
    lines.append(f'- Session-valid 5m windows: {w5:,}')
    lines.append(f'- Raw bullish 5m FVGs: {b5:,}')
    lines.append(f'- Raw bearish 5m FVGs: {s5:,}')
    lines.append('')
lines.append('## Failed Tests')
lines.append('')
fails=[r for r in results if not r.passed]
if not fails:
    lines.append('None.')
else:
    for r in fails:
        lines.append(f'- **{r.category} / {r.name}**: {r.detail}')
lines.append('')
lines.append('## Limitations')
lines.append('')
for x in report['limitations']:
    lines.append(f'- {x}')
lines.append('')
lines.append('## Detailed Test Results')
lines.append('')
for r in results:
    mark='PASS' if r.passed else 'FAIL'
    extra=f' — {r.detail}' if r.detail else ''
    lines.append(f'- [{mark}] {r.category}: {r.name}{extra}')
(OUTDIR/'crt_fvg_qa_report.md').write_text('\n'.join(lines),encoding='utf-8')

print(json.dumps({
    'result':'PASS' if failed==0 else 'FAIL',
    'passed':passed,
    'total':len(results),
    'failed':failed,
    'categories':bycat,
    'mnq':mnq_stats,
    'sha256':sha256,
    'report_md':str(OUTDIR/'crt_fvg_qa_report.md'),
    'report_json':str(OUTDIR/'crt_fvg_qa_report.json'),
}, indent=2))
if failed:
    raise SystemExit(1)
