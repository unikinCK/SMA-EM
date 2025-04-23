"""
SMA Home Manager 2.0 Speedwire decoder

Original authors:
    • david-m-m   2019‑03‑17
    • datenschuft 2020‑01‑04

Revision history (excerpt):
    • 2025‑04‑23  Read *actual* values as signed INT32
    • 2025‑04‑23  Derive signed phase currents (i1/i2/i3) from net phase power

This software is released under the GNU General Public License v2.
"""

from __future__ import annotations
import binascii
from typing import Dict, Tuple

# ──────────────────────────────────────────────────────────────────────────────
#  Configuration tables
# ──────────────────────────────────────────────────────────────────────────────

# Unit definitions with scaling factors (to base unit)
sma_units: Dict[str, int] = {
    "W": 10,
    "VA": 10,
    "VAr": 10,
    "kWh": 3_600_000,
    "kVAh": 3_600_000,
    "kVArh": 3_600_000,
    "A": 1_000,
    "V": 1_000,
    "°": 1_000,
    "Hz": 1_000,
}

# Channel map:  <channel_number>: (name, unit_actual, unit_total)
sma_channels: Dict[int, Tuple[str, str, str]] = {
    # Totals
    1: ("pconsume", "W", "kWh"),
    2: ("psupply", "W", "kWh"),
    3: ("qconsume", "VAr", "kVArh"),
    4: ("qsupply", "VAr", "kVArh"),
    9: ("sconsume", "VA", "kVAh"),
    10: ("ssupply", "VA", "kVAh"),
    13: ("cosphi", "°", ""),
    14: ("frequency", "Hz", ""),
    # Phase 1
    21: ("p1consume", "W", "kWh"),
    22: ("p1supply", "W", "kWh"),
    23: ("q1consume", "VAr", "kVArh"),
    24: ("q1supply", "VAr", "kVArh"),
    29: ("s1consume", "VA", "kVAh"),
    30: ("s1supply", "VA", "kVAh"),
    31: ("i1", "A", ""),
    32: ("u1", "V", ""),
    33: ("cosphi1", "°", ""),
    # Phase 2
    41: ("p2consume", "W", "kWh"),
    42: ("p2supply", "W", "kWh"),
    43: ("q2consume", "VAr", "kVArh"),
    44: ("q2supply", "VAr", "kVArh"),
    49: ("s2consume", "VA", "kVAh"),
    50: ("s2supply", "VA", "kVAh"),
    51: ("i2", "A", ""),
    52: ("u2", "V", ""),
    53: ("cosphi2", "°", ""),
    # Phase 3
    61: ("p3consume", "W", "kWh"),
    62: ("p3supply", "W", "kWh"),
    63: ("q3consume", "VAr", "kVArh"),
    64: ("q3supply", "VAr", "kVArh"),
    69: ("s3consume", "VA", "kVAh"),
    70: ("s3supply", "VA", "kVAh"),
    71: ("i3", "A", ""),
    72: ("u3", "V", ""),
    73: ("cosphi3", "°", ""),
    # Common
    36864: ("speedwire-version", "", ""),
}

# ──────────────────────────────────────────────────────────────────────────────
#  Helper functions
# ──────────────────────────────────────────────────────────────────────────────

def _decode_obis_header(obis: bytes) -> Tuple[int, str]:
    """Return (measurement-id, datatype) for a 4‑byte OBIS header."""
    measurement = int.from_bytes(obis[:2], "big")
    raw_type = obis[2]

    match raw_type:
        case 4:
            dtype = "actual"
        case 8:
            dtype = "counter"
        case 0 if measurement == 36864:
            dtype = "version"
        case _:
            dtype = "unknown"
            print(f"Unknown datatype: measurement {measurement}, raw {raw_type}")

    return measurement, dtype

# ──────────────────────────────────────────────────────────────────────────────
#  Main decoder
# ──────────────────────────────────────────────────────────────────────────────

def decode_speedwire(datagram: bytes) -> Dict[str, float | str]:
    """Decode a single Speedwire datagram from the SMA Home Manager 2.0.

    Returns a dict with *engineering‑value* entries (scaled) plus meta‑data.
    Additionally, phase currents `i1`, `i2`, `i3` are returned **with logical
    sign** (‑ = Einspeisung, + = Bezug) – derived from net phase power.
    """

    emparts: Dict[str, float | str] = {}

    # ── pre‑checks ────────────────────────────────────────────────────────────
    if datagram[:3] != b"SMA":
        return emparts

    datalen = int.from_bytes(datagram[12:14], "big") + 16
    if datalen == 54:  # keep‑alive telegram – no measurements
        return emparts

    # ── header meta‑data ──────────────────────────────────────────────────────
    emparts["serial"] = int.from_bytes(datagram[20:24], "big")
    emparts["timestamp"] = int.from_bytes(datagram[24:28], "big")

    # ── iterate over OBIS blocks ──────────────────────────────────────────────
    pos = 28
    while pos < datalen:
        meas, dtype = _decode_obis_header(datagram[pos:pos + 4])

        if dtype == "actual":
            raw = datagram[pos + 4:pos + 8]
            val = int.from_bytes(raw, "big", signed=True)  # signed INT32!
            pos += 8

            if meas in sma_channels:
                name, unit_a, _ = sma_channels[meas]
                emparts[name] = val / sma_units[unit_a]
                emparts[f"{name}unit"] = unit_a

        elif dtype == "counter":
            val = int.from_bytes(datagram[pos + 4:pos + 12], "big")
            pos += 12
            if meas in sma_channels:
                name, _, unit_t = sma_channels[meas]
                emparts[f"{name}counter"] = val / sma_units[unit_t]
                emparts[f"{name}counterunit"] = unit_t

        elif dtype == "version":
            raw = datagram[pos + 4:pos + 8]
            pos += 8
            if meas in sma_channels:
                hexver = binascii.b2a_hex(raw).decode()
                version = f"{int(hexver[0:2],16)}.{int(hexver[2:4],16)}.{int(hexver[4:6],16)}"
                revision = {
                    "1": ".S", "2": ".A", "3": ".B", "4": ".R",
                    "5": ".E", "6": ".N",
                }.get(chr(int(hexver[6:8], 16)), "")
                emparts[sma_channels[meas][0]] = f"{version}{revision}|{hexver[:6]}"
        else:
            pos += 8  # skip unknown block

    # ── derive signed phase currents ──────────────────────────────────────────
    _derive_signed_currents(emparts)

    return emparts

# ──────────────────────────────────────────────────────────────────────────────
#  Post‑processing helpers
# ──────────────────────────────────────────────────────────────────────────────

def _derive_signed_currents(values: Dict[str, float | str]) -> None:
    """Add logical sign to i1/i2/i3 based on net phase power (pXconsume‑pXsupply)."""

    for phase in (1, 2, 3):
        try:
            p_cons = values.get(f"p{phase}consume", 0.0)  # in W
            p_supp = values.get(f"p{phase}supply", 0.0)
            i_abs = values.get(f"i{phase}")
            if i_abs is None:
                continue

            p_net = p_cons - p_supp  # >0 = Bezug, <0 = Einspeisung
            sign = -1 if p_net < 0 else 1
            values[f"i{phase}"] = sign * i_abs
        except Exception as exc:  # pragma: no cover – never fail caller
            print(f"Signed current derivation error (phase {phase}): {exc}")
