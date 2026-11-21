"""Deterministic, reset-aware quota analytics for irregular observations."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from .model import parse_datetime

MIN_FORECAST_SAMPLES = 6
MIN_VALIDATION_PREDICTIONS = 3
FRESH_FOR_ANALYTICS = timedelta(minutes=15)
MIN_RATE_INTERVAL_HOURS = 5 / 60
MIN_SUMMARY_RATE_INTERVALS = 3
MAX_ROBUST_POINTS = 120
ALLOWED_STATUSES = {"AVAILABLE", "QUOTA_EXHAUSTED", "RATE_LIMITED"}
QUALITY_RANK = {
    "EXACT_OFFICIAL": 4,
    "EXACT_LOCAL": 3,
    "OFFICIAL_UNSTABLE": 3,
    "OBSERVED_INTERNAL": 2,
    "ESTIMATED": 1,
    "UNKNOWN": 0,
}


def analyze_history(records: list[dict[str, Any]], *, now: datetime) -> dict[str, Any]:
    moment = _aware(now)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    malformed = 0
    for raw in records:
        point = _normalize(raw)
        if point is None:
            malformed += 1
            continue
        if point["metric"] != "remaining_percent":
            continue
        grouped[(point["provider"], point["window"])].append(point)
    series = [
        _analyze_series(provider, window, sorted(points, key=lambda item: item["time"]), moment)
        for (provider, window), points in sorted(grouped.items())
    ]
    usable_series = sum(bool(item["provenance"]["usable_count"]) for item in series)
    return {
        "metric": "remaining_percent",
        "series": series,
        "history": {
            "status": "READY",
            "observation_rows": len(records),
            "valid_series": len(series),
            "series_with_usable_points": usable_series,
            "malformed_rows_ignored": malformed,
            "retention_days": 180,
            "storage": "local SQLite",
        },
        "methodology": {
            "irregular_sampling": "rates use actual elapsed hours",
            "reset_handling": "each quota window is segmented at reset timestamp changes or upward jumps",
            "missing_semantics": "UNKNOWN and missing observations are never converted to zero",
            "forecast_gate": f"at least {MIN_FORECAST_SAMPLES} current-cycle samples and walk-forward validation",
            "models": ["M0 recent rate", "M1 time-aware EWMA", "M2 Theil-Sen", "M3 Holt when sampling is near-regular"],
        },
    }


def _normalize(raw: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    sampled = parse_datetime(raw.get("sampled_at"))
    if sampled is None:
        return None
    value = raw.get("value")
    if value is not None:
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = None
        if value is not None and not 0 <= value <= 100:
            value = None
    return {
        "time": sampled,
        "sampled_at": sampled.isoformat(),
        "source_observed_at": _iso(raw.get("source_observed_at")),
        "provider": str(raw.get("provider") or "unknown"),
        "metric": str(raw.get("metric") or "unknown"),
        "window": str(raw.get("window_id") or "unknown"),
        "value": value,
        "quality": str(raw.get("quality") or "UNKNOWN"),
        "source": str(raw.get("source") or "unknown"),
        "reset_at": _iso(raw.get("reset_at")),
        "stale": bool(raw.get("stale")),
        "status": str(raw.get("collector_status") or "UNKNOWN"),
    }


def _analyze_series(
    provider: str, window: str, points: list[dict[str, Any]], now: datetime
) -> dict[str, Any]:
    cycle = 0
    previous_valid: dict[str, Any] | None = None
    resets: list[dict[str, str]] = []
    for point in points:
        point["cycle"] = cycle
        if not _usable(point):
            continue
        reason = None
        if previous_valid is not None:
            old_reset = previous_valid.get("reset_at")
            new_reset = point.get("reset_at")
            if old_reset and new_reset and old_reset != new_reset:
                reason = "reset_timestamp_changed"
            elif point["value"] - previous_valid["value"] >= 5:
                reason = "remaining_increased"
        if reason:
            cycle += 1
            point["cycle"] = cycle
            resets.append({"at": point["sampled_at"], "reason": reason})
        previous_valid = point

    public_points = [
        {
            "t": point["sampled_at"],
            "value": point["value"],
            "quality": point["quality"],
            "stale": point["stale"],
            "status": point["status"],
            "reset_at": point["reset_at"],
            "cycle": point["cycle"],
        }
        for point in points[-360:]
    ]
    usable = [point for point in points if _usable(point)]
    current_cycle = usable[-1]["cycle"] if usable else 0
    current = [point for point in usable if point["cycle"] == current_cycle]
    latest_raw = points[-1] if points else None
    latest_is_current = bool(
        latest_raw
        and _usable(latest_raw)
        and now - latest_raw["time"] <= FRESH_FOR_ANALYTICS
    )
    rates = _interval_rates(current)
    summary = _summary(current, rates, latest_is_current)
    anomaly = _burst(rates)
    forecast = _forecast(current, rates, latest_is_current, now)
    cycles = _cycle_statistics(usable, current_cycle)
    qualities = [QUALITY_RANK.get(point["quality"], 0) for point in current]
    return {
        "provider": provider,
        "window": window,
        "metric": "remaining_percent",
        "points": public_points,
        "resets": resets[-20:],
        "summary": summary,
        "anomaly": anomaly,
        "forecast": forecast,
        "cycles": cycles,
        "provenance": {
            "source": current[-1]["source"] if current else (points[-1]["source"] if points else "unknown"),
            "quality": current[-1]["quality"] if current else "UNKNOWN",
            "observation_count": len(points),
            "usable_count": len(current),
            "time_range": {
                "from": current[0]["sampled_at"] if current else None,
                "to": current[-1]["sampled_at"] if current else None,
            },
            "fresh": latest_is_current,
            "lowest_quality_rank": min(qualities) if qualities else 0,
            "limitations": _limitations(points, current, latest_is_current),
        },
    }


def _usable(point: dict[str, Any]) -> bool:
    return (
        point.get("value") is not None
        and not point.get("stale")
        and QUALITY_RANK.get(str(point.get("quality")), 0) >= 2
        and point.get("status") in ALLOWED_STATUSES
    )


def _interval_rates(points: list[dict[str, Any]]) -> list[dict[str, float]]:
    rates: list[dict[str, float]] = []
    for left, right in zip(points, points[1:]):
        hours = (right["time"] - left["time"]).total_seconds() / 3600
        # Provider percentages are usually integer-rounded.  Extrapolating a
        # one-point change observed seconds apart into pp/hour is numerically
        # correct but operationally misleading, so rates require five minutes.
        if hours < MIN_RATE_INTERVAL_HOURS:
            continue
        rates.append(
            {
                "rate": (left["value"] - right["value"]) / hours,
                "hours": hours,
                "at": right["time"].timestamp(),
            }
        )
    return rates


def _summary(
    points: list[dict[str, Any]], rates: list[dict[str, float]], latest_is_current: bool
) -> dict[str, Any]:
    values = [item["rate"] for item in rates]
    enough_rates = len(values) >= MIN_SUMMARY_RATE_INTERVALS
    robust = (
        -_theil_sen(
            [(point["time"], point["value"]) for point in points[-MAX_ROBUST_POINTS:]]
        )
        if enough_rates and _span_hours(points) >= 0.5
        else None
    )
    return {
        "status": "OK" if latest_is_current else "STALE_OR_MISSING_CURRENT",
        "current_remaining": points[-1]["value"] if points and latest_is_current else None,
        "consumed_since_reset": max(0.0, points[0]["value"] - points[-1]["value"]) if len(points) >= 2 else None,
        "recent_rate_pph": values[-1] if values else None,
        "rolling_median_rate_pph": statistics.median(values[-7:]) if enough_rates else None,
        "ewma_rate_pph": _time_aware_ewma(rates) if enough_rates else None,
        "theil_sen_rate_pph": robust,
        "rate_mad_pph": _mad(values) if len(values) >= 3 else None,
        "rate_iqr_pph": _iqr(values) if len(values) >= 4 else None,
        "sample_count": len(points),
        "interval_count": len(rates),
        "span_hours": _span_hours(points),
    }


def _time_aware_ewma(rates: list[dict[str, float]], half_life_hours: float = 6.0) -> float | None:
    if not rates:
        return None
    estimate = rates[0]["rate"]
    for item in rates[1:]:
        alpha = 1 - math.exp(-math.log(2) * item["hours"] / half_life_hours)
        estimate = alpha * item["rate"] + (1 - alpha) * estimate
    return estimate


def _theil_sen(points: list[tuple[datetime, float]]) -> float:
    slopes: list[float] = []
    origin = points[0][0]
    normalized = [((moment - origin).total_seconds() / 3600, value) for moment, value in points]
    for index, (left_t, left_v) in enumerate(normalized):
        for right_t, right_v in normalized[index + 1 :]:
            if right_t > left_t:
                slopes.append((right_v - left_v) / (right_t - left_t))
    return statistics.median(slopes) if slopes else 0.0


def _burst(rates: list[dict[str, float]]) -> dict[str, Any]:
    if len(rates) < 7:
        return {"status": "INSUFFICIENT_DATA", "detected": False}
    current = rates[-1]["rate"]
    baseline_values = [item["rate"] for item in rates[:-1]][-24:]
    baseline = statistics.median(baseline_values)
    mad = _mad(baseline_values)
    if baseline < 0:
        return {
            "status": "REPLENISHING_BASELINE",
            "detected": False,
            "current_rate_pph": current,
            "baseline_median_pph": baseline,
            "baseline_mad_pph": mad,
            "ratio": None,
            "interval_minutes": rates[-1]["hours"] * 60,
            "method": "rolling median + MAD",
        }
    robust_sigma = 1.4826 * mad
    threshold = max(baseline * 2.5, baseline + 3 * robust_sigma, 0.1)
    ratio = current / baseline if baseline > 0 else None
    return {
        "status": "OK",
        "detected": current > threshold,
        "current_rate_pph": current,
        "baseline_median_pph": baseline,
        "baseline_mad_pph": mad,
        "ratio": ratio,
        "interval_minutes": rates[-1]["hours"] * 60,
        "method": "rolling median + MAD",
    }


def _forecast(
    points: list[dict[str, Any]],
    rates: list[dict[str, float]],
    latest_is_current: bool,
    now: datetime,
) -> dict[str, Any]:
    if not latest_is_current:
        return _no_forecast("STALE_OR_MISSING_CURRENT", len(points))
    if len(points) < MIN_FORECAST_SAMPLES:
        return _no_forecast("INSUFFICIENT_SAMPLES", len(points))
    if _span_hours(points) < 0.25:
        return _no_forecast("INSUFFICIENT_HORIZON", len(points))
    validations = [_walk_forward(name, points) for name in ("M0", "M1", "M2", "M3")]
    eligible = [item for item in validations if item["validation_count"] >= MIN_VALIDATION_PREDICTIONS]
    if not eligible:
        return _no_forecast("VALIDATION_UNAVAILABLE", len(points), validations)
    best = min(eligible, key=lambda item: item["mae"])
    tolerance = best["mae"] * 1.05 + 0.1
    selected = next(item for item in eligible if item["mae"] <= tolerance)
    rate = _fit_rate(selected["model"], points)
    if rate is None or rate <= 0.02:
        return _no_forecast("NO_MEASURABLE_CONSUMPTION", len(points), validations)
    rate_errors = [
        error / horizon
        for error, horizon in zip(selected["absolute_errors"], selected["horizons_hours"])
        if horizon >= MIN_RATE_INTERVAL_HOURS
    ]
    rate_error = _percentile(rate_errors, 0.9) if rate_errors else None
    if rate_error is None or rate_error >= max(rate * 1.5, 0.5):
        return _no_forecast("UNCERTAINTY_TOO_WIDE", len(points), validations)
    relative_error = rate_error / rate if rate > 0 else math.inf
    confidence = "HIGH" if relative_error <= 0.25 and selected["validation_count"] >= 8 else (
        "MEDIUM" if relative_error <= 0.75 else "LOW"
    )
    reset_at = parse_datetime(points[-1].get("reset_at"))
    current = points[-1]["value"]
    targets = {
        str(target): _threshold_eta(current, target, rate, rate_error, now, reset_at)
        for target in (10.0, 0.0)
    }
    horizon_hours = 24.0 if points[-1].get("window") == "5h" else 168.0
    if reset_at is not None:
        horizon_hours = min(horizon_hours, max(0.0, (reset_at - now).total_seconds() / 3600))
    curve = []
    validation_horizon = selected.get("validation_horizon_hours") or 1.0
    value_error = _percentile(selected["absolute_errors"], 0.9) or 0.0
    for step in range(1, 13):
        hours = horizon_hours * step / 12 if horizon_hours > 0 else 0
        estimate = max(0.0, current - rate * hours)
        spread = value_error * math.sqrt(max(hours, 0.01) / max(validation_horizon, 0.01))
        curve.append(
            {
                "t": (now + timedelta(hours=hours)).isoformat(),
                "value": estimate,
                "lower": max(0.0, estimate - spread),
                "upper": min(100.0, estimate + spread),
            }
        )
    return {
        "status": "FORECAST",
        "model": selected["model"],
        "model_label": _model_label(selected["model"]),
        "rate_pph": rate,
        "rate_error_p90_pph": rate_error,
        "confidence": confidence,
        "sample_count": len(points),
        "training_horizon_hours": _span_hours(points),
        "validation_horizon_hours": selected["validation_horizon_hours"],
        "validation_count": selected["validation_count"],
        "mae_pp": selected["mae"],
        "median_absolute_error_pp": selected["median_absolute_error"],
        "targets": targets,
        "curve": curve,
        "candidates": [_public_validation(item) for item in validations],
        "last_fit": now.isoformat(),
        "interval_method": "walk-forward absolute-error P90, horizon-scaled",
    }


def _walk_forward(model: str, points: list[dict[str, Any]]) -> dict[str, Any]:
    minimum = {"M0": 2, "M1": 4, "M2": 5, "M3": 12}[model]
    errors: list[float] = []
    horizons: list[float] = []
    for index in range(minimum, len(points)):
        training = points[:index]
        rate = _fit_rate(model, training)
        if rate is None:
            continue
        hours = (points[index]["time"] - training[-1]["time"]).total_seconds() / 3600
        if hours <= 0:
            continue
        prediction = training[-1]["value"] - rate * hours
        errors.append(abs(prediction - points[index]["value"]))
        horizons.append(hours)
    return {
        "model": model,
        "mae": statistics.fmean(errors) if errors else None,
        "median_absolute_error": statistics.median(errors) if errors else None,
        "validation_count": len(errors),
        "validation_horizon_hours": statistics.median(horizons) if horizons else None,
        "absolute_errors": errors,
        "horizons_hours": horizons,
    }


def _fit_rate(model: str, points: list[dict[str, Any]]) -> float | None:
    rates = _interval_rates(points)
    if model == "M0":
        return rates[-1]["rate"] if rates else None
    if model == "M1":
        return _time_aware_ewma(rates) if len(points) >= 4 else None
    if model == "M2":
        robust_points = points[-MAX_ROBUST_POINTS:]
        return -_theil_sen([(point["time"], point["value"]) for point in robust_points]) if len(robust_points) >= 5 else None
    if model == "M3" and len(points) >= 12 and _near_regular(points):
        return _holt_rate(points)
    return None


def _holt_rate(points: list[dict[str, Any]], alpha: float = 0.45, beta: float = 0.2) -> float | None:
    first_hours = (points[1]["time"] - points[0]["time"]).total_seconds() / 3600
    if first_hours <= 0:
        return None
    level = points[0]["value"]
    trend = (points[1]["value"] - points[0]["value"]) / first_hours
    previous_time = points[0]["time"]
    for point in points[1:]:
        hours = (point["time"] - previous_time).total_seconds() / 3600
        if hours <= 0:
            continue
        prior_level = level
        predicted = level + trend * hours
        level = alpha * point["value"] + (1 - alpha) * predicted
        trend = beta * ((level - prior_level) / hours) + (1 - beta) * trend
        previous_time = point["time"]
    return -trend


def _near_regular(points: list[dict[str, Any]]) -> bool:
    intervals = [
        (right["time"] - left["time"]).total_seconds()
        for left, right in zip(points, points[1:])
        if right["time"] > left["time"]
    ]
    if len(intervals) < 8:
        return False
    mean = statistics.fmean(intervals)
    return bool(mean and statistics.pstdev(intervals) / mean <= 0.25)


def _threshold_eta(
    current: float,
    threshold: float,
    rate: float,
    rate_error: float,
    now: datetime,
    reset_at: datetime | None,
) -> dict[str, Any]:
    if current <= threshold:
        hours = 0.0
    else:
        hours = (current - threshold) / rate
    fastest = rate + rate_error
    slowest = rate - rate_error
    low = max(0.0, (current - threshold) / fastest) if fastest > 0 else None
    high = max(0.0, (current - threshold) / slowest) if slowest > 0 else None
    reset_first = bool(reset_at and now + timedelta(hours=hours) >= reset_at)
    return {
        "threshold": threshold,
        "hours": hours,
        "interval_hours": [low, high],
        "reset_before_threshold": reset_first,
        "reset_at": reset_at.isoformat() if reset_at else None,
    }


def _cycle_statistics(points: list[dict[str, Any]], current_cycle: int) -> dict[str, Any]:
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for point in points:
        groups[point["cycle"]].append(point)
    completed = [group for cycle, group in groups.items() if cycle < current_cycle and len(group) >= 2]
    usages = [max(0.0, group[0]["value"] - group[-1]["value"]) for group in completed]
    durations = [_span_hours(group) for group in completed]
    peak_rates = [
        max((item["rate"] for item in _interval_rates(group)), default=0.0)
        for group in completed
    ]
    return {
        "completed_count": len(completed),
        "median_usage_pp": statistics.median(usages) if usages else None,
        "median_duration_hours": statistics.median(durations) if durations else None,
        "peak_velocity_pph": max(peak_rates) if peak_rates else None,
        "usage_mad_pp": _mad(usages) if len(usages) >= 3 else None,
    }


def _no_forecast(reason: str, sample_count: int, validations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "status": "NO_FORECAST",
        "reason": reason,
        "sample_count": sample_count,
        "candidates": [_public_validation(item) for item in (validations or [])],
    }


def _public_validation(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": value["model"],
        "model_label": _model_label(value["model"]),
        "mae_pp": value.get("mae"),
        "median_absolute_error_pp": value.get("median_absolute_error"),
        "validation_count": value.get("validation_count", 0),
        "validation_horizon_hours": value.get("validation_horizon_hours"),
    }


def _model_label(model: str) -> str:
    return {
        "M0": "M0 最近速率",
        "M1": "M1 时间加权 EWMA",
        "M2": "M2 Theil–Sen 稳健趋势",
        "M3": "M3 Holt 线性趋势",
    }.get(model, model)


def _limitations(
    points: list[dict[str, Any]], current: list[dict[str, Any]], latest_is_current: bool
) -> list[str]:
    values = []
    if not latest_is_current:
        values.append("latest observation is missing, stale, or unavailable")
    if len(current) < MIN_FORECAST_SAMPLES:
        values.append("insufficient current-cycle samples for forecasting")
    if any(point.get("value") is None for point in points):
        values.append("history contains explicit missing observations")
    if any(point.get("stale") for point in points):
        values.append("stale observations are excluded from fitting")
    if len(current) > MAX_ROBUST_POINTS:
        values.append(f"robust regression uses the latest {MAX_ROBUST_POINTS} current-cycle samples")
    return values


def _mad(values: list[float]) -> float:
    if not values:
        return 0.0
    center = statistics.median(values)
    return statistics.median(abs(value - center) for value in values)


def _iqr(values: list[float]) -> float:
    return _percentile(values, 0.75) - _percentile(values, 0.25)


def _percentile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    location = (len(ordered) - 1) * probability
    lower = math.floor(location)
    upper = math.ceil(location)
    if lower == upper:
        return ordered[lower]
    fraction = location - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def _span_hours(points: list[dict[str, Any]]) -> float:
    if len(points) < 2:
        return 0.0
    return (points[-1]["time"] - points[0]["time"]).total_seconds() / 3600


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso(value: Any) -> str | None:
    parsed = parse_datetime(value)
    return parsed.isoformat() if parsed else None
