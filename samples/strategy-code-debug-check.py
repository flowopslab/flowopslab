#!/usr/bin/env python3
"""Small public proof for a FlowOps Lab strategy-code debugging sprint.

This sample checks a toy rotation strategy data handoff for common code-level
issues: signal lag, lookahead-prone columns, missing values, and weight sanity.
Boundary: code debugging only, not financial advice, no trading advice, and no profit guarantee.
Public wallet for USDT/USDC on EVM if commissioning a focused sprint: 0x8B9D88f5868B5D576524Abd53a4325F120e9aD2b
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from decimal import Decimal, InvalidOperation
from typing import Any


SAMPLE_CSV = """date,symbol,close,signal,signal_lag,weight
2026-05-27,AAA,101.20,0.32,0.20,0.55
2026-05-27,BBB,88.10,0.18,0.12,0.45
2026-05-28,AAA,102.40,0.28,0.32,0.40
2026-05-28,BBB,87.70,0.22,0.18,0.60
"""

LOOKAHEAD_MARKERS = ("future", "next_", "tomorrow", "forward_return", "target_return")


def decimal_value(value: Any, label: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} is not numeric: {value!r}") from exc
    if number.is_nan():
        raise ValueError(f"{label} is NaN")
    return number


def read_rows(text: str) -> list[dict[str, str]]:
    rows = list(csv.DictReader(io.StringIO(text.strip())))
    if not rows:
        raise ValueError("strategy input has no rows")
    return rows


def check_strategy_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    required = {"date", "symbol", "close", "signal", "signal_lag", "weight"}
    columns = set(rows[0])
    missing_required = sorted(required - columns)
    if missing_required:
        raise ValueError(f"missing required columns: {missing_required}")

    lookahead_columns = sorted(
        column for column in columns if any(marker in column.lower() for marker in LOOKAHEAD_MARKERS)
    )
    missing_cells = [
        {"row": index + 1, "column": column}
        for index, row in enumerate(rows)
        for column in required
        if str(row.get(column, "")).strip() == ""
    ]
    if missing_cells:
        raise ValueError(f"missing required values: {missing_cells[:3]}")

    dates = sorted({row["date"] for row in rows})
    weights_by_date: dict[str, Decimal] = {date: Decimal("0") for date in dates}
    lag_mismatches: list[dict[str, str]] = []
    previous_signal_by_symbol: dict[str, Decimal] = {}
    for row in sorted(rows, key=lambda item: (item["date"], item["symbol"])):
        close = decimal_value(row["close"], "close")
        signal = decimal_value(row["signal"], "signal")
        signal_lag = decimal_value(row["signal_lag"], "signal_lag")
        weight = decimal_value(row["weight"], "weight")
        if close <= 0:
            raise ValueError("close must be positive")
        if weight < 0:
            raise ValueError("weight must be non-negative")
        weights_by_date[row["date"]] += weight
        previous_signal = previous_signal_by_symbol.get(row["symbol"])
        if previous_signal is not None and signal_lag != previous_signal:
            lag_mismatches.append(
                {"date": row["date"], "symbol": row["symbol"], "expected": str(previous_signal), "actual": str(signal_lag)}
            )
        previous_signal_by_symbol[row["symbol"]] = signal

    weight_sums = {date: str(total) for date, total in weights_by_date.items()}
    bad_weight_dates = [date for date, total in weights_by_date.items() if abs(total - Decimal("1")) > Decimal("0.0001")]

    return {
        "rows": len(rows),
        "dates": dates,
        "checks": {
            "required_columns": not missing_required,
            "signal_lag": not lag_mismatches,
            "no_lookahead_columns": not lookahead_columns,
            "weights_sum_to_one": not bad_weight_dates,
        },
        "lookahead_columns": lookahead_columns,
        "lag_mismatches": lag_mismatches,
        "weight_sums": weight_sums,
        "bad_weight_dates": bad_weight_dates,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check a small rotation strategy code/data handoff.")
    parser.add_argument("--self-test", action="store_true", help="Run the bundled sample.")
    parser.add_argument("--csv", help="Optional CSV file with date,symbol,close,signal,signal_lag,weight columns.")
    args = parser.parse_args()

    if args.csv:
        with open(args.csv, "r", encoding="utf-8") as handle:
            text = handle.read()
        source = args.csv
    else:
        text = SAMPLE_CSV
        source = "bundled-rotation-strategy-sample"

    report = check_strategy_rows(read_rows(text))
    report.update({"ok": all(report["checks"].values()), "source": source, "boundary": "code debugging only"})
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
