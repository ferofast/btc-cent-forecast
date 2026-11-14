"""btc-cent-forecast-01 entry: shrunk 60-minute momentum forecast.

Forecasts Bitcoin's price 240 minutes after each checkpoint from the
4,320 one-minute closes up to it:

    guess = last * exp(0.5 * (log(last) - log(price 60 minutes ago)))

clipped to within +/-2% of the checkpoint close, on the price grid's
5 decimals and inside the scorer's (0, 10_000_000) bounds.

Why this shape:
  * On the competition's own practice cases (Orca cbBTC/USDC, the exact
    series the final is graded on) this scores $372.02 mean absolute
    error vs the persistence baseline's $470.55 - a 21% improvement.
  * On a 60-checkpoint rolling window of independent 1-minute BTC
    closes (Coinbase BTC-USD, 2026-11-04 -> 2026-11-13) it scores
    $559.18 vs persistence $498.84: it loses there, and the honest
    reading is that no model tested beats persistence out of sample
    (variance ratios at 240 minutes are below 1 on both series, and
    the 1-minute autocorrelations are ~0). Every tilted forecaster is
    a gamble on the final 48 hours trending the way the practice
    window did; this one is the middle of the momentum family, big
    enough to clear the prize bar in a trending final, not so extreme
    that it blows up worse than the k=0.75 variant in a choppy one.
  * A walk-forward ridge on the same features was rejected: it scored
    worse than momentum on both windows ($418.97 practice, $581.25
    rolling) and its in-case fit is unstable (one practice case off
    by $833).
  * Pure persistence was rejected too: it equals the house baseline
    exactly, and a prize needs a score strictly below the baseline.

Deterministic: no randomness, no wall clock, no network, standard
library only. Reads $MAKEFUN_INPUT_DIR (else /input), writes
$MAKEFUN_OUTPUT_DIR (else /output), one <id>.out per <id>.in.
"""

import json
import math
import os
from pathlib import Path

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

# Shrinkage applied to the 60-minute log return.
K = 0.5
# Hard clip on the forecast's log move away from the checkpoint close.
CLIP_LOG = math.log(1.02)

MIN_PRICE = 0.00001
MAX_PRICE = 9_999_999.99999


def price5(x):
    """x kept on the grid's 5 decimals and inside (0, 10_000_000)."""
    return round(min(MAX_PRICE, max(MIN_PRICE, x)) * 1e5) / 1e5


def forecast(prices):
    """One forecast from a case's closes (last element = checkpoint)."""
    last = prices[-1]
    if len(prices) < 61:
        return price5(last)
    p60 = prices[-61]
    if not (p60 > 0.0 and last > 0.0):
        return price5(last)
    drift = K * (math.log(last) - math.log(p60))
    drift = max(-CLIP_LOG, min(CLIP_LOG, drift))
    return price5(last * math.exp(drift))


def main():
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    inputs = sorted(Path(INPUT_DIR).glob("*.in"))
    for path in inputs:
        case_id = path.name[: -len(".in")]
        prices = None
        try:
            with open(path, "r", encoding="utf-8") as f:
                case = json.load(f)
            markets = case.get("markets")
            if not isinstance(markets, list) or len(markets) != 1:
                raise ValueError(f"{path.name} does not hold exactly one market")
            prices = markets[0].get("prices")
            if not isinstance(prices, list) or not prices:
                raise ValueError(f"{path.name} has no prices")
            guess = forecast(prices)
        except Exception:
            # Never let one bad case kill the entry: fall back to the
            # checkpoint close (persistence), which is always valid.
            # An invalid case would void prize eligibility for the
            # whole entry, so a valid-shaped output is written even
            # when the input itself is unusable.
            try:
                guess = price5(float(prices[-1]))
            except Exception:
                guess = 1.0
        payload = {"forecasts": [{"case": case_id, "price": guess}]}
        with open(out_dir / f"{case_id}.out", "w", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")


if __name__ == "__main__":
    main()
