"""Personalized reminder time via von Mises KDE on hour-of-day."""

from __future__ import annotations

from datetime import time
from typing import Iterable


def compute_optimal_reminder(entry_hours: Iterable[int], fallback: time) -> time:
    """Return the modal hour-of-day for entries, fallback if < 7 samples.

    Uses a von Mises KDE on the circle (kappa=4 ~ moderate concentration),
    evaluated at each integer hour. Returns hour with peak density.
    """
    hours = [int(h) % 24 for h in entry_hours]
    if len(hours) < 7:
        return fallback

    import numpy as np

    angles = np.array(hours) * (2.0 * np.pi / 24.0)
    kappa = 4.0
    grid_hours = np.arange(24)
    grid_angles = grid_hours * (2.0 * np.pi / 24.0)
    # KDE: sum exp(kappa * cos(theta - mu_i)) over samples
    diff = grid_angles[:, None] - angles[None, :]
    density = np.exp(kappa * np.cos(diff)).sum(axis=1)
    peak_hour = int(grid_hours[int(np.argmax(density))])
    return time(hour=peak_hour, minute=0)
