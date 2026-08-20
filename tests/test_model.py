from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import quant.model as model_mod
from quant.model import ProbabilityModel, label_outcomes, predict_with_champion, train_challenger


def test_label_outcomes_various_branches():
    # entry=100, stop=95 -> r=5, win_r=2 -> target=110, loss_r=-1 -> stop=95
    trades = pd.DataFrame({
        "entry_price": [100.0, 100.0, 100.0, 100.0],
        "stop_price":  [95.0, 95.0, 95.0, 95.0],
        "max_high_in_horizon": [112.0, 105.0, 112.0, 103.0],  # target-only, neither, both, neither
        "min_low_in_horizon":  [98.0, 93.0, 90.0, 97.0],
    })
    labels = label_outcomes(trades, win_r=2.0, loss_r=-1.0)
    # row0: hit target, not stop -> 1 | row1: hit stop only -> 0
    # row2: both hit (ambiguous) -> conservative 0 | row3: neither -> 0
    assert labels.tolist() == [1, 0, 0, 0]


@pytest.fixture(autouse=True)
def isolated_model_dirs(tmp_path, monkeypatch):
    """quant/model.py's save()/load() default `directory` params are bound
    at function-definition time to the real CHAMPION_DIR/CHALLENGERS_DIR, so
    monkeypatching those module attributes alone would NOT redirect calls
    made through the defaults. Tests below pass `directory=` explicitly
    instead. METADATA_DIR IS referenced dynamically inside the function
    bodies, so patching it here is sufficient to keep metadata out of the
    real repo."""
    metadata = tmp_path / "metadata"
    monkeypatch.setattr(model_mod, "METADATA_DIR", metadata)
    return {"champion": tmp_path / "champion", "challengers": tmp_path / "challengers", "metadata": metadata}


def _separable_dataset(n=60, seed=3):
    rng = np.random.default_rng(seed)
    x1 = rng.normal(0, 1, n)
    x2 = rng.normal(0, 1, n)
    y = (x1 + x2 > 0).astype(int)
    X = pd.DataFrame({"f1": x1, "f2": x2})
    return X, pd.Series(y)


def test_probability_model_fit_predict_roundtrip():
    X, y = _separable_dataset()
    X_train, X_test = X.iloc[:45], X.iloc[45:]
    y_train, y_test = y.iloc[:45], y.iloc[45:]

    model = ProbabilityModel(algo="logistic_regression")
    meta = model.fit(
        X_train, y_train, X_test, y_test,
        train_window="2020:2021", validation_window="2022", threshold=0.55, version="v1",
    )

    assert meta.algo == "logistic_regression"
    assert meta.n_train == 45
    assert meta.n_test == len(X_test)
    assert 0.0 <= meta.test_auc <= 1.0

    proba = model.predict_proba(X_test)
    assert proba.shape == (len(X_test),)
    assert ((proba >= 0) & (proba <= 1)).all()


def test_probability_model_rejects_unknown_algo():
    with pytest.raises(ValueError):
        ProbabilityModel(algo="not_a_real_algo")


def test_probability_model_predict_proba_requires_fit_or_load():
    model = ProbabilityModel()
    with pytest.raises(RuntimeError):
        model.predict_proba(pd.DataFrame({"f1": [1.0]}))


def test_probability_model_save_load_roundtrip(isolated_model_dirs):
    X, y = _separable_dataset()
    model = ProbabilityModel(algo="logistic_regression")
    model.fit(X.iloc[:45], y.iloc[:45], X.iloc[45:], y.iloc[45:], "2020", "2021", 0.55, "v1")

    champion_dir = isolated_model_dirs["champion"]
    model.save("champion", directory=champion_dir)

    assert (champion_dir / "champion.joblib").exists()
    assert (isolated_model_dirs["metadata"] / "champion.json").exists()

    loaded = ProbabilityModel.load("champion", directory=champion_dir)
    assert loaded.metadata.version == "v1"
    assert loaded.feature_columns == ["f1", "f2"]

    original_proba = model.predict_proba(X.iloc[45:])
    loaded_proba = loaded.predict_proba(X.iloc[45:])
    np.testing.assert_allclose(original_proba, loaded_proba)


def test_predict_with_champion_returns_none_when_no_champion_trained():
    row = pd.Series({"f1": 0.5, "f2": -0.2})
    result = predict_with_champion(row, name="champion")
    assert result["ml_probability"] is None
    assert "no champion model trained" in result["reason"]


def test_train_challenger_end_to_end(isolated_model_dirs):
    X, y = _separable_dataset(n=60, seed=11)
    df = X.copy()
    df["entry_price"] = 100.0
    df["stop_price"] = 95.0
    df["max_high_in_horizon"] = np.where(y == 1, 112.0, 103.0)
    df["min_low_in_horizon"] = np.where(y == 1, 98.0, 93.0)

    save_dir = isolated_model_dirs["challengers"]
    model = train_challenger(
        df, feature_columns=["f1", "f2"], train_window="2020", validation_window="2021",
        threshold=0.55, version="challenger_v1", test_size=0.2, save_dir=save_dir,
    )
    assert model.metadata.version == "challenger_v1"
    assert (save_dir / "challenger_v1.joblib").exists()
    assert (isolated_model_dirs["metadata"] / "challenger_v1.json").exists()


def test_train_challenger_rejects_too_few_rows():
    df = pd.DataFrame({
        "f1": [0.1] * 5, "entry_price": [100.0] * 5, "stop_price": [95.0] * 5,
        "max_high_in_horizon": [112.0] * 5, "min_low_in_horizon": [98.0] * 5,
    })
    with pytest.raises(ValueError):
        train_challenger(df, feature_columns=["f1"], train_window="x", validation_window="y", threshold=0.5, version="v")
