"""CUSUM change-point detection on a recent value series."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Shift:
    direction: str  # "up" | "down"
    magnitude: float
    index: int  # index in the series where the shift starts (best estimate)


def detect_recent_shift(
    series: list[float],
    window: int = 5,
    threshold: float = 0.8,
) -> Optional[Shift]:
    """Detect a sustained recent shift using a simple CUSUM-style test.

    - Requires at least `2*window` points.
    - Compares the mean of the trailing `window` vs the mean of the
      preceding points; reports a Shift when |Δ| >= threshold AND the
      last `window` points are all on the same side of the baseline mean.
    """
    if not series or len(series) < 2 * window:
        return None

    import numpy as np

    arr = np.array(series, dtype=float)
    baseline = arr[:-window]
    recent = arr[-window:]
    base_mean = float(baseline.mean())
    recent_mean = float(recent.mean())
    delta = recent_mean - base_mean
    if abs(delta) < threshold:
        return None
    if delta > 0 and not (recent > base_mean).all():
        return None
    if delta < 0 and not (recent < base_mean).all():
        return None
    return Shift(
        direction="up" if delta > 0 else "down",
        magnitude=abs(delta),
        index=len(arr) - window,
    )
