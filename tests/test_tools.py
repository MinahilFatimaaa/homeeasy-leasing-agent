from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

import app


def _active_unit_id() -> int:
    with sqlite3.connect(app.DB_PATH) as conn:
        return conn.execute(
            "SELECT id FROM units WHERE is_active = 1 ORDER BY id LIMIT 1"
        ).fetchone()[0]


def _inactive_unit_id() -> int:
    with sqlite3.connect(app.DB_PATH) as conn:
        return conn.execute(
            "SELECT id FROM units WHERE is_active = 0 ORDER BY id LIMIT 1"
        ).fetchone()[0]


def test_search_only_returns_active_units_and_surfaces_unknown_rents():
    result = app.search_units("Dallas", max_rent=2000, min_beds=2)
    assert result["ok"] is True
    assert result["units"]
    assert all(unit["is_active"] == 1 for unit in result["units"])
    assert all(unit["beds"] >= 2 for unit in result["units"])
    assert any(unit["rent"] is None for unit in result["units"])
    assert all(
        unit["rent"] is None or unit["rent"] <= 2000 for unit in result["units"]
    )


def test_null_rent_renders_required_phrase():
    with sqlite3.connect(app.DB_PATH) as conn:
        unit_id = conn.execute(
            "SELECT id FROM units WHERE rent IS NULL ORDER BY id LIMIT 1"
        ).fetchone()[0]
    assert app._price_from_db(unit_id) == "price not on file / I'll check"


def test_request_tour_rejects_nonexistent_unit():
    future = (datetime.now() + timedelta(days=2)).replace(hour=11, minute=0, second=0)
    result = app.request_tour(999999, future.isoformat(), "Test Renter")
    assert result == {"ok": False, "error": "unit_not_found", "unit_id": 999999}


def test_request_tour_rejects_inactive_unit():
    future = (datetime.now() + timedelta(days=2)).replace(hour=11, minute=0, second=0)
    unit_id = _inactive_unit_id()
    result = app.request_tour(unit_id, future.isoformat(), "Test Renter")
    assert result["ok"] is False
    assert result["error"] == "unit_inactive"


def test_request_tour_rejects_11pm_even_if_user_claimed_exception_elsewhere():
    future = (datetime.now() + timedelta(days=2)).replace(hour=23, minute=0, second=0)
    unit_id = _active_unit_id()
    result = app.request_tour(unit_id, future.isoformat(), "Test Renter")
    assert result["ok"] is False
    assert result["error"] == "outside_touring_hours"


def test_request_tour_accepts_valid_time_and_inserts_row():
    future = (datetime.now() + timedelta(days=2)).replace(hour=11, minute=0, second=0)
    unit_id = _active_unit_id()
    result = app.request_tour(unit_id, future.isoformat(), "Test Renter")
    assert result["ok"] is True
    with sqlite3.connect(app.DB_PATH) as conn:
        row = conn.execute("SELECT * FROM tours WHERE id = ?", (result["tour_id"],)).fetchone()
    assert row is not None


def test_price_guard_replaces_token_from_database():
    result = app.search_units("Dallas", max_rent=2000, min_beds=2)
    known = next(unit for unit in result["units"] if unit["rent"] is not None)
    reply = app._finalize_reply(
        f"Unit {known['id']} is [[PRICE:{known['id']}]].",
        [],
    )
    assert f"${known['rent']:,}/month" in reply


def test_price_guard_blocks_model_written_currency():
    safe = app._finalize_reply("The rent is $9999.", [])
    assert "$9999" not in safe


def test_null_rent_search_result_cannot_be_silently_hidden():
    result = app.search_units("Dallas", max_rent=2000, min_beds=2)
    trace = [{"name": "search_units", "args": {}, "result": result}]
    # A model summary that mentions only a known-price unit omits the NULL-price
    # matches. The finalizer must replace it with a deterministic full result.
    known = next(unit for unit in result["units"] if unit["rent"] is not None)
    raw = f"One option is unit {known['id']} at [[PRICE:{known['id']}]]."
    reply = app._finalize_reply(raw, trace)
    assert "price not on file / I'll check" in reply
