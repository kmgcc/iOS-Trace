#!/usr/bin/env python3
"""
Compare per-scenario Power Profiler runs for iOS applications and devices.

Usage:
    python3 compare_elements.py <xml_path:label> <xml_path:label> ...
    python3 compare_elements.py /tmp/ios-traces/idle.xml:"1. Idle Baseline" /tmp/ios-traces/streaming.xml:"2. Active Streaming"

Arguments:
    <xml_path:label>  Path to exported ProcessSubsystemPowerImpact XML, optionally followed by ':Label'.
                      If ':Label' is omitted, the filename without extension will be used.
                      The first XML provided is treated as the Baseline for differential (delta) calculations.

Dependencies:
    Python 3.8+ (Zero external pip dependencies; standard library only).
"""

import sys
import os
import re

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
    for m in re.finditer(r'<row[^>]*>(.*?)</row>', xml, re.S):
        body = m.group(1)
        tokens = []
        for tm in TOKEN_RE.finditer(body):
            name = tm.group(1)
            if name in ('pid', 'device-session'):
                continue
            if name in ('sentinel', 'process'):
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

def summarize(path, label):
    rows = parse(path)
    # kind '0' = regular per-second samples (cpu, display, instr, gpu)
    reg = [r for r in rows if r.get('kind') == '0']
    # kind '1' = networking samples (wifi, cellular)
    net = [r for r in rows if r.get('kind') == '1']

    n_sec = len(reg)
    cpu_vals = [num(r['cpu']) for r in reg if num(r['cpu']) is not None]
    disp_vals = [num(r['display']) for r in reg if num(r['display']) is not None]
    gpu_vals = [num(r['gpu']) for r in reg if num(r['gpu']) is not None]
    instr = sum(num(r['instr']) or 0 for r in reg)

    wifi_tx = sum(num(r['wifi_tx']) or 0 for r in net)
    wifi_rx = sum(num(r['wifi_rx']) or 0 for r in net)

    def avg(vals):
        return sum(vals)/len(vals) if vals else None

    return {
        'label': label,
        'path': path,
        'n_sec': n_sec,
        'cpu_avg': avg(cpu_vals),
        'cpu_max': max(cpu_vals) if cpu_vals else None,
        'disp_avg': avg(disp_vals),
        'gpu_avg': avg(gpu_vals),
        'instr_total': instr,
        'instr_per_s': instr / n_sec if n_sec > 0 else 0,
        'wifi_tx_kib': wifi_tx / 1024,
        'wifi_rx_kib': wifi_rx / 1024,
    }

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__.strip())
        sys.exit(0 if len(sys.argv) > 1 else 1)

    targets = []
    for arg in sys.argv[1:]:
        if ':' in arg:
            path, label = arg.split(':', 1)
        else:
            path = arg
            label = os.path.splitext(os.path.basename(path))[0]
        targets.append((path, label))

    results = []
    for path, label in targets:
        try:
            results.append(summarize(path, label))
        except Exception as e:
            print(f"Error parsing '{path}': {e}", file=sys.stderr)
            sys.exit(1)

    has_net = any(r['wifi_tx_kib'] > 0 or r['wifi_rx_kib'] > 0 for r in results)

    print()
    if has_net:
        print(f"{'Scenario':<24} {'Sec':>4} {'CPU Avg':>8} {'CPU Max':>8} {'Display':>8} {'GPU Avg':>8} {'Total Instr':>12} {'Instr M/s':>10} {'WiFi Tx/Rx':>12}")
        print("=" * 105)
    else:
        print(f"{'Scenario':<26} {'Sec':>4} {'CPU Avg':>8} {'CPU Max':>8} {'Display':>8} {'GPU Avg':>8} {'Total Instr':>12} {'Instr M/s':>10}")
        print("=" * 92)

    for r in results:
        disp_str = f"{r['disp_avg']:>8.2f}" if r['disp_avg'] is not None else f"{'—':>8}"
        gpu_str = f"{r['gpu_avg']:>8.2f}" if r['gpu_avg'] is not None else f"{'—':>8}"
        cpu_avg_str = f"{r['cpu_avg']:>8.2f}" if r['cpu_avg'] is not None else f"{'—':>8}"
        cpu_max_str = f"{r['cpu_max']:>8.1f}" if r['cpu_max'] is not None else f"{'—':>8}"
        instr_g_str = f"{r['instr_total']/1e9:>11.2f}G"
        instr_m_str = f"{r['instr_per_s']/1e6:>10.1f}"

        if has_net:
            wifi_str = f"{r['wifi_tx_kib']/1024:.1f}/{r['wifi_rx_kib']/1024:.1f}MB"
            print(f"{r['label']:<24} {r['n_sec']:>4} {cpu_avg_str} {cpu_max_str} "
                  f"{disp_str} {gpu_str} {instr_g_str} {instr_m_str} {wifi_str:>12}")
        else:
            print(f"{r['label']:<26} {r['n_sec']:>4} {cpu_avg_str} {cpu_max_str} "
                  f"{disp_str} {gpu_str} {instr_g_str} {instr_m_str}")

    if len(results) > 1:
        base = results[0]['instr_per_s']
        base_label = results[0]['label']
        divider_len = 105 if has_net else 92
        print("-" * divider_len)
        print(f"Differential vs Baseline [{base_label}]:")
        for r in results[1:]:
            d_instr = (r['instr_per_s'] - base) / 1e6
            d_cpu = (r['cpu_avg'] - results[0]['cpu_avg']) if (r['cpu_avg'] is not None and results[0]['cpu_avg'] is not None) else None
            cpu_diff_str = f", CPU Avg Delta {d_cpu:+.2f}" if d_cpu is not None else ""
            net_delta_str = ""
            if has_net:
                d_tx = r['wifi_tx_kib'] - results[0]['wifi_tx_kib']
                net_delta_str = f", WiFi Tx Delta {d_tx/1024:+.2f}MB"
            print(f"  {r['label']:<24} {d_instr:>+8.1f} M/s instructions{cpu_diff_str}{net_delta_str}")
    print()

if __name__ == '__main__':
    main()
