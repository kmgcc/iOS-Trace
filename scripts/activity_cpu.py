#!/usr/bin/env python3
"""
Parse an xctrace 'activity-monitor-process-live' XML export into per-process
CPU utilization (ms of CPU per second of wall time) and memory footprint.

Works on the exact XML shape emitted by:
    xcrun xctrace export --input <trace> \
      --xpath "/trace-toc/run[@number='1']/data/table[@schema='activity-monitor-process-live']"

Each row is one process snapshot at one sampling interval (rows are ordered in
time; the first row defines the process name via <process id=.. fmt="Name (pid)">,
later rows reference it):
  <duration>            wall-clock length of this sampling interval (ns)
  <duration-on-core>    CUMULATIVE CPU time consumed by the process (ns) — the
                        per-interval CPU is the delta between consecutive rows.

So per-second CPU load for interval i = (cpu[i] - cpu[i-1]) * 1000 / duration[i],
expressed as ms of CPU per second of wall time (1000 ms/s ≈ one full core).

Usage:
    python3 activity_cpu.py <xml_path> [process_name_filter]

Arguments:
    <xml_path>            Exported 'activity-monitor-process-live' table XML.
    [process_name_filter] Optional substring; only process names containing it
                          are summarized (e.g. 'VioRelay' matches 'VioRelay (5177)';
                          use '.app/VioRelay' to exclude 'VioRelayWidgets').

Example:
    python3 activity_cpu.py /tmp/ios-traces/actmon-pre.xml VioRelay
    # Repeat for pre/post runs and compare the Avg CPU (ms/s) line for A/B deltas.

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
    """Return per-sample dicts for every row (ordered), with resolved process name."""
    with open(path, encoding='utf-8', errors='replace') as f:
        xml = f.read()

    samples = []
    cur_name = None
    cur_mem = 0
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

        # First row of a new process: cpu is cumulative from process start, no delta.
        if cur_cpu is None:
            prev_cpu = cpu
        else:
            prev_cpu = cur_cpu

        if cpu is not None:
            cur_cpu = cpu
        if dur is not None:
            cur_dur = dur
        if mem is not None:
            cur_mem = mem

        # CPU load for this interval = (cpu - prev_cpu) ms of CPU per dur seconds,
        # normalized to ms per second.
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


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__.strip())
        sys.exit(0 if len(sys.argv) > 1 else 1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    if os.path.isdir(path) or path.endswith('.trace'):
        print(
            f"Error: Expected an exported XML file, but got a .trace bundle: {path}\n"
            f"Please export it first using:\n"
            f"  xcrun xctrace export --input \"{path}\" "
            f"--xpath \"/trace-toc/run[@number='1']/data/table[@schema='activity-monitor-process-live']\" > \"{path.replace('.trace', '-actmon.xml')}\"",
            file=sys.stderr,
        )
        sys.exit(1)

    filt = sys.argv[2] if len(sys.argv) > 2 else None
    samples = parse(path)

    # Group consecutive samples by process name.
    by_proc = {}
    for s in samples:
        nm = s['name']
        if nm is None:
            continue
        if filt and filt not in nm:
            continue
        by_proc.setdefault(nm, []).append(s)

    if not by_proc:
        print(f"No rows matched filter {filt!r}.")
        return

    print(f"Activity Monitor CPU summary: {path}")
    if filt:
        print(f"Filter: process name contains {filt!r}")
    print("=" * 88)
    print(f"{'Process':<40} {'Samples':>7} {'Avg CPU':>9} {'Max CPU':>9} {'Avg Mem':>12}")
    print("-" * 88)

    results = []
    for name, rs in sorted(by_proc.items(), key=lambda kv: -max((r['cpu_ms_s'] or 0) for r in kv[1])):
        loads = [r['cpu_ms_s'] for r in rs if r['cpu_ms_s'] is not None]
        if not loads:
            continue
        avg = sum(loads) / len(loads)
        mx = max(loads)
        avg_mem = sum(r['mem_mb'] for r in rs) / len(rs)
        results.append((name, len(loads), avg, mx, avg_mem))

    for name, n, avg, mx, mem in results:
        print(f"{name[:38]:<40} {n:>7} {avg:>8.0f}ms/s {mx:>8.0f}ms/s {mem:>10.1f}MB")

    print("-" * 88)
    print("CPU is ms of CPU per second of wall time (1000 ms/s ≈ one full core).")
    print("Compare Avg values across idle/pre/post runs for A/B deltas.")
    print()


if __name__ == '__main__':
    main()
