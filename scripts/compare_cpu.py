#!/usr/bin/env python3
"""
Compare multiple Activity Monitor runs and print a differential table, so A/B
regression checks still work when Power Profiler is unavailable (iOS < 26).

Reuses the same parsing as activity_cpu.py: per-interval CPU load is derived
from the cumulative duration-on-core delta, normalized to ms of CPU per second
of wall time (1000 ms/s ≈ one full core).

Usage:
    python3 compare_cpu.py <xml_path:label> <xml_path:label> ...
    python3 compare_cpu.py /tmp/ios-traces/idle-actmon.xml:"1. Idle" \
                           /tmp/ios-traces/pre-actmon.xml:"2. Pre-Opt" \
                           /tmp/ios-traces/post-actmon.xml:"3. Post-Opt"

Arguments:
    <xml_path:label>  Path to an exported 'activity-monitor-process-live' XML,
                      optionally followed by ':Label'. If ':Label' is omitted,
                      the filename without extension is used. The first XML is
                      the baseline; each later run is diffed against it.
    --process <name>  Optional; only summarize processes whose name contains
                      this substring (e.g. 'VioRelay').

Example:
    python3 compare_cpu.py idle.xml:"Idle" pre.xml:"Pre" post.xml:"Post" --process VioRelay

Dependencies:
    Python 3.8+ (Zero external pip dependencies; standard library only).
"""

import re
import sys
import os

ROW_RE = re.compile(r'<row[^>]*>(.*?)</row>', re.S)
PROC_DEF_RE = re.compile(r'<process\s+id="\d+"\s+fmt="([^"]*)"')
DUR_RE = re.compile(r'<duration\s+id="\d+"\s+fmt="[^"]*">(\d+)</duration>')
CPU_RE = re.compile(r'<duration-on-core\s+id="\d+"\s+fmt="[^"]*">(\d+)</duration-on-core>')
MEM_RE = re.compile(r'<size-in-bytes\s+id="\d+"\s+fmt="[^"]*">(\d+)</size-in-bytes>')


def parse(path):
    """Return list of {name, duration_ms, cpu_ms_s, mem_mb} per sample."""
    with open(path, encoding='utf-8', errors='replace') as f:
        xml = f.read()

    samples = []
    cur_name = None
    cur_mem = 0.0
    cur_cpu = None
    cur_dur = None

    for rm in ROW_RE.finditer(xml):
        body = rm.group(1)
        pm = PROC_DEF_RE.search(body)
        if pm:
            cur_name = pm.group(1)
        dm = DUR_RE.search(body)
        cm = CPU_RE.search(body)
        mm = MEM_RE.search(body)

        dur = int(dm.group(1)) / 1e6 if dm else None
        cpu = int(cm.group(1)) / 1e6 if cm else None
        mem = int(mm.group(1)) / 1e6 if mm else None

        prev_cpu = cur_cpu
        if cpu is not None:
            cur_cpu = cpu
        if dur is not None:
            cur_dur = dur
        if mem is not None:
            cur_mem = mem

        load = None
        if cpu is not None and prev_cpu is not None and cur_dur:
            load = (cpu - prev_cpu) * 1000.0 / cur_dur

        samples.append({
            'name': cur_name,
            'duration_ms': cur_dur or 0,
            'cpu_ms_s': load,
            'mem_mb': cur_mem,
        })
    return samples


def summarize(path, label, filt):
    samples = parse(path)
    by_proc = {}
    for s in samples:
        nm = s['name']
        if nm is None:
            continue
        if filt and filt not in nm:
            continue
        by_proc.setdefault(nm, []).append(s)

    # Pick the process with the highest observed CPU load (usually the target).
    best = None
    for name, rs in by_proc.items():
        loads = [r['cpu_ms_s'] for r in rs if r['cpu_ms_s'] is not None]
        if not loads:
            continue
        if best is None or max(loads) > best['max']:
            best = {'name': name, 'loads': loads,
                    'mem': sum(r['mem_mb'] for r in rs) / len(rs)}
    if best is None:
        return {'label': label, 'path': path, 'present': False}
    avg = sum(best['loads']) / len(best['loads'])
    return {
        'label': label, 'path': path, 'present': True,
        'name': best['name'], 'n': len(best['loads']),
        'avg': avg, 'max': max(best['loads']),
        'mem_mb': best['mem'],
    }


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__.strip())
        sys.exit(0 if len(sys.argv) > 1 else 1)

    filt = None
    if '--process' in sys.argv:
        i = sys.argv.index('--process')
        filt = sys.argv[i + 1]
        del sys.argv[i:i + 2]

    targets = []
    for arg in sys.argv[1:]:
        if not arg.strip():
            continue
        if ':' in arg:
            path, label = arg.split(':', 1)
        else:
            path = arg
            label = os.path.splitext(os.path.basename(path))[0]
        targets.append((path, label))

    results = []
    for path, label in targets:
        try:
            results.append(summarize(path, label, filt))
        except Exception as e:
            print(f"Error parsing '{path}': {e}", file=sys.stderr)
            sys.exit(1)

    print()
    print(f"{'Scenario':<26} {'Process':<30} {'Avg CPU':>9} {'Max CPU':>9} {'Avg Mem':>10}")
    print("=" * 92)
    for r in results:
        if not r['present']:
            print(f"{r['label']:<26} {'(no matching rows)':<30}")
            continue
        print(f"{r['label']:<26} {r['name'][:28]:<30} {r['avg']:>8.0f}ms/s {r['max']:>8.0f}ms/s {r['mem_mb']:>9.1f}MB")

    if len(results) > 1 and all(r['present'] for r in results):
        base = results[0]
        print("-" * 92)
        print(f"Differential vs Baseline [{base['label']}]:")
        for r in results[1:]:
            d_avg = r['avg'] - base['avg']
            d_mem = r['mem_mb'] - base['mem_mb']
            pct = (d_avg / base['avg'] * 100) if base['avg'] else 0
            print(f"  {r['label']:<24} CPU {d_avg:+.0f} ms/s ({pct:+.1f}%)   Mem {d_mem:+.1f} MB")
    print()
    print("CPU is ms of CPU per second of wall time (1000 ms/s ≈ one full core).")
    print()


if __name__ == '__main__':
    main()
