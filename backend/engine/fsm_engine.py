from typing import Any, List, Optional

from ..models.analysis_models import FSMTransition
from ..models.sim_models import SignalDatabase, SignalFrame
from ..models.spec_models import Specification


def _get_state(frame: SignalFrame) -> Optional[str]:
    """Extract the FSM state string from a signal frame.

    The signal is expected to be named 'fsm_state'. Returns None if absent.
    """
    val = frame.signals.get("fsm_state")
    if val is None:
        return None
    return str(val)


def run_fsm_engine(
    spec: Specification,
    signal_db: SignalDatabase,
) -> List[FSMTransition]:
    """Detect all FSM state transitions in the simulation trace and validate them.

    For each pair of consecutive frames where the FSM state differs, a
    FSMTransition is emitted. The ``valid`` field is True iff the destination
    state is listed as an allowed successor of the source state in the spec's
    FSM definition.

    Both valid and invalid transitions are returned so callers can build a
    complete picture of the FSM's execution history.
    """
    fsm_def = spec.fsm_definition
    valid_transitions_map = fsm_def.valid_transitions  # {from_state: [next_states]}

    transitions: List[FSMTransition] = []
    frames = signal_db.frames

    if len(frames) < 2:
        return transitions

    for i in range(1, len(frames)):
        prev_frame = frames[i - 1]
        curr_frame = frames[i]

        from_state = _get_state(prev_frame)
        to_state = _get_state(curr_frame)

        # Skip frames where fsm_state is not present or hasn't changed
        if from_state is None or to_state is None:
            continue
        if from_state == to_state:
            continue

        # Determine allowed next states from the current from_state
        allowed_next: List[str] = list(valid_transitions_map.get(from_state, []))

        is_valid = to_state in allowed_next

        transitions.append(
            FSMTransition(
                from_state=from_state,
                to_state=to_state,
                cycle=curr_frame.cycle,
                valid=is_valid,
                allowed_next=allowed_next,
            )
        )

    return transitions
