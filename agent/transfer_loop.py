"""Explore → Act → Verify → Recover → Persist loop for Store B.

Skill stays frozen. Adapter starts empty and accumulates discovered mappings.
"""

from __future__ import annotations

from .adapter import (
    INTENT_DETAILS,
    INTENT_PUBLISH,
    INTENT_SHIPPING,
    INTENT_START,
    empty_store_b_adapter,
    mapping_for_intent,
    upsert_mapping,
)
from .executor import (
    BrowserHands,
    MissingTargetError,
    ProductSpec,
    demo_hold,
    demo_pause,
    execute_candidate,
    execute_resolved_targets,
    persist_live_product,
)
from .explorer import explore_step
from .failure_diagnoser import diagnose_failure
from .grounding import (
    elements_from_observation,
    make_step_mapping,
    product_inputs_for_step,
    require_decision_backend,
)
from .models import (
    CandidateAction,
    EnvironmentAdapter,
    Skill,
    SkillStep,
    Verification,
)
from .adapter_curator import apply_patch, mark_mapping_success
from .observer import observe_app
from .recovery import (
    append_lesson,
    build_recovery_patch,
    lesson_from_verification,
    persist,
    propose_recovery,
)
from .verifier import failure_class_to_mismatch, verify_independent, verify_step

MAX_ATTEMPTS_PER_STEP = 10

_LOOP_TRACE: list[dict] = []
_DASHBOARD_HOOK = None


def reset_loop_trace() -> None:
    _LOOP_TRACE.clear()


def current_loop_trace() -> list[dict]:
    return list(_LOOP_TRACE)


def set_dashboard_hook(hook) -> None:
    global _DASHBOARD_HOOK
    _DASHBOARD_HOOK = hook


def record_loop_event(
    *,
    semantic_step: str,
    control: str = "",
    verification: str = "passed",
    failure_class: str = "none",
    patch: str | None = None,
    mapping_count: int = 0,
) -> None:
    _LOOP_TRACE.append(
        {
            "semantic_step": semantic_step,
            "control": control,
            "verification": verification,
            "failure_class": failure_class,
            "patch": patch,
            "adapter_version": mapping_count,
            "mapping_count": mapping_count,
        }
    )


def _emit_live_dashboard(phase: str, adapter: EnvironmentAdapter, message: str) -> None:
    if _DASHBOARD_HOOK is not None:
        _DASHBOARD_HOOK(phase, adapter, message)


def _log(message: str) -> None:
    print(message, flush=True)


def _details_followups(
    step: SkillStep,
    product: ProductSpec,
    elements: list[dict[str, str]],
    already: set[str],
) -> list[CandidateAction]:
    ids = {item.get("testid") for item in elements}
    extras: list[CandidateAction] = []
    if (
        step.intent == INTENT_DETAILS
        and "store-b-field-price" in ids
        and "store-b-field-price" not in already
    ):
        extras.append(
            CandidateAction(
                target_testid="store-b-field-price",
                action="fill",
                value=product.price,
                rationale="complete price for details step",
                confidence=0.95,
            )
        )
    return extras


def _start_targets_for_memory(trail: list[str]) -> list[str]:
    unique = list(dict.fromkeys(trail))
    nav = [
        item
        for item in unique
        if item.endswith(("-nav-inventory", "-nav-catalog", "-nav-listings"))
    ]
    create = [
        item
        for item in unique
        if item.endswith(("-create-listing", "-new-row"))
    ]
    if nav and create:
        return [nav[0], create[0]]
    if create:
        return create
    if nav:
        return nav
    return [
        item
        for item in unique
        if not item.endswith(
            (
                "-go-live",
                "-launch-product",
                "-publish",
                "-product-card",
                "-field-shipping",
                "-field-tax-class",
                "-field-name",
                "-field-price",
                "-field-image",
                "-field-listing-type",
            )
        )
    ] or unique


