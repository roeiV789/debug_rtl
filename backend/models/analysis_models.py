from dataclasses import dataclass, field
from typing import Any, Dict, List

from pydantic import BaseModel

from .spec_models import Specification
from .sim_models import SignalDatabase


# ---------------------------------------------------------------------------
# Internal dataclasses
# ---------------------------------------------------------------------------

@dataclass
class FSMTransition:
    from_state: str
    to_state: str
    cycle: int
    valid: bool
    allowed_next: List[str]


@dataclass
class RuleViolation:
    rule_id: str
    rule_name: str
    severity: str
    trigger_cycle: int
    details: str
    relevant_cycles: List[int]
    signals_snapshot: Dict[str, Any]


@dataclass
class AnalysisContext:
    spec: Specification
    signal_db: SignalDatabase
    fsm_transitions: List[FSMTransition]
    rule_violations: List[RuleViolation]

    def to_prompt_context(self) -> str:
        """Serialize everything into a well-structured plain-text block for an LLM prompt."""
        lines: List[str] = []

        # --- Header ---
        lines.append("=== RTL Debug Analysis Context ===")
        lines.append("")

        # --- Interface / Spec Overview ---
        lines.append(f"Interface Type : {self.spec.interface_type}")
        lines.append(f"Version        : {self.spec.version}")
        lines.append(f"Description    : {self.spec.description}")
        lines.append("")

        # --- Protocol Rules ---
        lines.append("--- Protocol Rules ---")
        for rule in self.spec.protocol_rules:
            lines.append(f"  [{rule.id}] {rule.name} (severity={rule.severity})")
            lines.append(f"    Description      : {rule.description}")
            lines.append(f"    Trigger          : {rule.trigger}")
            lines.append(f"    Assert Condition : {rule.assert_condition}")
        lines.append("")

        # --- FSM Definition ---
        fsm = self.spec.fsm_definition
        lines.append("--- FSM Definition ---")
        lines.append(f"  Name          : {fsm.name}")
        lines.append(f"  States        : {', '.join(fsm.states)}")
        lines.append(f"  Initial State : {fsm.initial_state}")
        lines.append("  Valid Transitions:")
        for from_state, allowed in fsm.valid_transitions.items():
            lines.append(f"    {from_state} -> {', '.join(allowed)}")
        lines.append("")

        # --- Rule Violations ---
        lines.append("--- Rule Violations ---")
        if not self.rule_violations:
            lines.append("  (none)")
        else:
            for v in self.rule_violations:
                lines.append(f"  Violation [{v.rule_id}] {v.rule_name}")
                lines.append(f"    Severity       : {v.severity}")
                lines.append(f"    Trigger Cycle  : {v.trigger_cycle}")
                lines.append(f"    Details        : {v.details}")
                lines.append(f"    Relevant Cycles: {v.relevant_cycles}")
                lines.append("    Signal Snapshot:")
                for sig, val in v.signals_snapshot.items():
                    lines.append(f"      {sig} = {val}")
        lines.append("")

        # --- FSM Transitions ---
        lines.append("--- FSM Transitions ---")
        invalid_transitions = [t for t in self.fsm_transitions if not t.valid]
        valid_transitions = [t for t in self.fsm_transitions if t.valid]

        lines.append(f"  Total transitions : {len(self.fsm_transitions)}")
        lines.append(f"  Valid             : {len(valid_transitions)}")
        lines.append(f"  Invalid           : {len(invalid_transitions)}")
        lines.append("")

        if invalid_transitions:
            lines.append("  Invalid FSM Transitions:")
            for t in invalid_transitions:
                lines.append(
                    f"    Cycle {t.cycle}: {t.from_state} -> {t.to_state}"
                    f"  [allowed: {', '.join(t.allowed_next) if t.allowed_next else 'none'}]"
                )
        else:
            lines.append("  No invalid FSM transitions detected.")
        lines.append("")

        if valid_transitions:
            lines.append("  Valid FSM Transitions:")
            for t in valid_transitions:
                lines.append(f"    Cycle {t.cycle}: {t.from_state} -> {t.to_state}")
        lines.append("")

        lines.append("=== End of Analysis Context ===")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pydantic models (API response layer)
# ---------------------------------------------------------------------------

class ViolationOut(BaseModel):
    rule_id: str
    rule_name: str
    severity: str
    trigger_cycle: int
    details: str
    relevant_cycles: List[int]


class FSMIssueOut(BaseModel):
    from_state: str
    to_state: str
    cycle: int
    allowed_next: List[str]


class RecommendationOut(BaseModel):
    title: str
    body: str   # markdown


class AnalysisResult(BaseModel):
    violations: List[ViolationOut]
    fsm_issues: List[FSMIssueOut]
    ai_summary: str                       # markdown
    ai_recommendations: List[RecommendationOut]
