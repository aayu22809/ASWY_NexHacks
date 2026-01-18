"""Shared thermal state for cross-module access."""

from __future__ import annotations

import time
from threading import Lock
from typing import Any, Dict, Optional

_lock = Lock()
_state: Dict[str, Any] = {
    "frame": None,
    "max_temp": None,
    "min_temp": None,
    "mean_temp": None,
    "ambient_c": None,
    "source": None,
    "timestamp": None,
}


def set_from_frame(frame, timestamp: Optional[str] = None, source: Optional[str] = None) -> None:
    try:
        import numpy as np
        max_temp = float(np.max(frame))
        min_temp = float(np.min(frame))
        mean_temp = float(np.mean(frame))
    except Exception:
        return
    _update(
        frame=frame,
        max_temp=max_temp,
        min_temp=min_temp,
        mean_temp=mean_temp,
        ambient_c=None,
        source=source,
        timestamp=timestamp or time.strftime("%Y-%m-%dT%H:%M:%S"),
    )


def set_from_temp(
    temp_c: float,
    ambient_c: Optional[float] = None,
    timestamp: Optional[str] = None,
    source: Optional[str] = None,
) -> None:
    temp_c = float(temp_c)
    _update(
        frame=None,
        max_temp=temp_c,
        min_temp=temp_c,
        mean_temp=temp_c,
        ambient_c=ambient_c,
        source=source,
        timestamp=timestamp or time.strftime("%Y-%m-%dT%H:%M:%S"),
    )


def _update(**kwargs) -> None:
    with _lock:
        _state.update(kwargs)


def snapshot() -> Dict[str, Any]:
    with _lock:
        return dict(_state)
