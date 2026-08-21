"""
ML Probability Model (PDF section 6).

Estimates P(reach +2R before -1R within N trading days) as an explicit,
storable, versioned probability — it never issues an order itself, and
nothing downstream is allowed to let it bypass the deterministic gates in
quant/no_trade.py or quant/execution.py.

Guardrails enforced here, per the PDF:
  - time-aware splits only (no shuffling future rows into training)
  - simple interpretable baseline first (logistic regression), gradient
    boosting available once the baseline is beaten out-of-sample
  - every prediction is stamped with model version, training window,
    feature version and threshold so it can be reconstructed later
  - no retrain-on-a-single-loss: retraining is a deliberate, scheduled
    action (see models/challengers/ + quant/model.py train_challenger),
    never triggered inline by a losing trade
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

from quant.config import ROOT
from quant.features import FEATURE_VERSION

MODELS_DIR = ROOT / "models"
CHAMPION_DIR = MODELS_DIR / "champion"
CHALLENGERS_DIR = MODELS_DIR / "challengers"
METADATA_DIR = MODELS_DIR / "metadata"

ALGOS = {
    "logistic_regression": lambda: LogisticRegression(max_iter=1000, class_weight="balanced"),
    "gradient_boosting": lambda: GradientBoostingClassifier(),
}


@dataclass
class ModelMetadata:
    version: str
    algo: str
    feature_version: str
    feature_columns: list[str]
    train_window: str          # e.g. "2018-01-01:2023-12-31"
    validation_window: str
    threshold: float
    test_auc: float
    test_brier: float
    train_positive_rate: float  # fraction of y_train == 1 — the naive "always
                                 # predict this constant" baseline has Brier
                                 # score train_positive_rate * (1 - train_positive_rate);
                                 # a model with test_brier worse than that is
                                 # worse than guessing the base rate.
    n_train: int
    n_test: int
    created_ts: float

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def label_outcomes(
    trades: pd.DataFrame,
    win_r: float = 2.0,
    loss_r: float = -1.0,
    horizon_days: int = 10,
) -> pd.Series:
    """
    trades must have columns: entry_price, stop_price, high, low over the
    following `horizon_days` bars per row (precomputed by the backtest
    harness). Returns 1 if +win_r*R was reached before -loss_r*R within the
    horizon, else 0. This label definition — not the model — is what makes
    the probability meaningful, so keep it in one place.
    """
    r = (trades["entry_price"] - trades["stop_price"]).abs()
    target = trades["entry_price"] + win_r * r
    stop = trades["entry_price"] + loss_r * r  # loss_r is negative
    hit_target = trades["max_high_in_horizon"] >= target
    hit_stop = trades["min_low_in_horizon"] <= stop
    # if both would trigger within the window we don't know intrabar order —
    # conservative default: treat as loss unless target-only triggers.
    label = np.where(hit_target & ~hit_stop, 1, 0)
    return pd.Series(label, index=trades.index, name="label")


class ProbabilityModel:
    def __init__(self, algo: str = "logistic_regression"):
        if algo not in ALGOS:
            raise ValueError(f"unknown algo {algo!r}, choose from {list(ALGOS)}")
        self.algo = algo
        self.model = ALGOS[algo]()
        self.feature_columns: list[str] = []
        self.metadata: ModelMetadata | None = None

    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        train_window: str,
        validation_window: str,
        threshold: float,
        version: str,
    ) -> ModelMetadata:
        self.feature_columns = list(X_train.columns)
        self.model.fit(X_train.values, y_train.values)

        proba_test = self.model.predict_proba(X_test.values)[:, 1]
        auc = roc_auc_score(y_test, proba_test) if y_test.nunique() > 1 else float("nan")
        brier = brier_score_loss(y_test, proba_test)

        self.metadata = ModelMetadata(
            version=version,
            algo=self.algo,
            feature_version=FEATURE_VERSION,
            feature_columns=self.feature_columns,
            train_window=train_window,
            validation_window=validation_window,
            threshold=threshold,
            test_auc=float(auc),
            test_brier=float(brier),
            train_positive_rate=float(y_train.mean()),
            n_train=len(X_train),
            n_test=len(X_test),
            created_ts=time.time(),
        )
        return self.metadata

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if not self.feature_columns:
            raise RuntimeError("model has no feature_columns — fit() or load() it first")
        X_aligned = X[self.feature_columns]
        return self.model.predict_proba(X_aligned.values)[:, 1]

    def save(self, name: str, directory: Path = CHALLENGERS_DIR) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        METADATA_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, directory / f"{name}.joblib")
        (METADATA_DIR / f"{name}.json").write_text(self.metadata.to_json(), encoding="utf-8")
        (directory / f"{name}.features.json").write_text(
            json.dumps(self.feature_columns, indent=2), encoding="utf-8"
        )

    @classmethod
    def load(cls, name: str, directory: Path = CHAMPION_DIR) -> "ProbabilityModel":
        meta = json.loads((METADATA_DIR / f"{name}.json").read_text(encoding="utf-8"))
        inst = cls(algo=meta["algo"])
        inst.model = joblib.load(directory / f"{name}.joblib")
        inst.feature_columns = json.loads((directory / f"{name}.features.json").read_text(encoding="utf-8"))
        inst.metadata = ModelMetadata(**meta)
        return inst


def train_challenger(
    trades_with_horizon: pd.DataFrame,
    feature_columns: list[str],
    train_window: str,
    validation_window: str,
    threshold: float,
    version: str,
    algo: str = "logistic_regression",
    win_r: float = 2.0,
    loss_r: float = -1.0,
    horizon_days: int = 10,
    test_size: float = 0.2,
    save_dir: Path | None = None,
) -> ProbabilityModel:
    """
    End-to-end challenger trainer: labels outcomes, splits, fits, and saves
    to models/challengers/ — the function this module's own docstring
    already promised existed ("see models/challengers/ + quant/model.py
    train_challenger").

    trades_with_horizon must be sorted chronologically and contain
    entry_price, stop_price, max_high_in_horizon, min_low_in_horizon (for
    label_outcomes) plus every column in feature_columns. The train/test
    split is a plain positional split on the LAST test_size fraction of rows
    — time-aware by construction, never a random shuffle (PDF section 6's
    "never randomly shuffle future observations into training").

    Promotion to champion is intentionally NOT part of this function — a
    freshly trained challenger is just a candidate. See
    research/promotion.py's evaluate_promotion()/promote_challenger() for
    the separate, deterministic decision of whether it ever becomes the
    live model.
    """
    labels = label_outcomes(trades_with_horizon, win_r=win_r, loss_r=loss_r, horizon_days=horizon_days)
    X = trades_with_horizon[feature_columns]
    n = len(X)
    if n < 10:
        raise ValueError(f"train_challenger: only {n} rows — need enough history for a meaningful time-aware split")
    split = int(n * (1 - test_size))

    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = labels.iloc[:split], labels.iloc[split:]

    model = ProbabilityModel(algo=algo)
    model.fit(X_train, y_train, X_test, y_test, train_window, validation_window, threshold, version)
    model.save(version, directory=save_dir if save_dir is not None else CHALLENGERS_DIR)
    return model


def predict_with_champion(features_row: pd.Series, name: str = "champion") -> dict[str, Any]:
    """Convenience entry point used by the market-open routine. Returns a
    dict ready to drop into the SETUP QUALITY record (section 5)."""
    if not (METADATA_DIR / f"{name}.json").exists():
        return {
            "ml_probability": None,
            "model_version": None,
            "reason": "no champion model trained yet — treat as insufficient evidence, do not assume 0.5",
        }
    model = ProbabilityModel.load(name)
    proba = float(model.predict_proba(pd.DataFrame([features_row]))[0])
    return {
        "ml_probability": round(proba, 4),
        "model_version": model.metadata.version,
        "threshold": model.metadata.threshold,
        "feature_version": model.metadata.feature_version,
    }
