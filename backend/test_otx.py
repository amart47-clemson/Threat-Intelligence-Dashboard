"""Run OTX feed pull in isolation. Run from backend/: python test_otx.py"""
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from config import Config
from feeds.otx import fetch_otx_pulses, parse_pulses

if not Config.OTX_API_KEY:
    print("ERROR: Set OTX_API_KEY in .env before running this test.")
    sys.exit(1)

pulses = fetch_otx_pulses()
aggregated = parse_pulses(pulses)

print(f"\n--- OTX Feed Summary ---")
print(f"Pulses fetched: {len(pulses)}")
print(f"Unique indicators: {len(aggregated)}")

for i, (value, data) in enumerate(list(aggregated.items())[:10]):
    print(
        f"  [{i+1}] {value} | type={data['ioc_type'].value} "
        f"| pulses={data['pulse_count']} | tags={list(data['tags'])[:3]}"
    )

if len(aggregated) > 10:
    print(f"  ... and {len(aggregated) - 10} more")
