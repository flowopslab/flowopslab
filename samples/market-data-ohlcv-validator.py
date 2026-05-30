#!/usr/bin/env python3
"""Small public proof for a FlowOps Lab market-data/OHLCV validation sprint.

This sample validates Binance-style OHLCV candles for BTCUSDT and ETHUSDT.
Boundary: data engineering only, not financial advice, no trading advice, and no profit guarantee.
Public wallet for USDT/USDC on EVM if commissioning a focused sprint: 0x8B9D88f5868B5D576524Abd53a4325F120e9aD2b
"""

from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from typing import Any


OFFLINE_KLINES = {
    "BTCUSDT": [
        [1717200000000, "67540.00", "68420.50", "66611.10", "68120.25", "23456.789", 1717286399999],
        [1717286400000, "68120.25", "69980.00", "67888.00", "69444.40", "19876.123", 1717372799999],
        [1717372800000, "69444.40", "70110.75", "69000.00", "69750.10", "17654.456", 1717459199999],
    ],
    "ETHUSDT": [
        [1717200000000, "3760.10", "3824.00", "3695.50", "3798.20", "345678.901", 1717286399999],
        [1717286400000, "3798.20", "3865.35", "3777.00", "3842.80", "312345.678", 1717372799999],
        [1717372800000, "3842.80", "3890.00", "3805.20", "3868.40", "298765.432", 1717459199999],
    ],
}


def as_decimal(value: Any, label: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} is not numeric: {value!r}") from exc
    if number.is_nan():
        raise ValueError(f"{label} is NaN")
    return number


def normalize_candle(row: list[Any]) -> dict[str, Any]:
    if len(row) < 7:
        raise ValueError(f"expected at least 7 Binance kline fields, got {len(row)}")
    open_time = int(row[0])
    close_time = int(row[6])
    open_price = as_decimal(row[1], "open")
    high_price = as_decimal(row[2], "high")
    low_price = as_decimal(row[3], "low")
    close_price = as_decimal(row[4], "close")
    volume = as_decimal(row[5], "volume")
    if close_time <= open_time:
        raise ValueError("close_time must be after open_time")
    if high_price < max(open_price, low_price, close_price):
        raise ValueError("high must be at least open, low, and close")
    if low_price > min(open_price, high_price, close_price):
        raise ValueError("low must be at most open, high, and close")
    if volume < 0:
        raise ValueError("volume must be non-negative")
    return {
        "open_time": open_time,
        "open": str(open_price),
        "high": str(high_price),
        "low": str(low_price),
        "close": str(close_price),
        "volume": str(volume),
        "close_time": close_time,
    }


def validate_candles(symbol: str, rows: list[list[Any]]) -> list[dict[str, Any]]:
    if not rows:
        raise ValueError(f"{symbol} has no candles")
    candles = [normalize_candle(row) for row in rows]
    for previous, current in zip(candles, candles[1:]):
        if current["open_time"] <= previous["open_time"]:
            raise ValueError(f"{symbol} candles are not strictly increasing")
    return candles


def fetch_binance_klines(symbol: str, limit: int) -> list[list[Any]]:
    query = urllib.parse.urlencode({"symbol": symbol, "interval": "1d", "limit": limit})
    url = f"https://api.binance.com/api/v3/klines?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "FlowOpsLabSample/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a small BTC/ETH OHLCV sample.")
    parser.add_argument("--offline", action="store_true", help="Use bundled sample candles instead of live public API data.")
    parser.add_argument("--symbols", default="BTCUSDT,ETHUSDT", help="Comma-separated symbols for live mode.")
    parser.add_argument("--limit", type=int, default=3, help="Number of daily candles per symbol in live mode.")
    args = parser.parse_args()

    symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()]
    source = "offline-sample" if args.offline else "binance-public-api"
    validated: dict[str, list[dict[str, Any]]] = {}
    for symbol in symbols:
        rows = OFFLINE_KLINES[symbol] if args.offline else fetch_binance_klines(symbol, args.limit)
        validated[symbol] = validate_candles(symbol, rows)

    print(json.dumps({"ok": True, "source": source, "symbols": symbols, "candles": validated}, indent=2))


if __name__ == "__main__":
    main()
