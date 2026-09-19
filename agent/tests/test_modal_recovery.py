"""Wave 7E: Modal / local scoring of diagnoser-shaped hypotheses."""

from __future__ import annotations

from agent.modal_recovery import (
    build_snapshot,
    candidate_from_hypothesis,
    hypotheses_from_observation,
    score_diagnoser_hypotheses,
)
from agent.models import AppObservation, ObservationControl, VerificationResult
from modal_app.scoring import (
    HYPOTHESIS_DECOY,
    HYPOTHESIS_SHIPPING,
    SHIPPING_SNAPSHOT,
    pick_winner,
    score_hypothesis,
)


def test_shipping_snapshot_picks_shipping_hypothesis(monkeypatch):
    monkeypatch.setenv("SKILLSHIFT_FORCE_LOCAL_MODAL", "1")
    a = score_hypothesis(SHIPPING_SNAPSHOT, HYPOTHESIS_SHIPPING)
    b = score_hypothesis(SHIPPING_SNAPSHOT, HYPOTHESIS_DECOY)
    assert a["verified_success"] is True
    assert b["verified_success"] is False
    assert pick_winner([a, b]) == "A"

    winner, report = score_diagnoser_hypotheses(
        SHIPPING_SNAPSHOT, [HYPOTHESIS_SHIPPING, HYPOTHESIS_DECOY]
    )
    assert winner == "A"
    assert report["mode"] == "local"


def test_hypotheses_come_from_diagnoser_shaped_dicts(monkeypatch, capsys):
    monkeypatch.setenv("SKILLSHIFT_FORCE_LOCAL_MODAL", "1")
    observation = AppObservation(
        screen="Create Listing",
        url="http://localhost:3010/store-b",
        controls=[
            ObservationControl(ref="store-b-field-shipping", role="select", name="Shipping"),
            ObservationControl(ref="store-b-field-listing-type", role="select", name="Listing type"),
            ObservationControl(ref="store-b-go-live", role="button", name="Go Live", enabled=False),
        ],
        messages=["Select a shipping category to go live."],
    )
    result = VerificationResult(
        passed=False,
        confidence=0.9,
        expected_state="product is published",
        observed_evidence=["Go Live disabled", "shipping blocker visible"],
        failure_class="missing_prerequisite",
    )
    snapshot = build_snapshot(result, observation, ["store-b-go-live"])
    hyps = hypotheses_from_observation(observation, failure_class="missing_prerequisite")
    assert hyps[0]["actions"][0]["target_testid"] == "store-b-field-shipping"
    winner, _report = score_diagnoser_hypotheses(snapshot, hyps)
    assert winner == "A"
    chosen = candidate_from_hypothesis(next(h for h in hyps if h["id"] == winner))
    assert chosen is not None
    assert chosen.target_testid == "store-b-field-shipping"
    out = capsys.readouterr().out
    assert "Modal unavailable" in out or "local" in _report["mode"]


def test_live_path_does_not_use_launch10_decision():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    live = (root / "agent" / "transfer_loop.py").read_text(encoding="utf-8")
    run = (root / "agent" / "run_transfer.py").read_text(encoding="utf-8")
    recovery = (root / "agent" / "recovery.py").read_text(encoding="utf-8")
    assert "LAUNCH10" not in live
    assert "LAUNCH10" not in run
    assert "LAUNCH10" not in recovery
    assert "CAMPAIGN_ACTION" not in live
