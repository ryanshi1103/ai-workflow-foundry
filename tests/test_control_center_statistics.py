from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flowfoundry.control_center.analytics import analyze_history
from flowfoundry.control_center.history import HistoryStore


NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)


def row(
    hours: float,
    value: float | None,
    *,
    provider: str = "openai",
    window: str = "5h",
    reset_at: datetime | None = None,
    quality: str = "EXACT_OFFICIAL",
    stale: bool = False,
    status: str = "AVAILABLE",
) -> dict:
    sampled = NOW + timedelta(hours=hours)
    return {
        "sampled_at": sampled.isoformat(),
        "source_observed_at": sampled.isoformat(),
        "provider": provider,
        "metric": "remaining_percent",
        "window_id": window,
        "value": value,
        "quality": quality,
        "source": "fixture.official",
        "reset_at": reset_at.isoformat() if reset_at else None,
        "stale": stale,
        "collector_status": status,
        "schema_version": 1,
    }


def series_for(provider: str, window: str, records: list[dict], *, now: datetime = NOW) -> dict:
    result = analyze_history(records, now=now)
    return next(
        item
        for item in result["series"]
        if item["provider"] == provider and item["window"] == window
    )


class HistoryStoreTests(unittest.TestCase):
    def test_sqlite_history_keeps_missing_semantics_and_required_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.sqlite3"
            store = HistoryStore(path)
            cards = [
                {
                    "provider": "openai",
                    "health": "AVAILABLE",
                    "quality": "EXACT_OFFICIAL",
                    "source": "codex.app-server",
                    "observed_at": NOW.isoformat(),
                    "payload": {"stale": False},
                    "windows": [
                        {"id": "5h", "remaining_percent": 82, "resets_at": (NOW + timedelta(hours=4)).isoformat(), "quality": "EXACT_OFFICIAL"},
                        {"id": "weekly", "remaining_percent": None, "resets_at": None, "quality": "UNKNOWN"},
                    ],
                }
            ]
            inserted = store.record_cards(cards, sampled_at=NOW)
            self.assertEqual(inserted, 2)
            self.assertEqual(store.count(), 2)
            values = {item["window_id"]: item for item in store.read()}
            self.assertEqual(values["5h"]["value"], 82)
            self.assertIsNone(values["weekly"]["value"])
            self.assertEqual(values["weekly"]["quality"], "UNKNOWN")
            self.assertEqual(values["5h"]["collector_status"], "AVAILABLE")
            with closing(sqlite3.connect(path)) as connection:
                columns = {item[1] for item in connection.execute("PRAGMA table_info(observations)")}
            self.assertTrue({"sampled_at", "provider", "metric", "window_id", "value", "quality", "source", "reset_at", "stale", "collector_status"} <= columns)

    def test_history_deduplicates_one_sampling_instant(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = HistoryStore(Path(directory) / "history.sqlite3")
            card = {
                "provider": "openai", "health": "AVAILABLE", "quality": "EXACT_OFFICIAL",
                "source": "fixture", "observed_at": NOW.isoformat(), "payload": {},
                "windows": [{"id": "5h", "remaining_percent": 50, "resets_at": None}],
            }
            store.record_cards([card], sampled_at=NOW)
            store.record_cards([card], sampled_at=NOW)
            self.assertEqual(store.count(), 1)

    def test_history_treats_naive_sampling_time_as_utc(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = HistoryStore(Path(directory) / "history.sqlite3")
            card = {
                "provider": "openai", "health": "AVAILABLE", "quality": "EXACT_OFFICIAL",
                "source": "fixture", "observed_at": NOW.isoformat(), "payload": {},
                "windows": [{"id": "5h", "remaining_percent": 50, "resets_at": None}],
            }
            naive = NOW.replace(tzinfo=None)
            store.record_cards([card], sampled_at=naive)
            self.assertEqual(store.read()[0]["sampled_at"], NOW.isoformat())
            self.assertEqual(len(store.read(since=naive)), 1)


class QuotaAnalyticsTests(unittest.TestCase):
    def test_irregular_linear_series_uses_real_elapsed_time(self) -> None:
        offsets = [-15, -10, -6, -3, -1, 0]
        records = [row(hour, 70 - 2 * (hour + 15)) for hour in offsets]
        result = series_for("openai", "5h", records)
        summary = result["summary"]
        self.assertAlmostEqual(summary["recent_rate_pph"], 2.0, places=6)
        self.assertAlmostEqual(summary["rolling_median_rate_pph"], 2.0, places=6)
        self.assertAlmostEqual(summary["ewma_rate_pph"], 2.0, places=6)
        self.assertAlmostEqual(summary["theil_sen_rate_pph"], 2.0, places=6)
        self.assertEqual(result["forecast"]["status"], "FORECAST")
        self.assertGreaterEqual(result["forecast"]["validation_count"], 3)

    def test_unknown_missing_and_stale_are_not_zero_or_current(self) -> None:
        records = [row(-3, 80), row(-2, None, quality="UNKNOWN"), row(-1, 78), row(0, 77, stale=True)]
        result = series_for("openai", "5h", records)
        self.assertIsNone(result["summary"]["current_remaining"])
        self.assertEqual(result["forecast"]["status"], "NO_FORECAST")
        self.assertEqual(result["forecast"]["reason"], "STALE_OR_MISSING_CURRENT")
        self.assertEqual(result["points"][1]["value"], None)

    def test_reset_boundary_prevents_cross_cycle_fit(self) -> None:
        first_reset = NOW - timedelta(hours=2)
        second_reset = NOW + timedelta(hours=3)
        records = [
            row(-5, 40, reset_at=first_reset),
            row(-4, 30, reset_at=first_reset),
            row(-3, 20, reset_at=first_reset),
            row(-2, 100, reset_at=second_reset),
            row(-1, 96, reset_at=second_reset),
            row(0, 92, reset_at=second_reset),
        ]
        result = series_for("openai", "5h", records)
        self.assertEqual(len(result["resets"]), 1)
        self.assertEqual(result["summary"]["sample_count"], 3)
        self.assertEqual(result["summary"]["consumed_since_reset"], 8)
        self.assertIsNone(result["summary"]["theil_sen_rate_pph"])
        self.assertEqual(result["forecast"]["status"], "NO_FORECAST")

    def test_two_quota_windows_are_analyzed_independently(self) -> None:
        records = []
        for hour, five, weekly in [(-3, 90, 70), (-2, 88, 69), (-1, 86, 68), (0, 84, 67)]:
            records.extend([row(hour, five, window="5h"), row(hour, weekly, window="weekly")])
        result = analyze_history(records, now=NOW)
        self.assertEqual({item["window"] for item in result["series"]}, {"5h", "weekly"})
        five = series_for("openai", "5h", records)
        weekly = series_for("openai", "weekly", records)
        self.assertAlmostEqual(five["summary"]["recent_rate_pph"], 2)
        self.assertAlmostEqual(weekly["summary"]["recent_rate_pph"], 1)

    def test_monotonic_no_consumption_has_no_forecast(self) -> None:
        records = [row(hour, 75) for hour in (-5, -4, -3, -2, -1, 0)]
        result = series_for("openai", "5h", records)
        self.assertEqual(result["summary"]["rolling_median_rate_pph"], 0)
        self.assertEqual(result["forecast"]["status"], "NO_FORECAST")
        self.assertEqual(result["forecast"]["reason"], "NO_MEASURABLE_CONSUMPTION")

    def test_insufficient_samples_return_no_forecast(self) -> None:
        result = series_for("openai", "5h", [row(-1, 80), row(0, 79)])
        self.assertEqual(result["forecast"]["status"], "NO_FORECAST")
        self.assertEqual(result["forecast"]["reason"], "INSUFFICIENT_SAMPLES")

    def test_short_rounded_interval_does_not_create_absurd_hourly_rate(self) -> None:
        records = [row(-1 / 600, 80), row(0, 79)]  # six seconds, one percentage point
        result = series_for("openai", "5h", records)
        self.assertIsNone(result["summary"]["recent_rate_pph"])
        self.assertEqual(result["summary"]["interval_count"], 0)

    def test_smoothed_rate_waits_for_three_real_intervals(self) -> None:
        records = [row(-0.5, 70), row(-0.25, 60), row(0, 50)]
        result = series_for("openai", "5h", records)
        self.assertEqual(result["summary"]["recent_rate_pph"], 40)
        self.assertIsNone(result["summary"]["rolling_median_rate_pph"])
        self.assertIsNone(result["summary"]["ewma_rate_pph"])
        self.assertIsNone(result["summary"]["theil_sen_rate_pph"])

    def test_theil_sen_resists_a_single_outlier(self) -> None:
        values = [100, 98, 96, 55, 92, 90, 88, 86, 84]
        records = [row(index - 8, value) for index, value in enumerate(values)]
        result = series_for("openai", "5h", records)
        self.assertAlmostEqual(result["summary"]["theil_sen_rate_pph"], 2.0, delta=0.25)
        # A majority of identical rates correctly gives robust MAD=0 even
        # though the isolated outlier is very large.
        self.assertEqual(result["summary"]["rate_mad_pph"], 0)

    def test_burst_uses_rolling_median_and_mad(self) -> None:
        values = [100, 99, 98, 97, 96, 95, 94, 88]
        records = [row(index - 7, value) for index, value in enumerate(values)]
        result = series_for("openai", "5h", records)
        self.assertTrue(result["anomaly"]["detected"])
        self.assertEqual(result["anomaly"]["baseline_median_pph"], 1)
        self.assertEqual(result["anomaly"]["ratio"], 6)

    def test_replenishing_baseline_does_not_trigger_burst(self) -> None:
        values = [50, 51, 52, 53, 54, 55, 56, 54]
        records = [row(index - 7, value) for index, value in enumerate(values)]
        result = series_for("openai", "5h", records)
        self.assertFalse(result["anomaly"]["detected"])
        self.assertEqual(result["anomaly"]["status"], "REPLENISHING_BASELINE")

    def test_reset_before_depletion_is_explicit(self) -> None:
        reset = NOW + timedelta(hours=2)
        records = [row(hour, 60 + (-hour), window="weekly", reset_at=reset) for hour in (-8, -6, -4, -3, -2, -1, 0)]
        result = series_for("openai", "weekly", records)
        self.assertEqual(result["forecast"]["status"], "FORECAST")
        self.assertTrue(result["forecast"]["targets"]["10.0"]["reset_before_threshold"])

    def test_depletion_before_reset_is_explicit(self) -> None:
        reset = NOW + timedelta(hours=24)
        records = [row(hour, 28 - 2 * (hour + 6), reset_at=reset) for hour in (-6, -5, -4, -3, -2, -1, 0)]
        result = series_for("openai", "5h", records)
        self.assertEqual(result["forecast"]["status"], "FORECAST")
        self.assertFalse(result["forecast"]["targets"]["10.0"]["reset_before_threshold"])

    def test_walk_forward_selects_simplest_adequate_model(self) -> None:
        records = [row(index - 11, 95 - (index * 1.5)) for index in range(12)]
        result = series_for("openai", "5h", records)
        forecast = result["forecast"]
        self.assertEqual(forecast["status"], "FORECAST")
        self.assertEqual(forecast["model"], "M0")
        self.assertTrue(all("mae_pp" in item for item in forecast["candidates"]))
        self.assertGreaterEqual(forecast["validation_count"], 3)

    def test_unstable_history_exposes_low_confidence_and_wide_interval(self) -> None:
        values = [100, 99, 80, 79, 60, 59, 40, 39]
        records = [row(index - 7, value) for index, value in enumerate(values)]
        result = series_for("openai", "5h", records)
        forecast = result["forecast"]
        self.assertEqual(forecast["status"], "FORECAST")
        self.assertEqual(forecast["confidence"], "LOW")
        low, high = forecast["targets"]["10.0"]["interval_hours"]
        self.assertGreater(high - low, 20)

    def test_malformed_history_is_ignored_and_counted(self) -> None:
        valid = row(0, 90)
        result = analyze_history([{"sampled_at": "bad"}, valid, "not-a-row"], now=NOW)  # type: ignore[list-item]
        self.assertEqual(result["history"]["malformed_rows_ignored"], 2)
        self.assertEqual(len(result["series"]), 1)

    def test_analysis_is_deterministic_and_counts_only_usable_series(self) -> None:
        records = [row(-1, 80), row(0, 79), row(0, None, provider="xai", window="weekly", quality="UNKNOWN")]
        first = analyze_history(records, now=NOW)
        second = analyze_history(records, now=NOW)
        self.assertEqual(first, second)
        self.assertEqual(first["history"]["valid_series"], 2)
        self.assertEqual(first["history"]["series_with_usable_points"], 1)

    def test_provider_quality_downgrade_excludes_observation(self) -> None:
        records = [
            row(-2, 90),
            row(-1, 89, quality="UNKNOWN"),
            row(0, 88, quality="UNKNOWN"),
        ]
        result = series_for("openai", "5h", records)
        self.assertIsNone(result["summary"]["current_remaining"])
        self.assertEqual(result["forecast"]["reason"], "STALE_OR_MISSING_CURRENT")

    def test_completed_reset_cycle_statistics_are_separate(self) -> None:
        reset_one = NOW - timedelta(hours=2)
        reset_two = NOW + timedelta(hours=4)
        records = [
            row(-5, 100, reset_at=reset_one), row(-4, 80, reset_at=reset_one), row(-3, 60, reset_at=reset_one),
            row(-2, 100, reset_at=reset_two), row(-1, 95, reset_at=reset_two), row(0, 90, reset_at=reset_two),
        ]
        result = series_for("openai", "5h", records)
        self.assertEqual(result["cycles"]["completed_count"], 1)
        self.assertEqual(result["cycles"]["median_usage_pp"], 40)


if __name__ == "__main__":
    unittest.main()
