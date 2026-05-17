import io
from typing import Any, Dict, List

import pandas as pd

from ..models.sim_models import SignalDatabase, SignalFrame


def _coerce(value: Any) -> Any:
    """Attempt to coerce a value to int, then float, otherwise keep as string."""
    if pd.isna(value):
        return None
    # pandas may already have typed it; normalise to Python builtins
    if isinstance(value, (int,)):
        return int(value)
    if isinstance(value, float):
        # If the float is a whole number, prefer int representation
        if value == int(value):
            return int(value)
        return float(value)
    # String column — attempt numeric parse
    s = str(value).strip()
    try:
        int_val = int(s)
        return int_val
    except ValueError:
        pass
    try:
        float_val = float(s)
        if float_val == int(float_val):
            return int(float_val)
        return float_val
    except ValueError:
        pass
    return s


def parse_sim(data: bytes) -> SignalDatabase:
    """Parse a CSV simulation trace into a SignalDatabase.

    The CSV must have a 'cycle' column (integer). All other columns are signal
    values. Type detection is performed automatically per cell: int preferred,
    then float, then string.

    Returns a fully indexed SignalDatabase with:
        - frames      : ordered list of SignalFrame
        - signal_names: column names excluding 'cycle'
        - by_cycle    : dict mapping cycle number -> SignalFrame
        - by_signal   : dict mapping signal name -> list of values (one per frame,
                        in frame order)
    """
    df = pd.read_csv(io.BytesIO(data))

    if "cycle" not in df.columns:
        raise ValueError("Simulation CSV must contain a 'cycle' column.")

    signal_names: List[str] = [col for col in df.columns if col != "cycle"]

    frames: List[SignalFrame] = []
    by_cycle: Dict[int, SignalFrame] = {}
    by_signal: Dict[str, List[Any]] = {name: [] for name in signal_names}

    for _, row in df.iterrows():
        cycle = int(row["cycle"])
        signals: Dict[str, Any] = {name: _coerce(row[name]) for name in signal_names}
        frame = SignalFrame(cycle=cycle, signals=signals)
        frames.append(frame)
        by_cycle[cycle] = frame
        for name in signal_names:
            by_signal[name].append(signals[name])

    return SignalDatabase(
        frames=frames,
        signal_names=signal_names,
        by_cycle=by_cycle,
        by_signal=by_signal,
    )
