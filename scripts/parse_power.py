#!/usr/bin/env python3
"""
Parse Power Profiler ProcessSubsystemPowerImpact XML for iOS devices and apps.

Usage:
    python3 parse_power.py <path_to_xml> [scenario_label]
    python3 parse_power.py /tmp/ios-traces/streaming-power.xml "Audio Streaming Active"

Arguments:
    <path_to_xml>     Path to exported ProcessSubsystemPowerImpact XML.
    [scenario_label]  Optional descriptive label for the run.

Dependencies:
    Python 3.8+ (Zero external pip dependencies; standard library only).
"""

import sys
import os
import re
from collections import defaultdict

COLUMNS = ['start', 'duration', 'process', 'process-name', 'cpu', 'display',
           'instr', 'gpu', 'net', 'wifi_rx', 'wifi_tx', 'cell_rx', 'cell_tx', 'kind']
TOKEN_RE = re.compile(r'<(sentinel|process|pid|device-session|[\w-]+)(?:\s+[^>]*?)?(?:>(?P<val>.*?)</\1>|/>)', re.S)

def parse(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    if os.path.isdir(path) or path.endswith('.trace'):
        raise ValueError(
            f"Expected an exported XML file, but got a .trace bundle: {path}\n"
            f"Please export it first using:\n"
            f"  xcrun xctrace export --input \"{path}\" "
            f"--xpath \"/trace-toc/run[@number='1']/data/table[@schema='ProcessSubsystemPowerImpact']\" > \"{path.replace('.trace', '-power.xml')}\""
        )

    with open(path, encoding='utf-8', errors='replace') as f:
        xml = f.read()

    idmap = {}
    for m in re.finditer(r'<([\w-]+)\s+id="(\d+)"\s+fmt="[^"]*">(.*?)</\1>', xml, re.S):
        idmap[int(m.group(2))] = m.group(3).strip()

    rows = []
    for m in re.finditer(r'<row(?P<attrs>[^>]*)>(?P<body>.*?)</row>', xml, re.S):
        body = m.group('body')
        tokens = []
        for tm in TOKEN_RE.finditer(body):
            name = tm.group(1)
            if name in ('pid', 'device-session'):
                continue
            if name == 'sentinel':
                tokens.append(None)
                continue
            if name == 'process':
                tokens.append(None)
                continue
            val = tm.group('val')
            if val is not None:
                tokens.append(val.strip())
            else:
                rm = re.search(r'ref="(\d+)"', tm.group(0))
                tokens.append(idmap.get(int(rm.group(1))) if rm else None)

        row = {c: None for c in COLUMNS}
        for i, v in enumerate(tokens[:len(COLUMNS)]):
            row[COLUMNS[i]] = v
        rows.append(row)

    return rows

def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def summarize(path, label=None):
    if label is None:
        label = os.path.basename(path)
    rows = parse(path)

    print(f"\n===== [iOS Power Impact Summary] {label} =====")
    print(f"Data Source:       {path}")
    print(f"Total Table Rows:  {len(rows)}")

    kinds = defaultdict(int)
    for r in rows:
        kinds[r.get('kind')] += 1

    def avgmax(key, pred=None):
        vals = [num(r[key]) for r in rows if num(r[key]) is not None and (pred is None or pred(r))]
        if not vals:
            return None, None
        return sum(vals) / len(vals), max(vals)

    cpu_avg, cpu_max = avgmax('cpu', lambda r: r.get('kind') == '0')
    disp_avg, disp_max = avgmax('display', lambda r: r.get('kind') == '0')
    gpu_avg, gpu_max = avgmax('gpu', lambda r: r.get('kind') == '0')
    net_avg, _ = avgmax('net', lambda r: r.get('kind') == '1')
    instr_total = sum(num(r['instr']) or 0 for r in rows if r.get('kind') == '0')
    n_sec = sum(1 for r in rows if r.get('kind') == '0')
    instr_per_s = instr_total / n_sec if n_sec > 0 else 0

    wifi_tx = sum(num(r['wifi_tx']) or 0 for r in rows if r.get('kind') == '1')
    wifi_rx = sum(num(r['wifi_rx']) or 0 for r in rows if r.get('kind') == '1')
    cell_tx = sum(num(r['cell_tx']) or 0 for r in rows if r.get('kind') == '1')
    cell_rx = sum(num(r['cell_rx']) or 0 for r in rows if r.get('kind') == '1')

    print(f"Effective Duration: {n_sec}s (1Hz metric samples)")
    print(f"CPU Impact:        Avg {cpu_avg:.2f}  | Max {cpu_max:.2f}" if cpu_avg is not None else "CPU Impact:        —")
    print(f"Display Impact:    Avg {disp_avg:.2f}  | Max {disp_max:.2f}" if disp_avg is not None else "Display Impact:    —")
    print(f"GPU Impact:        Avg {gpu_avg:.2f}  | Max {gpu_max:.2f}" if gpu_avg is not None else "GPU Impact:        —")
    print(f"Network Impact:    Avg {net_avg:.2f}" if net_avg is not None else "Network Impact:    —")
    print(f"Total CPU Instr:   {instr_total/1e9:.3f} G (Giga-instructions)")
    print(f"Instruction Rate:  {instr_per_s/1e6:.1f} M/s (Mega-instructions/sec)")
    if wifi_tx > 0 or wifi_rx > 0:
        print(f"WiFi Tx / Rx:      {wifi_tx/1024:.1f} KiB / {wifi_rx/1024:.1f} KiB")
    if cell_tx > 0 or cell_rx > 0:
        print(f"Cellular Tx / Rx:  {cell_tx/1024:.1f} KiB / {cell_rx/1024:.1f} KiB")
    print("==============================================\n")
    return rows

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__.strip())
        sys.exit(0 if len(sys.argv) > 1 else 1)

    path = sys.argv[1]
    label = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        summarize(path, label)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
