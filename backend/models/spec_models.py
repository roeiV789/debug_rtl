from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ProtocolRule:
    id: str
    name: str
    description: str
    trigger: str           # e.g. "awvalid == 1"
    assert_condition: str  # e.g. "awready == 1 within 5 cycles"
    severity: str          # CRITICAL | ERROR | WARNING


@dataclass
class FSMDefinition:
    name: str
    states: List[str]
    initial_state: str
    valid_transitions: Dict[str, List[str]]  # {from_state: [allowed_next]}


@dataclass
class Specification:
    interface_type: str
    version: str
    description: str
    protocol_rules: List[ProtocolRule]
    fsm_definition: FSMDefinition
