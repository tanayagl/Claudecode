"""
Thin wrappers around CUPS CLI tools (lpadmin, lp, cancel, lpstat, lpinfo).

All callers outside this module go through these functions — nothing else
shells out to CUPS directly. Raises subprocess.CalledProcessError on failure
so the caller can decide whether to retry or surface the error.
"""

import subprocess
from pathlib import Path

from cups.parser import parse_lpinfo_v, parse_lpstat_o, parse_lpstat_p


def _run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, check=check)


# ---------------------------------------------------------------------------
# Device discovery
# ---------------------------------------------------------------------------

def list_usb_devices() -> list[dict]:
    """Return USB printer devices visible to CUPS (lpinfo -v, scheme=usb/direct)."""
    result = _run(["lpinfo", "-v"])
    return [
        d for d in parse_lpinfo_v(result.stdout)
        if d["scheme"] in ("direct", "usb") and d["uri"].startswith("usb://")
    ]


# ---------------------------------------------------------------------------
# Printer management
# ---------------------------------------------------------------------------

def add_printer(name: str, uri: str, ppd: str | None = None) -> None:
    """
    Add a printer to CUPS.

    ppd — a CUPS model URI (e.g. "drv:///...") passed via -m,
          a filesystem PPD path passed via -P,
          or None to attempt driverless IPP Everywhere (-m everywhere).

    Raises CalledProcessError if CUPS rejects the printer (e.g. driverless
    unsupported). Caller should catch and retry with a resolved PPD.
    """
    cmd = ["lpadmin", "-p", name, "-E", "-v", uri]
    if ppd is None:
        cmd += ["-m", "everywhere"]
    elif ppd.startswith("drv://") or ppd.startswith("lsb://") or ppd.startswith("foomatic"):
        cmd += ["-m", ppd]
    else:
        cmd += ["-P", ppd]
    _run(cmd)


def remove_printer(name: str) -> None:
    _run(["lpadmin", "-x", name])


def set_shared(name: str, shared: bool = True) -> None:
    """Toggle Bonjour/mDNS sharing for the printer via CUPS + Avahi."""
    value = "true" if shared else "false"
    _run(["lpadmin", "-p", name, "-o", f"printer-is-shared={value}"])


def enable_printer(name: str) -> None:
    _run(["cupsenable", name])


def disable_printer(name: str) -> None:
    _run(["cupsdisable", name])


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

def get_printer_statuses() -> list[dict]:
    """Return current state of all CUPS printers. Returns [] if CUPS has none."""
    result = _run(["lpstat", "-p"], check=False)
    return parse_lpstat_p(result.stdout)


def cups_is_alive() -> bool:
    """Return True if the CUPS scheduler is running and reachable."""
    try:
        result = _run(["lpstat", "-r"], check=False)
        return "scheduler is running" in result.stdout.lower()
    except FileNotFoundError:
        return False


# ---------------------------------------------------------------------------
# Job management
# ---------------------------------------------------------------------------

def submit_job(
    printer_name: str,
    file_path: Path,
    copies: int = 1,
    title: str | None = None,
) -> str:
    """
    Submit a print job. Returns the CUPS job ID string (e.g. "MyPrinter-3").
    file_path must exist on the hub filesystem.
    """
    cmd = ["lp", "-d", printer_name, "-n", str(copies)]
    if title:
        cmd += ["-t", title]
    cmd.append(str(file_path))
    result = _run(cmd)
    # Output: "request id is <printer>-<n> (1 file(s))"
    parts = result.stdout.strip().split()
    return parts[3] if len(parts) >= 4 else ""


def cancel_job(job_id: str) -> None:
    _run(["cancel", job_id], check=False)


def cancel_all_jobs(printer_name: str) -> None:
    _run(["cancel", "-a", printer_name], check=False)


def list_jobs(printer_name: str | None = None) -> list[dict]:
    cmd = ["lpstat", "-o"]
    if printer_name:
        cmd.append(printer_name)
    result = _run(cmd, check=False)
    return parse_lpstat_o(result.stdout)
