"""
Feature calculation — turns raw OHLCV bars into the indicators every
strategy sleeve, the regime engine and the ML model read from.

All indicators are hand-rolled on pandas/numpy (no ta-lib dependency) so the
math is auditable in one place. Every function is pure: DataFrame in,
DataFrame/Series out, no I/O, no side effects — this is what "feature
calculations reproducible" (Phase 1 exit criterion) depends on.

Expected input: a DataFrame indexed by date, columns
['open', 'high', 'low', 'close', 'volume'], ascending by date, one symbol.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FEATURE_VERSION = "1.0.0"


def returns(close: pd.Series, periods: list[int] = (1, 5, 20, 60)) -> pd.DataFrame:
    return pd.DataFrame({f"ret_{p}d": close.pct_change(p) for p in periods})


def sma(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(window).mean()


def ma_structure(close: pd.Series) -> pd.DataFrame:
    sma20, sma50, sma200 = sma(close, 20), sma(close, 50), sma(close, 200)
    return pd.DataFrame({
        "sma_20": sma20,
        "sma_50": sma50,
        "sma_200": sma200,
        "price_above_sma20": (close > sma20).astype(int),
        "price_above_sma50": (close > sma50).astype(int),
        "price_above_sma200": (close > sma200).astype(int),
        "sma20_slope_5d": sma20.pct_change(5),
        "sma50_above_sma200": (sma50 > sma200).astype(int),  # golden/death cross state
    })


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Wilder's ATR."""
    tr = true_range(df)
    return tr.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Wilder's RSI."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    return out.fillna(50)  # neutral when no data / no losses


def adx(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Average Directional Index — trend strength, independent of direction."""
    up_move = df["high"].diff()
    down_move = -df["low"].diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr = true_range(df)
    atr_ = tr.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()

    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(
        alpha=1 / window, min_periods=window, adjust=False).mean() / atr_.replace(0, np.nan)
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(
        alpha=1 / window, min_periods=window, adjust=False).mean() / atr_.replace(0, np.nan)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1 / window, min_periods=window, adjust=False).mean().fillna(0)


def zscore(close: pd.Series, window: int = 20) -> pd.Series:
    mean = close.rolling(window).mean()
    std = close.rolling(window).std()
    return (close - mean) / std.replace(0, np.nan)


def realized_volatility(close: pd.Series, window: int = 20) -> pd.Series:
    return close.pct_change().rolling(window).std() * np.sqrt(252)


def volume_features(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    avg_vol = df["volume"].rolling(window).mean()
    return pd.DataFrame({
        "volume_avg_20": avg_vol,
        "volume_ratio": df["volume"] / avg_vol.replace(0, np.nan),
        "dollar_volume_20": (df["close"] * df["volume"]).rolling(window).mean(),
    })


def breakout_features(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    range_high = df["high"].rolling(window).max()
    range_low = df["low"].rolling(window).min()
    return pd.DataFrame({
        "range_high_20": range_high,
        "range_low_20": range_low,
        "dist_from_high_20_pct": (df["close"] - range_high) / range_high,
        "new_high_break": (df["close"] >= range_high.shift(1)).astype(int),
        "range_width_pct": (range_high - range_low) / range_low.replace(0, np.nan),
    })


def gap_pct(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    return (df["open"] - prev_close) / prev_close.replace(0, np.nan)


def relative_strength(close: pd.Series, benchmark_close: pd.Series, window: int = 20) -> pd.Series:
    """Symbol return minus benchmark return over the same window — simple RS proxy."""
    sym_ret = close.pct_change(window)
    bench_ret = benchmark_close.pct_change(window).reindex(close.index).ffill()
    return sym_ret - bench_ret


def compute_features(df: pd.DataFrame, benchmark_close: pd.Series | None = None) -> pd.DataFrame:
    """Assemble the full feature set for one symbol's OHLCV history."""
    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"compute_features: missing columns {missing}")

    close = df["close"]
    out = pd.concat([
        returns(close),
        ma_structure(close),
        pd.DataFrame({
            "atr_14": atr(df, 14),
            "atr_pct": atr(df, 14) / close,
            "rsi_14": rsi(close, 14),
            "adx_14": adx(df, 14),
            "zscore_20": zscore(close, 20),
            "volatility_20": realized_volatility(close, 20),
            "gap_pct": gap_pct(df),
        }),
        volume_features(df),
        breakout_features(df),
    ], axis=1)

    if benchmark_close is not None:
        out["relative_strength_20"] = relative_strength(close, benchmark_close, 20)
        out["relative_strength_60"] = relative_strength(close, benchmark_close, 60)

    out["feature_version"] = FEATURE_VERSION
    return out
