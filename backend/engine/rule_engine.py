from typing import Any, Dict, List, Optional

from ..models.analysis_models import RuleViolation
from ..models.sim_models import SignalDatabase, SignalFrame
from ..models.spec_models import ProtocolRule, Specification


def _get_rule(spec: Specification, rule_id: str) -> Optional[ProtocolRule]:
    """Look up a ProtocolRule by its id."""
    for rule in spec.protocol_rules:
        if rule.id == rule_id:
            return rule
    return None


def _signal_int(frame: SignalFrame, signal: str, default: int = 0) -> int:
    """Return integer value of a signal in a frame, defaulting to 0 if absent or None."""
    val = frame.signals.get(signal)
    if val is None:
        return default
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _snapshot(frame: SignalFrame) -> Dict[str, Any]:
    """Return a copy of a frame's signal dict."""
    return dict(frame.signals)


# ---------------------------------------------------------------------------
# ERR_RULE_01 — Write Address Handshake Timeout
# ---------------------------------------------------------------------------
# Trigger : awvalid rises (0 -> 1)
# Assertion: awready == 1 within 5 cycles (inclusive window [C, C+5])
# ---------------------------------------------------------------------------

def _check_err_rule_01(
    spec: Specification,
    signal_db: SignalDatabase,
) -> List[RuleViolation]:
    rule = _get_rule(spec, "ERR_RULE_01")
    if rule is None:
        return []

    violations: List[RuleViolation] = []
    frames = signal_db.frames

    for i in range(1, len(frames)):
        prev_frame = frames[i - 1]
        curr_frame = frames[i]

        prev_awvalid = _signal_int(prev_frame, "awvalid")
        curr_awvalid = _signal_int(curr_frame, "awvalid")

        # Detect rising edge: 0 -> 1
        if prev_awvalid == 0 and curr_awvalid == 1:
            trigger_cycle = curr_frame.cycle
            window_end = trigger_cycle + 5

            # Check if awready == 1 anywhere in [trigger_cycle, trigger_cycle + 5]
            window_frames = signal_db.window(trigger_cycle, window_end)
            aw_ready_seen = any(
                _signal_int(f, "awready") == 1 for f in window_frames
            )

            if not aw_ready_seen:
                relevant_cycles = list(range(trigger_cycle, window_end + 1))
                # Snapshot from the trigger cycle
                snapshot = _snapshot(curr_frame)
                violations.append(
                    RuleViolation(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        trigger_cycle=trigger_cycle,
                        details=(
                            f"awvalid rose at cycle {trigger_cycle} but awready did not "
                            f"assert within 5 cycles (checked cycles {trigger_cycle}–{window_end})."
                        ),
                        relevant_cycles=relevant_cycles,
                        signals_snapshot=snapshot,
                    )
                )

    return violations


# ---------------------------------------------------------------------------
# ERR_RULE_02 — Write Response Before Handshake
# ---------------------------------------------------------------------------
# AW handshake: cycle where awvalid==1 AND awready==1
# W  handshake: cycle where wvalid==1  AND wready==1
# For each cycle B where bvalid==1: both AW and W handshakes must have
# occurred at some cycle < B.
# ---------------------------------------------------------------------------

def _check_err_rule_02(
    spec: Specification,
    signal_db: SignalDatabase,
) -> List[RuleViolation]:
    rule = _get_rule(spec, "ERR_RULE_02")
    if rule is None:
        return []

    violations: List[RuleViolation] = []
    frames = signal_db.frames

    # Collect all AW handshake cycles
    aw_handshake_cycles = [
        f.cycle
        for f in frames
        if _signal_int(f, "awvalid") == 1 and _signal_int(f, "awready") == 1
    ]

    # Collect all W handshake cycles
    w_handshake_cycles = [
        f.cycle
        for f in frames
        if _signal_int(f, "wvalid") == 1 and _signal_int(f, "wready") == 1
    ]

    for frame in frames:
        bvalid = _signal_int(frame, "bvalid")
        if bvalid != 1:
            continue

        b_cycle = frame.cycle

        # Check that at least one AW handshake occurred strictly before b_cycle
        aw_before = any(c < b_cycle for c in aw_handshake_cycles)
        # Check that at least one W handshake occurred strictly before b_cycle
        w_before = any(c < b_cycle for c in w_handshake_cycles)

        if not aw_before or not w_before:
            missing_parts: List[str] = []
            if not aw_before:
                missing_parts.append("AW handshake (awvalid & awready)")
            if not w_before:
                missing_parts.append("W handshake (wvalid & wready)")

            missing_str = " and ".join(missing_parts)
            relevant_cycles = sorted(
                set(aw_handshake_cycles + w_handshake_cycles + [b_cycle])
            )

            violations.append(
                RuleViolation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    trigger_cycle=b_cycle,
                    details=(
                        f"bvalid asserted at cycle {b_cycle} before {missing_str} "
                        f"completed. Transaction initiation incomplete."
                    ),
                    relevant_cycles=relevant_cycles,
                    signals_snapshot=_snapshot(frame),
                )
            )

    return violations


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_rule_engine(
    spec: Specification,
    signal_db: SignalDatabase,
) -> List[RuleViolation]:
    """Run all hard-coded rule checks against the signal database.

    Returns a combined list of RuleViolation objects for every detected
    protocol violation.
    """
    violations: List[RuleViolation] = []
    violations.extend(_check_err_rule_01(spec, signal_db))
    violations.extend(_check_err_rule_02(spec, signal_db))
    return violations