def _publish_targets_for_memory(trail: list[str]) -> list[str]:
    """Remember the finish control, not decoys or the resulting product card."""
    unique = list(dict.fromkeys(trail))
    finish = [
        item
        for item in unique
        if item.endswith(("-go-live", "-launch-product", "-publish", "-save-row"))
    ]
    if finish:
        return finish[-1:]
    cleaned = [
        item
        for item in unique
        if not item.endswith(
            (
                "-product-card",
                "-field-listing-type",
                "-field-shipping",
                "-field-tax-class",
                "-field-promo",
            )
        )
    ]
    return cleaned or unique[-1:]


def _save_step(
    adapter: EnvironmentAdapter,
    step: SkillStep,
    trail: list[str],
    *,
    confidence: float,
    learned_from: str,
    elements: list[dict[str, str]],
) -> EnvironmentAdapter:
    unique = list(dict.fromkeys(trail))
    if step.intent == INTENT_PUBLISH:
        unique = _publish_targets_for_memory(unique)
    elif step.intent == INTENT_START:
        unique = _start_targets_for_memory(unique)
    mapping = make_step_mapping(
        step.intent,
        unique,
        confidence=confidence,
        learned_from=learned_from,
        elements=elements,
    )
    return upsert_mapping(adapter, mapping)


def _product_live(hands: BrowserHands, product: ProductSpec) -> bool:
    try:
        card = hands.page.locator("[data-testid$='-product-card']").filter(
            has_text=product.name
        )
        return card.count() > 0 and card.first.is_visible()
    except Exception:
        return False


