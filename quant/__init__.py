"""Deterministic quant core: universe, features, regime, strategy sleeves,
ensemble, ML probability model, NO-TRADE gate, risk sizing, portfolio
controls, execution and reconciliation. See CLAUDE.md for the layering rule:
Claude/LLM never computes numbers used for sizing or order decisions —
everything in this package does.
"""
