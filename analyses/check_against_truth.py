"""Check the fee pilot readout against the effect the generator planted.

The generator records the true sell-through effect of the fee in
data/planted_effects.json, computed from whether each listing would have sold
without the fee. The readout never sees that file. This script checks that every
adjusted estimate's 95% interval contains the true effect, and prints how far
each point estimate landed from it.

Run: python analyses/check_against_truth.py  (after the readout)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
truth = json.loads((ROOT / "data" / "planted_effects.json").read_text())["sell_through_effect"]
findings = json.loads((ROOT / "reports" / "findings.json").read_text())

estimates = {
    "excluding_phoenix_baseball": findings["sell_through_did"]["excluding_phoenix_baseball"],
    **{d: v["sell_through_change_pts"] for d, v in findings["economics_by_day_type"].items()},
}

print(f"{'sell-through effect':28s} {'truth':>7s} {'estimate':>9s} {'95% CI':>17s}")
failed = []
for name, est in estimates.items():
    t = truth[name]
    ok = est["ci_low"] <= t <= est["ci_high"]
    print(f"{name:28s} {t*100:+6.1f}  {est['estimate']*100:+8.1f}  "
          f"[{est['ci_low']*100:+5.1f}, {est['ci_high']*100:+5.1f}]  {'ok' if ok else 'MISS'}")
    if not ok:
        failed.append(name)

if failed:
    sys.exit(f"True effect outside the 95% CI for: {', '.join(failed)}")