def ground_skill_step(
    hands: BrowserHands,
    step: SkillStep,
    product: ProductSpec,
    adapter: EnvironmentAdapter,
) -> tuple[EnvironmentAdapter, Verification]:
    existing = mapping_for_intent(adapter, step.intent)
    stale_repair = False
    if existing and existing.resolved_targets:
        from .metrics import record_cache_hit

        record_cache_hit()
        _log(f"  cache hit: {step.intent} → {existing.app_action}")
        record_loop_event(
            semantic_step=step.intent,
            control=f"cache {existing.app_action}",
            verification="passed",
            failure_class="none",
            mapping_count=len(adapter.mappings),
        )
        try:
            execute_resolved_targets(hands, existing.resolved_targets, product)
        except MissingTargetError as exc:
            _log(f"  stale mapping: saved testid missing {exc.testid}")
            adapter = adapter.model_copy(deep=True)
            for mapping in adapter.mappings:
                if mapping.semantic_intent == step.intent:
                    mapping.status = "deprecated"
                    mapping.failures += 1
            record_loop_event(
                semantic_step=step.intent,
                control=f"missing {exc.testid}",
                verification="failed",
                failure_class="stale_mapping",
                mapping_count=len(adapter.mappings),
            )
            stale_repair = True
        else:
            if step.intent == INTENT_PUBLISH and _product_live(hands, product):
                adapter = mark_mapping_success(adapter, step.intent, reusable=True)
                if mapping_for_intent(adapter, INTENT_SHIPPING):
                    adapter = mark_mapping_success(adapter, INTENT_SHIPPING, reusable=True)
                return adapter, Verification(
                    step_intent=step.intent,
                    expected_state=step.expected_state,
                    observed_state=f"public product card visible for {product.name}",
                    matched=True,
                    confidence=1.0,
                    mismatch_type="none",
                    failure_class="none",
                )
            verification, _ = verify_independent(hands, step, product_name=product.name)
            if verification.matched:
                return mark_mapping_success(adapter, step.intent, reusable=True), verification
            _log("  cache miss after replay — re-grounding")
            adapter = adapter.model_copy(deep=True)
            adapter.mappings = [
                m for m in adapter.mappings if m.semantic_intent != step.intent
            ]

    backend = require_decision_backend()
    trail: list[str] = []
    failed: set[str] = set()
    values = product_inputs_for_step(step, product)
    learned_from = "exploration"
    last: Verification | None = None

    for attempt in range(1, MAX_ATTEMPTS_PER_STEP + 1):
        observation = observe_app(hands)
        elements = elements_from_observation(observation)
        explored = explore_step(
            step,
            observation=observation,
            screenshot_bytes=hands.screenshot(),
            product_values=values,
            exclude_testids=failed or None,
            backend=backend,
        )
        action = explored.chosen
        _log(
            f"  explore[{attempt}]: {action.action} {action.target_testid} "
            f"({(action.rationale or '')[:60]})"
        )
        execute_candidate(hands, action, product=product)
        trail.append(action.target_testid)

        for extra in _details_followups(
            step, product, elements_from_observation(observe_app(hands)), set(trail)
        ):
            execute_candidate(hands, extra, product=product)
            trail.append(extra.target_testid)

        last, result = verify_independent(hands, step, product_name=product.name)
        if not last.matched:
            diagnosis = diagnose_failure(
                result,
                observe_app(hands),
                failed,
                backend=backend,
                expected_state=step.expected_state,
            )
            last = last.model_copy(
                update={
                    "hypothesis": diagnosis.hypothesis or last.hypothesis,
                    "alternative": diagnosis.alternative or last.alternative,
                    "failure_class": diagnosis.failure_class,
                    "mismatch_type": failure_class_to_mismatch(diagnosis.failure_class),
                }
            )
            _log(
                f"  diagnose: class={diagnosis.failure_class} "
                f"({(diagnosis.hypothesis or '')[:70]})"
            )
        _log(
            f"  verify: matched={last.matched} type={last.mismatch_type} "
            f"class={last.failure_class}"
        )
        record_loop_event(
            semantic_step=step.intent,
            control=f"{action.action} {action.target_testid}",
            verification="passed" if last.matched else "failed",
            failure_class=last.failure_class,
            mapping_count=len(adapter.mappings),
        )
        if not last.matched and last.failure_class == "missing_prerequisite":
            _emit_live_dashboard(
                "mismatch",
                adapter,
                last.hypothesis
                or "Missing environment prerequisite — publish blocked.",
            )

        if last.matched:
            adapter = _save_step(
                adapter,
                step,
                trail,
                confidence=action.confidence,
                learned_from=learned_from,
                elements=hands.visible_elements(),
            )
            if stale_repair:
                adapter = adapter.model_copy(deep=True)
                adapter.adapter_version += 1
                _log(f"  replace_mapping persisted; adapter_version={adapter.adapter_version}")
            return adapter, last

        lesson = lesson_from_verification(last)
        if lesson:
            adapter = append_lesson(adapter, lesson)

        if last.mismatch_type == "missing_prerequisite":
            adapter, last, finish_targets = _recover_prerequisite(
                hands, step, product, adapter, last, failed=failed, backend=backend
            )
            if last.matched:
                adapter = _save_step(
                    adapter,
                    step,
                    finish_targets
                    or [t for t in trail if t.endswith(("-go-live", "-launch-product", "-publish", "-save-row"))]
                    or trail[-1:],
                    confidence=0.9,
                    learned_from="recovery",
                    elements=hands.visible_elements(),
                )
                if stale_repair:
                    adapter = adapter.model_copy(deep=True)
                    adapter.adapter_version += 1
                return adapter, last
            continue

        failed.add(action.target_testid)
        from .metrics import record_recovery

        record_recovery()
        recovery = propose_recovery(
            last,
            elements_from_observation(observe_app(hands)),
            failed_testids=failed,
            screenshot_bytes=hands.screenshot(),
            backend=backend,
        )
        _log(
            f"  recover: {recovery.action} {recovery.target_testid} "
            f"({(recovery.rationale or '')[:60]})"
        )
        execute_candidate(hands, recovery, product=product)
        trail.append(recovery.target_testid)
        learned_from = "recovery"
        nav_obs = observe_app(hands)
        nav_patch = build_recovery_patch(last, recovery, nav_obs)

        for extra in _details_followups(
            step, product, elements_from_observation(observe_app(hands)), set(trail)
        ):
            execute_candidate(hands, extra, product=product)
            trail.append(extra.target_testid)

        last, result = verify_independent(hands, step, product_name=product.name)
        if not last.matched:
            diagnosis = diagnose_failure(
                result,
                observe_app(hands),
                failed,
                backend=backend,
                expected_state=step.expected_state,
            )
            last = last.model_copy(
                update={
                    "hypothesis": diagnosis.hypothesis or last.hypothesis,
                    "alternative": diagnosis.alternative or last.alternative,
                    "failure_class": diagnosis.failure_class,
                    "mismatch_type": failure_class_to_mismatch(diagnosis.failure_class),
                }
            )
        if last.matched:
            try:
                adapter = apply_patch(adapter, nav_patch, last, nav_obs)
            except ValueError:
                pass
            adapter = _save_step(
                adapter,
                step,
                trail,
                confidence=recovery.confidence,
                learned_from="recovery",
                elements=hands.visible_elements(),
            )
            return adapter, last

    assert last is not None
    raise RuntimeError(
        f"Failed to ground step {step.intent!r} after {MAX_ATTEMPTS_PER_STEP} attempts. "
        f"Last: type={last.mismatch_type} observed={last.observed_state!r}"
    )


