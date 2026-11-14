# btc-cent-forecast-01

Forecast Bitcoin's price 4 hours ahead, from the 4,320 one-minute
closes up to each checkpoint. Entry for the make.fun competition
`btc-cent-forecast-01`.

## The program

`main.py` (Python 3.13, standard library only, offline, deterministic)
writes one guess per case:

```
guess = last * exp(0.5 * (log(last) - log(price 60 minutes ago)))
```

clipped to within +/-2% of the checkpoint close, on the price grid's
5 decimals. A shrunk 60-minute momentum forecast: it follows the last
hour's move halfway, and never strays far from the checkpoint close.

## Validation

- Practice cases (Orca cbBTC/USDC, the series the final is graded
  on): **$372.02 mean absolute error** vs the persistence baseline's
  $470.55 (house 6-case baseline: $445.22).
- 60-checkpoint rolling window of independent 1-minute BTC closes
  (Coinbase BTC-USD, 2026-11-04 to 2026-11-13): $559.18 vs
  persistence $498.84. No model tested beats persistence out of
  sample; this entry is the middle of the momentum family, chosen so
  it clears the prize bar in a trending final without blowing up
  like the k=0.75 variant in a choppy one. A walk-forward ridge was
  tried and rejected (worse on both windows, unstable fit).
- Two runs on the same case write byte-identical output; a case runs
  in ~0.02 s (cap is 8 s).

## Run it

```
MAKEFUN_INPUT_DIR=<cases dir> MAKEFUN_OUTPUT_DIR=<out dir> python3 main.py
```

Reads every `*.in` in the input directory, writes `<id>.out` with
`{"forecasts": [{"case": "<id>", "price": <guess>}]}` for each.
