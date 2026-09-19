"""Wave 7D: action/model counters and naive replay baseline."""

from __future__ import annotations

from agent.executor import BrowserHands, execute_candidate
from agent.metrics import reuse_gain, snapshot, start_run
from agent.models import CandidateAction, RunMetrics
from agent.run_baseline_replay import STORE_A_LABELS, collections_is_not_success


def test_counters_increase_on_execute_candidate():
    class FakeLocator:
        def click(self) -> None:
            return None

        def is_enabled(self) -> bool:
            return True

        def fill(self, text: str) -> None:
            return None

    class FakePage:
        def get_by_test_id(self, testid: str) -> FakeLocator:
            return FakeLocator()

    start_run("Leather Bag")
    before = snapshot().actions
    hands = BrowserHands(FakePage(), "http://localhost:3010")  # type: ignore[arg-type]
    execute_candidate(
        hands,
        CandidateAction(
            target_testid="store-b-nav-inventory",
            action="click",
            rationale="test",
            confidence=0.8,
        ),
    )
    after = snapshot()
    assert after.actions == before + 1
    assert after.product == "Leather Bag"


def test_reuse_gain_keys_from_fake_metrics():
    first = RunMetrics(
        product="Leather Bag",
        actions=12,
        model_calls=9,
        recoveries=2,
        cache_hits=0,
    )
    second = RunMetrics(
        product="Blue Sneaker",
        actions=5,
        model_calls=1,
        recoveries=0,
        cache_hits=4,
    )
    gain = reuse_gain(first, second)
    assert set(gain) == {"actions", "model_calls", "recoveries"}
    assert gain["actions"] == 7
    assert gain["model_calls"] == 8
    assert gain["recoveries"] == 2


def test_baseline_refuses_collections_as_success():
    class FakePage:
        def locator(self, _sel: str):
            class H:
                def first(self):
                    return self

                def inner_text(self) -> str:
                    return "Collections"

            return H()

        def get_by_test_id(self, _tid: str):
            class C:
                def count(self) -> int:
                    return 0

            return C()

    assert "Inventory" not in STORE_A_LABELS
    assert "Go Live" not in STORE_A_LABELS
    assert collections_is_not_success(FakePage()) is True
    import agent.run_baseline_replay as baseline

    assert hasattr(baseline, "main")