def _recover_prerequisite(
    hands: BrowserHands,
    step: SkillStep,
    product: ProductSpec,
    adapter: EnvironmentAdapter,
    verification: Verification,
    *,
    failed: set[str],
    backend: str,
) -> tuple[EnvironmentAdapter, Verification, list[str]]:
    from .metrics import record_recovery

    record_recovery()
    _log("  WORKFLOW MISMATCH — missing prerequisite")
    _log(f"  Hypothesis: {verification.hypothesis}")
    observation = observe_app(hands)
    recovery = None
    try:
        from .modal_recovery import (
            build_snapshot,
            candidate_from_hypothesis,
            hypotheses_from_observation,
            score_diagnoser_hypotheses,
        )
        from .verifier import verification_to_result

        scored_hyps = hypotheses_from_observation(
            observation, failure_class=verification.failure_class
        )
        winner_id, report = score_diagnoser_hypotheses(
            build_snapshot(verification_to_result(verification), observation, failed),
            scored_hyps,
        )
        _log(f"  hypothesis score ({report.get('mode')}): winner={winner_id}")
        scored_rows = {item.get("id"): item for item in report.get("candidates") or []}
        scored_ok = bool(
            scored_rows.get(winner_id, {}).get("verified_success")
            or scored_rows.get(winner_id, {}).get("ok")
        )
        winner_hyp = next((item for item in scored_hyps if item.get("id") == winner_id), None)
        if scored_ok and winner_hyp is not None:
            recovery = candidate_from_hypothesis(winner_hyp)
            if recovery is not None:
                from .grounding import validate_candidate

                recovery = validate_candidate(
                    recovery, elements_from_observation(observation)
                )
    except Exception:
        recovery = None
    if recovery is None:
        recovery = propose_recovery(
            verification,
            elements_from_observation(observation),
            failed_testids=failed,
            screenshot_bytes=hands.screenshot(),
            backend=backend,
        )
    _log(f"  recover prereq: {recovery.action} {recovery.target_testid}")
    execute_candidate(hands, recovery, product=product)
    learned_obs = observe_app(hands)
    pending = build_recovery_patch(verification, recovery, learned_obs)
    lesson = lesson_from_verification(verification)
    if lesson:
        adapter = append_lesson(adapter, lesson)

    # Prefer the real publish control once the prerequisite is satisfied —
    # but only when we are grounding the publish skill step.
    from .grounding import FINISH_SUFFIXES, first_suffix

    observation = observe_app(hands)
    elements = elements_from_observation(observation)
    ids = {item.get("testid") for item in elements}
    finish_id = first_suffix(ids, FINISH_SUFFIXES)
    if step.intent == INTENT_PUBLISH and finish_id:
        from .models import CandidateAction

        chosen = CandidateAction(
            target_testid=finish_id,
            action="click",
            rationale="retry publish after prerequisite",
            confidence=0.9,
        )
    else:
        explored = explore_step(
            step,
            observation=observation,
            screenshot_bytes=hands.screenshot(),
            product_values=product_inputs_for_step(step, product),
            exclude_testids=failed | {recovery.target_testid},
            backend=backend,
        )
        chosen = explored.chosen
        # If start step already satisfied after opening create form, don't force clicks.
        mid, _ = verify_independent(hands, step, product_name=product.name)
        if mid.matched and step.intent != INTENT_PUBLISH:
            return adapter, mid, [recovery.target_testid]

    _log(f"  retry step: {chosen.action} {chosen.target_testid}")
    execute_candidate(hands, chosen, product=product)
    demo_pause()
    last, result = verify_independent(hands, step, product_name=product.name)
    if not last.matched:
        diagnosis = diagnose_failure(
            result,
            observe_app(hands),
            failed,
            backend=backend,
            expected_state=step.expected_state,
        )
        last = last.model_copy(
            update={
                "hypothesis": diagnosis.hypothesis or last.hypothesis,
                "alternative": diagnosis.alternative or last.alternative,
                "failure_class": diagnosis.failure_class,
                "mismatch_type": failure_class_to_mismatch(diagnosis.failure_class),
            }
        )
    if last.matched:
        adapter = apply_patch(adapter, pending, last, learned_obs)
        _log(f"  patch applied: {pending.operation} {pending.semantic_intent}")
        record_loop_event(
            semantic_step=step.intent,
            control=f"{recovery.action} {recovery.target_testid}",
            verification="passed",
            failure_class="none",
            patch=pending.operation,
            mapping_count=len(adapter.mappings),
        )
    else:
        _log("  patch held — retry did not verify")
    return adapter, last, (
        [recovery.target_testid, chosen.target_testid]
        if step.intent != INTENT_PUBLISH
        else [chosen.target_testid]
    )


