#!/usr/bin/env python3

import argparse
import math
import re
import statistics
from pathlib import Path


def percentile(sorted_values, p):
    if not sorted_values:
        return math.nan

    k = (len(sorted_values) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)

    if f == c:
        return sorted_values[int(k)]

    return (
        sorted_values[f] * (c - k)
        + sorted_values[c] * (k - f)
    )


ap = argparse.ArgumentParser()
ap.add_argument("--log", required=True)
ap.add_argument("--saida-pgbench", required=True)
ap.add_argument("--modelo", required=True)
ap.add_argument("--rodada", type=int, required=True)

args = ap.parse_args()

lat_us = []

with open(args.log, encoding="utf-8") as f:
    for linha in f:
        campos = linha.split()

        if len(campos) < 3:
            continue

        try:
            lat_us.append(float(campos[2]))
        except ValueError:
            continue

if not lat_us:
    raise SystemExit("Nenhuma latencia encontrada.")

lat_ms = sorted(x / 1000.0 for x in lat_us)

texto = Path(args.saida_pgbench).read_text(
    encoding="utf-8",
    errors="replace"
)

m = re.search(
    r"tps = ([0-9.]+) \(without initial connection time\)",
    texto
)

tps = float(m.group(1)) if m else math.nan

print(
    f"{args.modelo},"
    f"{args.rodada},"
    f"{len(lat_ms)},"
    f"{tps:.6f},"
    f"{statistics.mean(lat_ms):.6f},"
    f"{statistics.median(lat_ms):.6f},"
    f"{percentile(lat_ms, 0.95):.6f},"
    f"{min(lat_ms):.6f},"
    f"{max(lat_ms):.6f},"
    f"{statistics.pstdev(lat_ms):.6f}"
)
