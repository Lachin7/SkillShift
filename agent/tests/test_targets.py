"""Wave 8B step 1: AppTarget registry is plumbing only."""

from __future__ import annotations

from agent.targets import TARGETS, current_target


def test_current_target_defaults_to_store_b(monkeypatch):
    monkeypatch.delenv("SKILLSHIFT_TARGET_APP", raising=False)
    target = current_target()
    assert target.app_id == "store-b"
    assert target.path == "/store-b"
    assert target.adapter_file.endswith("store_b__publish_product.json")


def test_store_c_is_registered_and_separate_from_b():
    assert "store-c" in TARGETS
    assert TARGETS["store-c"].adapter_file != TARGETS["store-b"].adapter_file
    assert TARGETS["store-c"].path == "/store-c"


def test_store_d_is_registered_and_separate():
    assert "store-d" in TARGETS
    assert TARGETS["store-d"].path == "/store-d"
    assert TARGETS["store-d"].adapter_file.endswith("store_d__publish_product.json")


def test_store_e_is_registered_and_separate():
    assert "store-e" in TARGETS
    assert TARGETS["store-e"].path == "/store-e"
    assert TARGETS["store-e"].adapter_file.endswith("store_e__publish_product.json")
