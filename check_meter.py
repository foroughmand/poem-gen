check_meter.py """
Test a Persian line against poetic meters — no language model needed.

Usage:
    python check_meter.py "بسی رنج بردم در این سال سی"
    python check_meter.py "..." motaqareb        # check one named meter
"""
import sys
from ge2pe_g2p import GE2PEG2P
from generate_rerank import MeterFilter, METERS

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    line = sys.argv[1]
    only = sys.argv[2] if len(sys.argv) > 2 else None

    g2p = GE2PEG2P()
    phonemes = g2p.transliterate(line)
    print(f"line     : {line}")
    print(f"phonemes : {phonemes}")

    # Any MeterFilter shares the same analyzer; use one to list scansions.
    probe = MeterFilter(g2p, "")
    scans = probe.scansions(line)
    print(f"scansions: {scans[:8]}{' ...' if len(scans) > 8 else ''}\n")

    meters = {only: METERS[only]} if only else METERS
    for name, target in meters.items():
        ok = MeterFilter(g2p, target).matches(line)
        print(f"  [{'MATCH' if ok else '  -  '}] {name:12} {target}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
