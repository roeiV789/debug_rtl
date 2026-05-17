from typing import Any, Dict

import yaml

from ..models.spec_models import FSMDefinition, ProtocolRule, Specification


def parse_spec(data: bytes) -> Specification:
    """Parse a YAML-encoded AXI-Lite protocol specification into a Specification dataclass.

    Expected top-level YAML keys:
        interface_type, version, description, protocol_rules, fsm_definition

    protocol_rules is a list of mappings with keys:
        id, name, description, trigger, assert_condition, severity

    fsm_definition is a mapping with keys:
        name, states, initial_state, valid_transitions
    """
    raw: Dict[str, Any] = yaml.safe_load(data)

    # --- Protocol Rules ---
    protocol_rules = []
    for rule_raw in raw.get("protocol_rules", []):
        rule = ProtocolRule(
            id=str(rule_raw["id"]),
            name=str(rule_raw["name"]),
            description=str(rule_raw.get("description", "")),
            trigger=str(rule_raw["trigger"]),
            assert_condition=str(rule_raw["assert_condition"]),
            severity=str(rule_raw["severity"]),
        )
        protocol_rules.append(rule)

    # --- FSM Definition ---
    fsm_raw = raw.get("fsm_definition", {})
    valid_transitions_raw: Dict[str, Any] = fsm_raw.get("valid_transitions", {})
    # Ensure values are lists of strings
    valid_transitions: Dict[str, list] = {
        str(from_state): [str(s) for s in (allowed or [])]
        for from_state, allowed in valid_transitions_raw.items()
    }
    fsm_definition = FSMDefinition(
        name=str(fsm_raw.get("name", "")),
        states=[str(s) for s in fsm_raw.get("states", [])],
        initial_state=str(fsm_raw.get("initial_state", "")),
        valid_transitions=valid_transitions,
    )

    return Specification(
        interface_type=str(raw.get("interface_type", "")),
        version=str(raw.get("version", "")),
        description=str(raw.get("description", "")),
        protocol_rules=protocol_rules,
        fsm_definition=fsm_definition,
    )
