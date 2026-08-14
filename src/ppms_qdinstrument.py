"""ppms_qdinstrument.py

Minimal, documented Python wrapper for Quantum Design PPMS control via QDInstrument.dll.

Requires:
- 32-bit Python
- pythonnet (`pip install pythonnet`)
- Access to QDInstrument.dll from the Quantum Design installation

Features:
- connect to PPMS through QDInstrument.dll
- read temperature and field
- query and set bridge configuration
- read bridge current/resistance pairs
- send arbitrary PPMS commands through SendPPMSCommand
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    import clr
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "pythonnet is required. Install it in 32-bit Python with: pip install pythonnet"
    ) from exc


RESISTANCE_ITEMS = {1: 4, 2: 6, 3: 8, 4: 10}
CURRENT_ITEMS = {1: 5, 2: 7, 3: 9, 4: 11}
DRIVE_MODE = {0: "AC", 1: "DC"}
CAL_MODE = {0: "Standard", 1: "Fast", 2: "HiRes"}


@dataclass
class BridgeConfig:
    enabled: bool
    current_uA: float
    power_uW: float
    drive_mode_code: int
    drive_mode: str
    calibration_mode_code: int
    calibration_mode: str
    voltage_mV: float
    raw: str


@dataclass
class BridgeMeasurement:
    channel: int
    current_uA: float
    resistance_ohm: float
    current_error: int = 0
    resistance_error: int = 0


class PPMSClient:
    """Small wrapper around QuantumDesign.QDInstrument for PPMS control."""

    def __init__(self, dll_path: str, remote: bool = False, ip: str = "127.0.0.1", port: int = 5000):
        self.dll_path = Path(dll_path).resolve()
        if not self.dll_path.exists():
            raise FileNotFoundError(f"QDInstrument.dll not found: {self.dll_path}")

        clr.AddReference(str(self.dll_path))
        import System
        import QuantumDesign.QDInstrument as QDI

        self.System = System
        self.QDI = QDI
        self.remote = remote
        self.ip = ip
        self.port = port
        self.inst = QDI.QDInstrumentFactory.GetQDInstrument(
            QDI.QDInstrumentBase.QDInstrumentType.PPMS,
            System.Boolean(remote),
            System.String(ip),
            System.UInt16(port),
        )

    @classmethod
    def connect(cls, dll_path: str, remote: bool = False, ip: str = "127.0.0.1", port: int = 5000) -> "PPMSClient":
        return cls(dll_path=dll_path, remote=remote, ip=ip, port=port)

    def _unwrap_3(self, result: Any) -> Tuple[int, str, str]:
        if not (isinstance(result, tuple) and len(result) == 3):
            raise RuntimeError(f"Unexpected 3-value return format: {result!r}")
        err, reply, error_reply = result
        return int(err), str(reply).strip(), str(error_reply).strip()

    def _unwrap_2(self, result: Any) -> Tuple[int, float]:
        if not (isinstance(result, tuple) and len(result) == 2):
            raise RuntimeError(f"Unexpected 2-value return format: {result!r}")
        err, value = result
        return int(err), float(value)

    def send_command(self, command: str, device: int = 15, timeout: float = 10.0) -> Tuple[int, str, str]:
        """Send an arbitrary PPMS command through SendPPMSCommand."""
        result = self.inst.SendPPMSCommand(
            command,
            self.System.String(""),
            self.System.String(""),
            self.System.Int32(device),
            self.System.Double(timeout),
        )
        return self._unwrap_3(result)

    def get_temperature(self) -> Dict[str, Any]:
        err, temp, status = self.inst.GetTemperature(
            self.System.Double(0.0),
            self.QDI.QDInstrumentBase.TemperatureStatus(0),
        )
        return {
            "error": int(err),
            "temperature_K": float(temp),
            "status": status,
            "status_text": self.inst.TemperatureStatusString(status),
        }

    def get_field(self) -> Dict[str, Any]:
        err, field, status = self.inst.GetField(
            self.System.Double(0.0),
            self.QDI.QDInstrumentBase.FieldStatus(0),
        )
        return {
            "error": int(err),
            "field_Oe": float(field),
            "status": status,
            "status_text": self.inst.FieldStatusString(status),
        }

    def bridge_query_raw(self, channel: int, device: int = 15, timeout: float = 10.0) -> Tuple[int, str, str]:
        return self.send_command(f"BRIDGE? {channel}", device=device, timeout=timeout)

    def parse_bridge_reply(self, reply: str) -> BridgeConfig:
        parts = [p.strip() for p in reply.split(",")]
        if len(parts) < 6:
            raise ValueError(f"Unexpected bridge reply format: {reply!r}")
        enabled = int(float(parts[0]))
        current_uA = float(parts[1])
        power_uW = float(parts[2])
        drive_code = int(float(parts[3]))
        mode_code = int(float(parts[4]))
        voltage_mV = float(parts[5])
        return BridgeConfig(
            enabled=bool(enabled),
            current_uA=current_uA,
            power_uW=power_uW,
            drive_mode_code=drive_code,
            drive_mode=DRIVE_MODE.get(drive_code, f"Unknown({drive_code})"),
            calibration_mode_code=mode_code,
            calibration_mode=CAL_MODE.get(mode_code, f"Unknown({mode_code})"),
            voltage_mV=voltage_mV,
            raw=reply,
        )

    def get_bridge(self, channel: int, fast: bool = True) -> BridgeMeasurement:
        if channel not in RESISTANCE_ITEMS:
            raise ValueError("Bridge channel must be 1..4")
        err_i, current_uA = self._unwrap_2(
            self.inst.GetPPMSItem(
                self.System.Int32(CURRENT_ITEMS[channel]),
                self.System.Double(0.0),
                self.System.Boolean(fast),
            )
        )
        err_r, resistance_ohm = self._unwrap_2(
            self.inst.GetPPMSItem(
                self.System.Int32(RESISTANCE_ITEMS[channel]),
                self.System.Double(0.0),
                self.System.Boolean(fast),
            )
        )
        return BridgeMeasurement(
            channel=channel,
            current_uA=current_uA,
            resistance_ohm=resistance_ohm,
            current_error=err_i,
            resistance_error=err_r,
        )

    def set_bridge(self, channel: int, excitation_uA: float, power_uW: float, dc: bool = False,
                   mode: int = 0, device: int = 15, timeout: float = 10.0) -> Tuple[int, str, str]:
        cmd = f"BRIDGE {channel} {excitation_uA:g} {power_uW:g} {1 if dc else 0} {mode}"
        return self.send_command(cmd, device=device, timeout=timeout)

    def close(self) -> None:
        """Placeholder for future cleanup; QDInstrument manages its own lifetime."""
        return None
