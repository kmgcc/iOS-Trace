#!/usr/bin/env python3
"""
Parse an xctrace 'time-profile' XML export (idmap/ref format) into top CPU
functions, thread breakdown, and per-binary attribution.

Works on the exact XML shape emitted by:
    xcrun xctrace export --input <trace> \
      --xpath "/trace-toc/run[@number='1']/data/table[@schema='time-profile']"

Usage:
    python3 top_time.py <time-profile.xml> [topN] [--leaf] [--by-binary]

Arguments:
    <time-profile.xml>  Exported 'time-profile' table XML.
    [topN]              Number of top entries to print (default: 25).
    [--leaf]            Attribute samples to leaf frames only (per-call-site cost).
                        Default is any-frame (inclusive, each sampled frame counts).
    [--by-binary]       Attribute samples by binary name instead of by function.

Example:
    python3 top_time.py /tmp/ios-traces/idle-time-profile.xml 15 --leaf

Dependencies:
    Python 3.8+ (Zero external pip dependencies; standard library only).
"""
import re
import sys
from collections import defaultdict

ROW_RE = re.compile(r'<row>(?P<body>.*?)</row>', re.S)
WEIGHT_DEF_RE = re.compile(r'<weight\s+id="(\d+)"[^>]*>([0-9]+)</weight>')
THREAD_DEF_RE = re.compile(r'<thread\s+id="(\d+)"[^>]*fmt="([^"]*)"')
FRAME_DEF_RE = re.compile(
    r'<frame\s+id="(\d+)"\s+name="([^"]*)"[^>]*>(?:<binary(?:[^>]*name="([^"]*)")?[^>]*/>)?</frame>')
BT_DEF_RE = re.compile(r'<backtrace\s+id="(\d+)">(?P<frames>.*?)</backtrace>', re.S)
TBT_DEF_RE = re.compile(r'<tagged-backtrace\s+id="(\d+)"[^>]*>(?P<body>.*?)</tagged-backtrace>', re.S)


def frame_name_binary(frame_xml):
    """Parse one <frame ...>...</frame> or <frame ref="N"/> into (name, binary, ref)."""
    m = re.search(r'<frame\s+id="(\d+)"\s+name="([^"]*)"[^>]*>(?P<body>.*?)</frame>', frame_xml, re.S)
    if m:
        name = m.group(2)
        binary = '?'
        bm = re.search(r'<binary[^>]*name="([^"]*)"', m.group('body'))
        if bm:
            binary = bm.group(1)
        return name, binary, None
    m = re.search(r'<frame\s+ref="(\d+)"\s*/>', frame_xml)
    if m:
        return None, None, int(m.group(1))
    return None, None, None


def parse(path):
    with open(path, encoding='utf-8', errors='replace') as f:
        xml = f.read()

    weights = {int(i): float(v) / 1e6 for i, v in WEIGHT_DEF_RE.findall(xml)}
    threads = {int(i): fmt for i, fmt in THREAD_DEF_RE.findall(xml)}
    frames = {}   # frame id -> (name, binary)
    for m in FRAME_DEF_RE.finditer(xml):
        frames[int(m.group(1))] = (m.group(2), m.group(3) or '?')
    bts = {}      # backtrace id -> body xml
    for m in BT_DEF_RE.finditer(xml):
        bts[int(m.group(1))] = m.group('frames')
    tbts = {}     # tagged-backtrace id -> body xml
    for m in TBT_DEF_RE.finditer(xml):
        tbts[int(m.group(1))] = m.group('body')

    rows = 0
    total = 0.0
    leaf_counts = defaultdict(float)
    frame_counts = defaultdict(float)
    bin_counts = defaultdict(float)
    thread_counts = defaultdict(float)

    for rm in ROW_RE.finditer(xml):
        body = rm.group('body')
        rows += 1

        w = 1.0
        wm = re.search(r'<weight\s+ref="(\d+)"\s*/>', body)
        if wm:
            w = weights.get(int(wm.group(1)), 1.0)
        else:
            wm = re.search(r'<weight\s+id="\d+"[^>]*>([0-9]+)</weight>', body)
            if wm:
                w = float(wm.group(1)) / 1e6
        total += w

        tm = re.search(r'<thread\s+ref="(\d+)"\s*/>', body)
        tname = None
        if tm:
            tname = threads.get(int(tm.group(1)))
        else:
            tm = re.search(r'<thread\s+id="\d+"[^>]*fmt="([^"]*)"', body)
            if tm:
                tname = tm.group(1)
        if tname:
            thread_counts[tname] += w

        bt = None
        tbm = re.search(r'<tagged-backtrace\s+ref="(\d+)"\s*/>', body)
        if tbm:
            bt = tbts.get(int(tbm.group(1)))
        else:
            tbm = re.search(r'<tagged-backtrace\s+id="\d+"[^>]*>(?P<body>.*?)</tagged-backtrace>', body, re.S)
            if tbm:
                bt = tbm.group('body')
        if not bt:
            continue

        bm2 = re.search(r'<backtrace\s+ref="(\d+)"\s*/>', bt)
        frames_body = None
        if bm2:
            frames_body = bts.get(int(bm2.group(1)))
        else:
            bm2 = re.search(r'<backtrace\s+id="\d+">(?P<frames>.*?)</backtrace>', bt, re.S)
            if bm2:
                frames_body = bm2.group('frames')
        if frames_body is None:
            continue

        stack = []
        for fm in re.finditer(r'<frame\b[^>]*/>', frames_body):
            name, binary, ref = frame_name_binary(fm.group(0))
            if ref is not None:
                f = frames.get(ref)
                if f:
                    stack.append(f)
            else:
                stack.append((name, binary))
        if not stack:
            continue
        leaf = stack[0]
        leaf_counts[leaf[0]] += w
        bin_counts[leaf[1]] += w
        for name, binary in stack:
            frame_counts[name] += w

    return rows, total, leaf_counts, frame_counts, bin_counts, thread_counts


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__.strip())
        sys.exit(0 if len(sys.argv) > 1 else 1)

    path = sys.argv[1]
    topn = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    leaf_only = '--leaf' in sys.argv
    by_binary = '--by-binary' in sys.argv

    rows, total, leaf_counts, frame_counts, bin_counts, thread_counts = parse(path)

    print(f"rows={rows} total_sample_ms={total:.1f} (~{total/1000.0:.2f}s CPU)")
    print("\n== Threads by sample weight ==")
    for name, w in sorted(thread_counts.items(), key=lambda kv: -kv[1])[:8]:
        print(f"{w:10.1f} ms  {name[:95]}")
    if by_binary:
        print("\n== Top binaries (leaf-attributed) ==")
        for name, w in sorted(bin_counts.items(), key=lambda kv: -kv[1])[:topn]:
            print(f"{w:10.1f} ms  {name}")
        return
    counts = leaf_counts if leaf_only else frame_counts
    kind = "LEAF" if leaf_only else "ANY-FRAME"
    print(f"\n== Top {topn} functions ({kind}) ==")
    for name, w in sorted(counts.items(), key=lambda kv: -kv[1])[:topn]:
        pct = 100.0 * w / total if total else 0
        print(f"{w:10.1f} ms  {pct:5.1f}%  {name[:115]}")


if __name__ == '__main__':
    main()
