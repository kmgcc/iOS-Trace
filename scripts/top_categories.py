#!/usr/bin/env python3
"""
Analyze memory allocation categories from exported Allocations XML on iOS.

Lists allocation categories ranked by event frequency (allocations/sec), persistent bytes, and transient bytes.
Useful for identifying buffer thrashing, missing object reuse, and memory bloat.

Usage:
    python3 top_categories.py <path_to_xml> <duration_in_seconds> [min_rate]
    python3 top_categories.py /tmp/ios-traces/alloc.xml 60 10.0

Arguments:
    <path_to_xml>          Path to exported Allocations XML (table schema 'all-allocations-summary').
    <duration_in_seconds>  Duration of trace in seconds (used to compute allocation rate).
    [min_rate]             Minimum allocation rate (events/sec) to display (default: 10.0).

Dependencies:
    Python 3.8+ (Zero external pip dependencies; standard library only).
"""

import sys
import os
import xml.etree.ElementTree as ET

def main():
    if len(sys.argv) < 3 or sys.argv[1] in ('-h', '--help'):
        print(__doc__.strip())
        sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help') else 1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    if os.path.isdir(path) or path.endswith('.trace'):
        print(
            f"Error: Expected an exported XML file, but got a .trace bundle: {path}\n"
            f"Please export it first using:\n"
            f"  xcrun xctrace export --input \"{path}\" "
            f"--xpath \"/trace-toc/run[@number='1']/data/table[@schema='all-allocations-summary']\" > \"{path.replace('.trace', '-alloc.xml')}\"",
            file=sys.stderr
        )
        sys.exit(1)

    try:
        seconds = float(sys.argv[2])
    except ValueError:
        print(f"Error: duration must be a valid number: {sys.argv[2]}", file=sys.stderr)
        sys.exit(1)

    min_rate = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0

    rows = {}
    try:
        tree = ET.parse(path)
        for node in tree.iter():
            if node.tag.endswith('row'):
                cat = node.get('category')
                if cat:
                    rows[cat] = node.attrib
    except Exception as e:
        print(f"Error parsing XML: {e}", file=sys.stderr)
        sys.exit(1)

    entries = []
    for cat, attrib in rows.items():
        count = int(attrib.get('count-events', '0') or 0)
        rate = count / seconds if seconds > 0 else 0
        if rate >= min_rate:
            persistent = float(attrib.get('persistent-bytes', '0') or 0)
            transient = float(attrib.get('transient-bytes', '0') or 0)
            entries.append((rate, cat, persistent, transient))

    entries.sort(reverse=True)
    print()
    print(f"Allocations Breakdown: {path}")
    print(f"Filtering: categories with rate >= {min_rate:.1f} events/s across {seconds:.1f}s sample ({len(entries)} matches)")
    print("=" * 86)
    print(f"{'Rate (events/s)':>15}   {'Persistent':>14}   {'Transient':>14}   {'Category Name'}")
    print("-" * 86)
    for rate, cat, p, t in entries:
        print(f"{rate:>14.0f}/s   {p/1e6:>11.2f} MB   {t/1e6:>11.2f} MB   {cat}")
    print()

if __name__ == '__main__':
    main()
