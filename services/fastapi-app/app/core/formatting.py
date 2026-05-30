"""Shared formatting helpers (no HTTP or framework dependencies)."""
from __future__ import annotations

_BINARY_UNITS = ("B", "KB", "MB", "GB", "TB", "PB")


def format_bytes_for_display(size: int | None, *, decimals: int = 2) -> str | None:
    """
    Turn a byte count into a short label such as ``879.42 GB`` or ``1.01 TB``.

    Uses 1024-based steps (same as most OS disk tools).
    """
    if size is None:
        return None
    if size < 0:
        size = 0
    value = float(size)
    unit = "B"
    for candidate in _BINARY_UNITS:
        unit = candidate
        if value < 1024.0 or candidate == _BINARY_UNITS[-1]:
            break
        value /= 1024.0
    if unit == "B":
        return f"{int(value)} B"
    return f"{value:.{decimals}f} {unit}"