def run_store_b_transfer(
    hands: BrowserHands,
    skill: Skill,
    product: ProductSpec,
    adapter: EnvironmentAdapter | None = None,
    *,
    persist_adapter: bool = True,
) -> tuple[EnvironmentAdapter, str]:
    """Full Skill transfer onto Store B. Adapter may be empty or cached."""
    require_decision_backend()
    state = adapter or empty_store_b_adapter(skill.name)
    hands.goto("/store-b")
    demo_pause()

    for step in skill.steps:
        _log(f"STEP: {step.intent}")
        if step.intent == INTENT_PUBLISH:
            for mapping in state.mappings:
                if not mapping.semantic_intent.startswith("satisfy environment prerequisite"):
                    continue
                if not mapping.resolved_targets:
                    continue
                try:
                    execute_resolved_targets(hands, mapping.resolved_targets, product)
                    demo_pause()
                except MissingTargetError:
                    continue

        state, verification = ground_skill_step(hands, step, product, state)
        if step.intent == INTENT_PUBLISH and not verification.matched:
            if _product_live(hands, product):
                verification = Verification(
                    step_intent=step.intent,
                    expected_state=step.expected_state,
                    observed_state=f"public product card visible for {product.name}",
                    matched=True,
                    confidence=1.0,
                    mismatch_type="none",
                )
        if not verification.matched:
            raise RuntimeError(
                f"Step unfinished: {step.intent} ({verification.mismatch_type})"
            )
        if persist_adapter:
            persist(state)

    card = hands.page.locator("[data-testid$='-product-card']").filter(has_text=product.name)
    if card.count() == 0:
        raise RuntimeError(f"Product card for {product.name!r} not visible after transfer.")
    text = card.inner_text()
    persist_live_product(product)
    if persist_adapter:
        persist(state)
    demo_hold()
    return state, text
