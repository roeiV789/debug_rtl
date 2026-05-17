from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SignalFrame:
    cycle: int
    signals: Dict[str, Any]


@dataclass
class SignalDatabase:
    frames: List[SignalFrame]
    signal_names: List[str]
    by_cycle: Dict[int, SignalFrame]     # indexed at build time
    by_signal: Dict[str, List[Any]]      # indexed at build time

    def query_cycles(self, signal: str, value: Any) -> List[int]:
        """Return all cycle numbers where signal == value."""
        result: List[int] = []
        for frame in self.frames:
            sig_val = frame.signals.get(signal)
            if sig_val == value:
                result.append(frame.cycle)
        return result

    def window(self, start: int, end: int) -> List[SignalFrame]:
        """Return frames in inclusive cycle range [start, end]."""
        return [frame for frame in self.frames if start <= frame.cycle <= end]
