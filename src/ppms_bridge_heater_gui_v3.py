"""Small GUI to use PPMS bridge channels as heaters via QDInstrument.dll.

Windows-only UI improvements:
- follows Windows app light/dark preference on startup and while running
- uses Bahnschrift as the primary UI font when available
- requests immersive dark title bar on supported Windows versions
"""

from __future__ import annotations

import ctypes
import math
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
import winreg

from ppms_qdinstrument import PPMSClient

try:
    import MultiPyVu as mpv
except Exception:
    mpv = None

MODE_NAME_TO_CODE = {"Standard": 0, "Fast": 1, "HiRes": 2}
APP_MODES = ["Ramp", "Field Controlled", "Field Stability", "Field Controlled Ramp", "Field Stability Ramp"]
RAMP_SHAPES = ["Linear", "Exponential", "Square", "Root"]
BACKENDS = ["PPMS", "DynaCool MPV"]

LIGHT_THEME = {
    "bg": "#f3f3f3",
    "card": "#ffffff",
    "fg": "#111111",
    "muted": "#5f5f5f",
    "accent": "#0a64ad",
    "input": "#ffffff",
    "border": "#d9d9d9",
}

DARK_THEME = {
    "bg": "#1f1f1f",
    "card": "#2b2b2b",
    "fg": "#f2f2f2",
    "muted": "#b9b9b9",
    "accent": "#4ea1ff",
    "input": "#323232",
    "border": "#424242",
}

class BridgeHeaterGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PPMS Bridge Heater Control")
        self.client = None
        self.mpv_client = None
        self.theme_name = None
        self.font_family = "Bahnschrift"

        self.ramp_running = False
        self.auto_running = False
        self.stop_requested = False
        self.auto_stop_requested = False
        self.ramp_thread = None
        self.auto_thread = None
        self.auto_suspended = False
        self.last_field_points = []

        self.backend_name = tk.StringVar(value="PPMS")
        self.dll_path = tk.StringVar(value=str(Path("QDInstrument.dll").resolve()))
        self.remote = tk.BooleanVar(value=False)
        self.ip = tk.StringVar(value="127.0.0.1")
        self.port = tk.IntVar(value=5000)

        self.app_mode = tk.StringVar(value="Ramp")
        self.channel = tk.IntVar(value=2)
        self.initial_uA = tk.DoubleVar(value=500.0)
        self.final_uA = tk.DoubleVar(value=2000.0)
        self.duration_s = tk.DoubleVar(value=7200.0)
        self.power_limit_uW = tk.DoubleVar(value=100.0)
        self.drive_dc = tk.BooleanVar(value=True)
        self.mode_name = tk.StringVar(value="Standard")
        self.ramp_shape = tk.StringVar(value="Linear")
        self.poll_fast = tk.BooleanVar(value=True)
        self.step_interval_s = tk.DoubleVar(value=10.0)

        self.field_low_uA = tk.DoubleVar(value=0.1)
        self.field_high_uA = tk.DoubleVar(value=100.0)
        self.field_threshold_oe = tk.DoubleVar(value=100.0)
        self.field_check_interval_s = tk.DoubleVar(value=5.0)
        self.field_wait_s = tk.DoubleVar(value=0.0)

        self.stab_low_uA = tk.DoubleVar(value=0.1)
        self.stab_high_uA = tk.DoubleVar(value=100.0)
        self.stab_dbdt_threshold = tk.DoubleVar(value=1.0)
        self.stab_max_field_oe = tk.DoubleVar(value=10000.0)
        self.stab_check_interval_s = tk.DoubleVar(value=5.0)
        self.stab_wait_s = tk.DoubleVar(value=0.0)

        self.live_resistance = tk.StringVar(value="-")
        self.live_current = tk.StringVar(value="-")
        self.live_power = tk.StringVar(value="-")
        self.live_field = tk.StringVar(value="-")
        self.live_dbdt = tk.StringVar(value="-")
        self.live_status = tk.StringVar(value="Disconnected")
        self.target_status = tk.StringVar(value="Idle")

        self._build_ui()
        self._apply_system_theme(initial=True)
        self._update_mode_visibility()
        self._schedule_poll()
        self._watch_theme_changes()


    def _get_windows_theme_mode(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if int(value) else "dark"
        except Exception:
            return "light"

    def _set_dark_title_bar(self, dark: bool):
        try:
            self.root.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            value = ctypes.c_int(1 if dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
        except Exception:
            pass

    def _apply_system_theme(self, initial: bool = False):
        mode = self._get_windows_theme_mode()
        if self.theme_name == mode and not initial:
            return
        self.theme_name = mode
        palette = DARK_THEME if mode == "dark" else LIGHT_THEME

        default_font = (self.font_family, 10)
        heading_font = (self.font_family, 10)
        self.root.option_add("*Font", default_font)
        self.root.configure(bg=palette["bg"])

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TFrame", background=palette["bg"])
        style.configure("TLabelframe", background=palette["bg"], foreground=palette["fg"], borderwidth=1)
        style.configure("TLabelframe.Label", background=palette["bg"], foreground=palette["fg"], font=heading_font)
        style.configure("TLabel", background=palette["bg"], foreground=palette["fg"])
        style.configure("TButton", background=palette["card"], foreground=palette["fg"], bordercolor=palette["border"], focusthickness=1, focuscolor=palette["accent"])
        style.map("TButton", background=[("active", palette["accent"])], foreground=[("active", palette["card"])])
        style.configure("TCheckbutton", background=palette["bg"], foreground=palette["fg"])
        style.configure("TCombobox", fieldbackground=palette["input"], background=palette["input"], foreground=palette["fg"], arrowcolor=palette["fg"], bordercolor=palette["border"])
        style.configure("TEntry", fieldbackground=palette["input"], foreground=palette["fg"], bordercolor=palette["border"])
        style.configure("TSpinbox", fieldbackground=palette["input"], foreground=palette["fg"], bordercolor=palette["border"])

        self._set_dark_title_bar(mode == "dark")

    def _watch_theme_changes(self):
        self._apply_system_theme()
        self.root.after(2000, self._watch_theme_changes)

    def _build_ui(self):
        pad = {"padx": 8, "pady": 6}

        frm_conn = ttk.LabelFrame(self.root, text="Connection")
        frm_conn.pack(fill="x", padx=10, pady=8)
        ttk.Label(frm_conn, text="Backend").grid(row=0, column=0, sticky="w", **pad)
        backend_box = ttk.Combobox(frm_conn, textvariable=self.backend_name, width=16, state="readonly", values=BACKENDS)
        backend_box.grid(row=0, column=1, sticky="w", **pad)
        ttk.Label(frm_conn, text="QDInstrument.dll").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(frm_conn, textvariable=self.dll_path, width=50).grid(row=1, column=1, columnspan=4, sticky="ew", **pad)
        ttk.Checkbutton(frm_conn, text="Remote", variable=self.remote).grid(row=2, column=0, sticky="w", **pad)
        ttk.Label(frm_conn, text="IP").grid(row=2, column=1, sticky="e", **pad)
        ttk.Entry(frm_conn, textvariable=self.ip, width=14).grid(row=2, column=2, sticky="w", **pad)
        ttk.Label(frm_conn, text="Port").grid(row=2, column=3, sticky="e", **pad)
        ttk.Entry(frm_conn, textvariable=self.port, width=8).grid(row=2, column=4, sticky="w", **pad)
        ttk.Button(frm_conn, text="Connect", command=self.connect).grid(row=0, column=5, rowspan=2, sticky="nsew", **pad)

        frm_common = ttk.LabelFrame(self.root, text="Bridge Setup")
        frm_common.pack(fill="x", padx=10, pady=8)
        ttk.Label(frm_common, text="Channel").grid(row=0, column=0, sticky="w", **pad)
        ttk.Spinbox(frm_common, from_=1, to=4, textvariable=self.channel, width=6).grid(row=0, column=1, sticky="w", **pad)
        ttk.Label(frm_common, text="Power limit (µW)").grid(row=0, column=2, sticky="w", **pad)
        ttk.Entry(frm_common, textvariable=self.power_limit_uW, width=12).grid(row=0, column=3, sticky="w", **pad)
        ttk.Checkbutton(frm_common, text="Use DC", variable=self.drive_dc).grid(row=0, column=4, sticky="w", **pad)
        ttk.Label(frm_common, text="Mode").grid(row=0, column=5, sticky="w", **pad)
        ttk.Combobox(frm_common, textvariable=self.mode_name, width=12, state="readonly", values=["Standard", "Fast", "HiRes"]).grid(row=0, column=6, sticky="w", **pad)
        ttk.Label(frm_common, text="Controller mode").grid(row=1, column=0, sticky="w", **pad)
        mode_box = ttk.Combobox(frm_common, textvariable=self.app_mode, width=18, state="readonly", values=APP_MODES)
        mode_box.grid(row=1, column=1, sticky="w", **pad)
        mode_box.bind("<<ComboboxSelected>>", lambda _e: self._update_mode_visibility())

        self.frm_ramp = ttk.LabelFrame(self.root, text="Ramp Mode")
        ttk.Label(self.frm_ramp, text="Initial current (µA)").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(self.frm_ramp, textvariable=self.initial_uA, width=12).grid(row=0, column=1, sticky="w", **pad)
        ttk.Label(self.frm_ramp, text="Final current (µA)").grid(row=0, column=2, sticky="w", **pad)
        ttk.Entry(self.frm_ramp, textvariable=self.final_uA, width=12).grid(row=0, column=3, sticky="w", **pad)
        ttk.Label(self.frm_ramp, text="Ramp time (s)").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(self.frm_ramp, textvariable=self.duration_s, width=12).grid(row=1, column=1, sticky="w", **pad)
        ttk.Label(self.frm_ramp, text="Step interval (s)").grid(row=1, column=2, sticky="w", **pad)
        ttk.Entry(self.frm_ramp, textvariable=self.step_interval_s, width=12).grid(row=1, column=3, sticky="w", **pad)
        ttk.Label(self.frm_ramp, text="Ramp shape").grid(row=2, column=0, sticky="w", **pad)
        ttk.Combobox(self.frm_ramp, textvariable=self.ramp_shape, width=12, state="readonly", values=RAMP_SHAPES).grid(row=2, column=1, sticky="w", **pad)
        ramp_btns = ttk.Frame(self.frm_ramp)
        ramp_btns.grid(row=3, column=0, columnspan=4, sticky="w", **pad)
        ttk.Button(ramp_btns, text="Apply Initial", command=self.apply_initial).pack(side="left", padx=6)
        ttk.Button(ramp_btns, text="Start Ramp", command=self.start_ramp).pack(side="left", padx=6)
        ttk.Button(ramp_btns, text="Stop Ramp", command=self.stop_ramp).pack(side="left", padx=6)

        self.frm_field = ttk.LabelFrame(self.root, text="Field Controlled Mode")
        ttk.Label(self.frm_field, text="Low current (µA)").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(self.frm_field, textvariable=self.field_low_uA, width=12).grid(row=0, column=1, sticky="w", **pad)
        ttk.Label(self.frm_field, text="High current (µA)").grid(row=0, column=2, sticky="w", **pad)
        ttk.Entry(self.frm_field, textvariable=self.field_high_uA, width=12).grid(row=0, column=3, sticky="w", **pad)
        ttk.Label(self.frm_field, text="Field threshold (Oe)").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(self.frm_field, textvariable=self.field_threshold_oe, width=12).grid(row=1, column=1, sticky="w", **pad)
        ttk.Label(self.frm_field, text="Check interval (s)").grid(row=1, column=2, sticky="w", **pad)
        ttk.Entry(self.frm_field, textvariable=self.field_check_interval_s, width=12).grid(row=1, column=3, sticky="w", **pad)
        ttk.Label(self.frm_field, text="Wait before high/ramp (s)").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(self.frm_field, textvariable=self.field_wait_s, width=12).grid(row=2, column=1, sticky="w", **pad)
        ttk.Label(self.frm_field, text="Ramp shape").grid(row=2, column=2, sticky="w", **pad)
        ttk.Combobox(self.frm_field, textvariable=self.ramp_shape, width=12, state="readonly", values=RAMP_SHAPES).grid(row=2, column=3, sticky="w", **pad)
        field_btns = ttk.Frame(self.frm_field)
        field_btns.grid(row=3, column=0, columnspan=4, sticky="w", **pad)
        ttk.Button(field_btns, text="AUTO", command=self.arm_field_mode).pack(side="left", padx=6)
        ttk.Button(field_btns, text="Manual High", command=lambda: self.manual_override("high", "field")).pack(side="left", padx=6)
        ttk.Button(field_btns, text="Manual Low", command=lambda: self.manual_override("low", "field")).pack(side="left", padx=6)
        ttk.Button(field_btns, text="Stop", command=self.stop_auto_mode).pack(side="left", padx=6)

        self.frm_stab = ttk.LabelFrame(self.root, text="Field Stability Mode")
        ttk.Label(self.frm_stab, text="Low current (µA)").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(self.frm_stab, textvariable=self.stab_low_uA, width=12).grid(row=0, column=1, sticky="w", **pad)
        ttk.Label(self.frm_stab, text="High current (µA)").grid(row=0, column=2, sticky="w", **pad)
        ttk.Entry(self.frm_stab, textvariable=self.stab_high_uA, width=12).grid(row=0, column=3, sticky="w", **pad)
        ttk.Label(self.frm_stab, text="|dB/dt| threshold (Oe/s)").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(self.frm_stab, textvariable=self.stab_dbdt_threshold, width=12).grid(row=1, column=1, sticky="w", **pad)
        ttk.Label(self.frm_stab, text="Max field (Oe)").grid(row=1, column=2, sticky="w", **pad)
        ttk.Entry(self.frm_stab, textvariable=self.stab_max_field_oe, width=12).grid(row=1, column=3, sticky="w", **pad)
        ttk.Label(self.frm_stab, text="Check interval (s)").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(self.frm_stab, textvariable=self.stab_check_interval_s, width=12).grid(row=2, column=1, sticky="w", **pad)
        ttk.Label(self.frm_stab, text="Wait before high/ramp (s)").grid(row=2, column=2, sticky="w", **pad)
        ttk.Entry(self.frm_stab, textvariable=self.stab_wait_s, width=12).grid(row=2, column=3, sticky="w", **pad)
        ttk.Label(self.frm_stab, text="Ramp shape").grid(row=3, column=0, sticky="w", **pad)
        ttk.Combobox(self.frm_stab, textvariable=self.ramp_shape, width=12, state="readonly", values=RAMP_SHAPES).grid(row=3, column=1, sticky="w", **pad)
        stab_btns = ttk.Frame(self.frm_stab)
        stab_btns.grid(row=4, column=0, columnspan=4, sticky="w", **pad)
        ttk.Button(stab_btns, text="AUTO", command=self.arm_stability_mode).pack(side="left", padx=6)
        ttk.Button(stab_btns, text="Manual High", command=lambda: self.manual_override("high", "stability")).pack(side="left", padx=6)
        ttk.Button(stab_btns, text="Manual Low", command=lambda: self.manual_override("low", "stability")).pack(side="left", padx=6)
        ttk.Button(stab_btns, text="Stop", command=self.stop_auto_mode).pack(side="left", padx=6)

        frm_live = ttk.LabelFrame(self.root, text="Live Values")
        frm_live.pack(fill="x", padx=10, pady=8)
        ttk.Label(frm_live, text="Resistance (Ω)").grid(row=0, column=0, sticky="w", **pad)
        ttk.Label(frm_live, textvariable=self.live_resistance).grid(row=0, column=1, sticky="w", **pad)
        ttk.Label(frm_live, text="Current (µA)").grid(row=1, column=0, sticky="w", **pad)
        ttk.Label(frm_live, textvariable=self.live_current).grid(row=1, column=1, sticky="w", **pad)
        ttk.Label(frm_live, text="Power (µW)").grid(row=2, column=0, sticky="w", **pad)
        ttk.Label(frm_live, textvariable=self.live_power).grid(row=2, column=1, sticky="w", **pad)
        ttk.Label(frm_live, text="Field (Oe)").grid(row=0, column=2, sticky="w", **pad)
        ttk.Label(frm_live, textvariable=self.live_field).grid(row=0, column=3, sticky="w", **pad)
        ttk.Label(frm_live, text="|dB/dt| (Oe/s)").grid(row=1, column=2, sticky="w", **pad)
        ttk.Label(frm_live, textvariable=self.live_dbdt).grid(row=1, column=3, sticky="w", **pad)
        ttk.Label(frm_live, text="State").grid(row=3, column=0, sticky="w", **pad)
        ttk.Label(frm_live, textvariable=self.live_status).grid(row=3, column=1, sticky="w", **pad)
        ttk.Label(frm_live, text="Controller").grid(row=4, column=0, sticky="w", **pad)
        ttk.Label(frm_live, textvariable=self.target_status).grid(row=4, column=1, columnspan=3, sticky="w", **pad)

    def _update_mode_visibility(self):
        for frame in (self.frm_ramp, self.frm_field, self.frm_stab):
            frame.pack_forget()
        mode = self.app_mode.get()
        if mode == "Ramp":
            self.frm_ramp.pack(fill="x", padx=10, pady=8)
        elif mode in ("Field Controlled", "Field Controlled Ramp"):
            self.frm_field.pack(fill="x", padx=10, pady=8)
        elif mode in ("Field Stability", "Field Stability Ramp"):
            self.frm_stab.pack(fill="x", padx=10, pady=8)

    def connect(self):
        try:
            backend = self.backend_name.get()
            self.client = None
            self.mpv_client = None
            if backend == "PPMS":
                self.client = PPMSClient.connect(self.dll_path.get(), remote=self.remote.get(), ip=self.ip.get(), port=int(self.port.get()))
            elif backend == "DynaCool MPV":
                if mpv is None:
                    raise RuntimeError("MultiPyVu is not installed in this Python environment.")
                client = mpv.Client(host=self.ip.get(), port=int(self.port.get()))
                client.open()
                self.mpv_client = client
            else:
                raise RuntimeError(f"Unsupported backend: {backend}")
            self.live_status.set(f"Connected ({backend})")
        except Exception as exc:
            self.client = None
            self.mpv_client = None
            self.live_status.set("Connection failed")
            messagebox.showerror("Connection error", str(exc))

    def _ensure_client(self):
        if self.backend_name.get() == "PPMS" and self.client is None:
            messagebox.showwarning("Not connected", "Connect to the selected backend first.")
            return False
        if self.backend_name.get() == "DynaCool MPV" and self.mpv_client is None:
            messagebox.showwarning("Not connected", "Connect to the selected backend first.")
            return False
        return True

    def _apply_current(self, current_uA: float):
        channel = int(self.channel.get())
        power_uW = float(self.power_limit_uW.get())
        dc = bool(self.drive_dc.get())
        mode_code = MODE_NAME_TO_CODE[self.mode_name.get()]
        if self.backend_name.get() == "PPMS":
            self.client.set_bridge(
                channel=channel,
                excitation_uA=float(current_uA),
                power_uW=power_uW,
                dc=dc,
                mode=mode_code,
            )
        else:
            current_limit = max(float(current_uA), 0.1)
            voltage_limit_mV = 10.0
            self.mpv_client.resistivity.bridge_setup(channel, True, current_limit, power_uW, voltage_limit_mV)
            self.mpv_client.resistivity.set_current(channel, float(current_uA), power_uW, voltage_limit_mV, dc, mode_code)


    def _get_field_oe(self) -> float:
        if self.backend_name.get() == "PPMS":
            return float(self.client.get_field()["field_Oe"])
        field_oe, _status = self.mpv_client.get_field()
        return float(field_oe)

    def apply_initial(self):
        if not self._ensure_client():
            return
        try:
            self._apply_current(float(self.initial_uA.get()))
            self.target_status.set("Initial value applied")
        except Exception as exc:
            messagebox.showerror("Apply initial failed", str(exc))

    def start_ramp(self):
        if not self._ensure_client():
            return
        if self.auto_running or self.ramp_running:
            messagebox.showinfo("Busy", "Another control mode is already active.")
            return
        try:
            initial = float(self.initial_uA.get())
            final = float(self.final_uA.get())
            duration = float(self.duration_s.get())
            step_interval = float(self.step_interval_s.get())
            ramp_shape = self.ramp_shape.get()
            if duration <= 0:
                raise ValueError("Ramp time must be > 0 s")
            if step_interval <= 0:
                raise ValueError("Step interval must be > 0 s")
        except Exception as exc:
            messagebox.showerror("Invalid input", str(exc))
            return
        self.stop_requested = False
        self.ramp_running = True
        self.target_status.set("Ramp running")
        self.ramp_thread = threading.Thread(target=self._ramp_worker, args=(initial, final, duration, step_interval, ramp_shape), daemon=True)
        self.ramp_thread.start()

    def stop_ramp(self):
        self.stop_requested = True
        self.target_status.set("Stopping ramp...")

    def _shape_fraction(self, frac: float, shape: str, initial: float, final: float) -> float:
        if shape == "Linear":
            return frac
        if shape == "Square":
            return frac ** 2
        if shape == "Root":
            return frac ** 0.5
        if shape == "Exponential":
            k = 4.0
            if final >= initial:
                return (math.exp(k * frac) - 1.0) / (math.exp(k) - 1.0)
            return 1.0 - (math.exp(k * (1.0 - frac)) - 1.0) / (math.exp(k) - 1.0)
        return frac

    def _ramp_worker(self, initial: float, final: float, duration: float, step_interval: float, ramp_shape: str):
        try:
            self._apply_current(initial)
            t0 = time.time()
            while True:
                if self.stop_requested:
                    self.root.after(0, lambda: self.target_status.set("Ramp stopped"))
                    break
                elapsed = time.time() - t0
                frac = min(max(elapsed / duration, 0.0), 1.0)
                shaped = self._shape_fraction(frac, ramp_shape, initial, final)
                current = initial + (final - initial) * shaped
                self._apply_current(current)
                self.root.after(0, lambda c=current: self.target_status.set(f"Ramp running, target {c:.4f} µA"))
                if frac >= 1.0:
                    self.root.after(0, lambda: self.target_status.set("Ramp complete"))
                    break
                time.sleep(step_interval)
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror("Ramp failed", str(exc)))
            self.root.after(0, lambda: self.target_status.set("Ramp error"))
        finally:
            self.ramp_running = False
            self.stop_requested = False

    def arm_field_mode(self):
        if not self._ensure_client():
            return
        if self.ramp_running or self.auto_running:
            messagebox.showinfo("Busy", "Another control mode is already active.")
            return
        self.auto_suspended = False
        self.auto_stop_requested = False
        self.auto_running = True
        self.target_status.set("Field control AUTO enabled")
        self.auto_thread = threading.Thread(target=self._field_control_worker, daemon=True)
        self.auto_thread.start()

    def _field_control_worker(self):
        try:
            low = float(self.field_low_uA.get())
            high = float(self.field_high_uA.get())
            threshold = float(self.field_threshold_oe.get())
            interval = float(self.field_check_interval_s.get())
            wait_s = float(self.field_wait_s.get())
            ramp_mode = self.app_mode.get() == "Field Controlled Ramp"
            ready_since = None
            ramp_started = False
            while not self.auto_stop_requested:
                field = self._get_field_oe()
                condition_high = field < threshold
                if not condition_high:
                    ready_since = None
                    ramp_started = False
                    self._apply_current(low)
                    msg = f"Field {field:.3f} Oe above threshold, using LOW {low:.3f} µA"
                else:
                    now = time.time()
                    if ready_since is None:
                        ready_since = now
                    waited = now - ready_since
                    if waited < wait_s:
                        self._apply_current(low)
                        msg = f"Field ready, waiting {wait_s - waited:.1f} s before HIGH/start"
                    else:
                        if ramp_mode:
                            if not ramp_started:
                                completed = self._run_embedded_ramp(stop_condition=self._field_low_condition)
                                ramp_started = completed
                            msg = f"Field {field:.3f} Oe below threshold, ramp active/completed" if ramp_started else f"Field condition changed, ramp reset to LOW"
                        else:
                            self._apply_current(high)
                            msg = f"Field {field:.3f} Oe below threshold, using HIGH {high:.3f} µA"
                self.root.after(0, lambda m=msg: self.target_status.set(m))
                time.sleep(interval)
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror("Field control failed", str(exc)))
            self.root.after(0, lambda: self.target_status.set("Field control error"))
        finally:
            self.auto_running = False
            self.auto_stop_requested = False

    def arm_stability_mode(self):
        if not self._ensure_client():
            return
        if self.ramp_running or self.auto_running:
            messagebox.showinfo("Busy", "Another control mode is already active.")
            return
        self.auto_suspended = False
        self.auto_stop_requested = False
        self.auto_running = True
        self.last_field_points = []
        self.target_status.set("Stability control AUTO enabled")
        self.auto_thread = threading.Thread(target=self._stability_worker, daemon=True)
        self.auto_thread.start()

    def _stability_worker(self):
        try:
            low = float(self.stab_low_uA.get())
            high = float(self.stab_high_uA.get())
            dbdt_threshold = float(self.stab_dbdt_threshold.get())
            max_field = float(self.stab_max_field_oe.get())
            interval = float(self.stab_check_interval_s.get())
            wait_s = float(self.stab_wait_s.get())
            ramp_mode = self.app_mode.get() == "Field Stability Ramp"
            ready_since = None
            ramp_started = False
            while not self.auto_stop_requested:
                field = self._get_field_oe()
                now = time.time()
                self.last_field_points.append((now, field))
                self.last_field_points = self.last_field_points[-2:]

                dbdt = None
                if len(self.last_field_points) == 2:
                    (t1, b1), (t2, b2) = self.last_field_points
                    dt = max(t2 - t1, 1e-9)
                    dbdt = abs((b2 - b1) / dt)

                condition_high = (dbdt is not None and dbdt < dbdt_threshold and field <= max_field)
                if not condition_high:
                    ready_since = None
                    ramp_started = False
                    self._apply_current(low)
                    if field > max_field:
                        msg = f"Field {field:.3f} Oe above max {max_field:.3f} Oe, forcing LOW {low:.3f} µA"
                    elif dbdt is None:
                        msg = "Collecting field points for stability estimate"
                    else:
                        msg = f"|dB/dt| {dbdt:.3f} Oe/s above threshold, using LOW {low:.3f} µA"
                else:
                    if ready_since is None:
                        ready_since = now
                    waited = now - ready_since
                    if waited < wait_s:
                        self._apply_current(low)
                        msg = f"Stability ready, waiting {wait_s - waited:.1f} s before HIGH/start"
                    else:
                        if ramp_mode:
                            if not ramp_started:
                                completed = self._run_embedded_ramp(stop_condition=self._stability_low_condition)
                                ramp_started = completed
                            msg = f"|dB/dt| {dbdt:.3f} Oe/s below threshold, ramp active/completed" if ramp_started else f"Stability condition changed, ramp reset to LOW"
                        else:
                            self._apply_current(high)
                            msg = f"|dB/dt| {dbdt:.3f} Oe/s below threshold, using HIGH {high:.3f} µA"
                self.root.after(0, lambda m=msg: self.target_status.set(m))
                time.sleep(interval)
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror("Stability control failed", str(exc)))
            self.root.after(0, lambda: self.target_status.set("Stability control error"))
        finally:
            self.auto_running = False
            self.auto_stop_requested = False


    def _run_embedded_ramp(self, stop_condition):
        initial = float(self.initial_uA.get())
        final = float(self.final_uA.get())
        duration = float(self.duration_s.get())
        step_interval = float(self.step_interval_s.get())
        ramp_shape = self.ramp_shape.get()
        low_current = self._current_low_value_for_active_mode()
        self._apply_current(initial)
        t0 = time.time()
        while (time.time() - t0) < duration and not self.auto_stop_requested:
            should_stop, reason = stop_condition()
            if should_stop:
                self._apply_current(low_current)
                self.root.after(0, lambda r=reason: self.target_status.set(f"Auto ramp aborted: {r}"))
                return False
            frac = min(max((time.time() - t0) / duration, 0.0), 1.0)
            shaped = self._shape_fraction(frac, ramp_shape, initial, final)
            current = initial + (final - initial) * shaped
            self._apply_current(current)
            self.root.after(0, lambda c=current: self.target_status.set(f"Auto ramp running, target {c:.4f} µA"))
            slept = 0.0
            inner_check_interval = self._active_auto_check_interval()
            while slept < step_interval and not self.auto_stop_requested:
                chunk = min(inner_check_interval, step_interval - slept)
                time.sleep(chunk)
                slept += chunk
                should_stop, reason = stop_condition()
                if should_stop:
                    self._apply_current(low_current)
                    self.root.after(0, lambda r=reason: self.target_status.set(f"Auto ramp aborted: {r}"))
                    return False
        if not self.auto_stop_requested:
            should_stop, reason = stop_condition()
            if should_stop:
                self._apply_current(low_current)
                self.root.after(0, lambda r=reason: self.target_status.set(f"Auto ramp aborted: {r}"))
                return False
            self._apply_current(final)
            return True
        return False

    def _current_low_value_for_active_mode(self) -> float:
        mode = self.app_mode.get()
        if mode in ("Field Controlled", "Field Controlled Ramp"):
            return float(self.field_low_uA.get())
        if mode in ("Field Stability", "Field Stability Ramp"):
            return float(self.stab_low_uA.get())
        return float(self.initial_uA.get())

    def _active_auto_check_interval(self) -> float:
        mode = self.app_mode.get()
        if mode in ("Field Controlled", "Field Controlled Ramp"):
            return max(float(self.field_check_interval_s.get()), 0.1)
        if mode in ("Field Stability", "Field Stability Ramp"):
            return max(float(self.stab_check_interval_s.get()), 0.1)
        return 1.0

    def _field_low_condition(self):
        field = self._get_field_oe()
        threshold = float(self.field_threshold_oe.get())
        if field >= threshold:
            return True, f"field {field:.3f} Oe >= threshold {threshold:.3f} Oe"
        return False, ""

    def _stability_low_condition(self):
        field = self._get_field_oe()
        now = time.time()
        self.last_field_points.append((now, field))
        self.last_field_points = self.last_field_points[-2:]
        max_field = float(self.stab_max_field_oe.get())
        threshold = float(self.stab_dbdt_threshold.get())
        if field > max_field:
            return True, f"field {field:.3f} Oe > max {max_field:.3f} Oe"
        if len(self.last_field_points) < 2:
            return False, ""
        (t1, b1), (t2, b2) = self.last_field_points
        dt = max(t2 - t1, 1e-9)
        dbdt = abs((b2 - b1) / dt)
        if dbdt >= threshold:
            return True, f"|dB/dt| {dbdt:.3f} Oe/s >= threshold {threshold:.3f} Oe/s"
        return False, ""

    def manual_override(self, which: str, source: str):
        if not self._ensure_client():
            return
        try:
            self.stop_auto_mode(silent=True)
            if source == "field":
                current = float(self.field_high_uA.get() if which == "high" else self.field_low_uA.get())
            else:
                current = float(self.stab_high_uA.get() if which == "high" else self.stab_low_uA.get())
            self._apply_current(current)
            self.target_status.set(f"Manual override {which.upper()} applied; auto suspended until re-armed")
        except Exception as exc:
            messagebox.showerror("Manual override failed", str(exc))

    def stop_auto_mode(self, silent: bool = False):
        self.auto_stop_requested = True
        if not silent:
            self.target_status.set("Stopping automatic mode...")

    def _schedule_poll(self):
        self._poll_live_values()
        self.root.after(1000, self._schedule_poll)

    def _poll_live_values(self):
        if self.client is None:
            return
        try:
            if self.backend_name.get() == "PPMS":
                pair = self.client.get_bridge(int(self.channel.get()), fast=bool(self.poll_fast.get()))
                field_data = self.client.get_field()
                current_uA = pair.current_uA
                resistance_ohm = pair.resistance_ohm
                field_oe = float(field_data["field_Oe"])
            else:
                channel = int(self.channel.get())
                resistance_ohm = float(self.mpv_client.resistivity.get_resistance(channel))
                current_uA = float(self.mpv_client.resistivity.get_current(channel))
                field_oe, _status = self.mpv_client.get_field()
            power_uW = (current_uA * 1e-6) ** 2 * resistance_ohm * 1e6
            self.live_current.set(f"{current_uA:.6f}")
            self.live_resistance.set(f"{resistance_ohm:.6f}")
            self.live_power.set(f"{power_uW:.6f}")
            self.live_field.set(f"{field_oe:.6f}")

            dbdt_text = "-"
            if len(self.last_field_points) == 2:
                (t1, b1), (t2, b2) = self.last_field_points
                dt = max(t2 - t1, 1e-9)
                dbdt_text = f"{abs((b2 - b1) / dt):.6f}"
            self.live_dbdt.set(dbdt_text)

            if self.live_status.get().startswith("Connected"):
                self.live_status.set("Connected / polling")
        except Exception as exc:
            self.live_status.set(f"Poll error: {exc}")


def main():
    root = tk.Tk()
    app = BridgeHeaterGUI(root)
    root.update_idletasks()
    root.minsize(root.winfo_reqwidth(), root.winfo_reqheight())
    root.mainloop()


if __name__ == "__main__":
    main()
