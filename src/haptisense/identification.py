"""Small, inspectable two-parameter identification with held-out evaluation.

Fits F = k*d + c*max(v, 0) only. Use raw normal force, not clamped command
magnitude. A synthetic self-check verifies the estimator, not tissue validity.
"""
from __future__ import annotations
import math


def fit_kelvin(rows):
    rows = list(rows)
    if len(rows) < 3:
        raise ValueError("at least three contact observations required")
    xx = xy = yy = xf = yf = 0.0
    for row in rows:
        d, v, f = (float(row[k]) for k in ("depth_m", "velocity_m_s", "normal_n"))
        if not all(math.isfinite(x) for x in (d, v, f)) or d <= 0 or f < 0:
            raise ValueError("use finite in-contact observations with positive depth and nonnegative raw normal force")
        v = max(0.0, v)
        xx += d*d; xy += d*v; yy += v*v; xf += d*f; yf += v*f
    determinant = xx*yy - xy*xy
    if xx <= 0 or yy <= 0 or determinant <= 1e-8*xx*yy:
        raise ValueError("unidentifiable design: vary depth and approach velocity independently")
    k = (xf*yy-yf*xy)/determinant
    c = (yf*xx-xf*xy)/determinant
    if k <= 0 or c < -1e-8:
        raise ValueError("unphysical least-squares fit; inspect model mismatch, units or data")
    return {"stiffness_n_m": k, "damping_n_s_m": max(0.0, c),
            "observations": len(rows), "design_separation": determinant/(xx*yy)}


def evaluate_fit(fit, held_out):
    rows = list(held_out)
    if not rows:
        raise ValueError("held-out observations required")
    errors = []
    for r in rows:
        d, v, f = (float(r[k]) for k in ("depth_m", "velocity_m_s", "normal_n"))
        if not all(math.isfinite(x) for x in (d, v, f)) or d <= 0 or f < 0:
            raise ValueError("invalid held-out observation")
        errors.append(fit["stiffness_n_m"]*d + fit["damping_n_s_m"]*max(v, 0)-f)
    return {"observations": len(rows), "rmse_n": math.sqrt(sum(e*e for e in errors)/len(errors)),
            "max_abs_error_n": max(abs(e) for e in errors)}
