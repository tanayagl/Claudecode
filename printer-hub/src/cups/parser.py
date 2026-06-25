import re


def parse_lpinfo_v(output: str) -> list[dict]:
    """
    Parse `lpinfo -v` output into device records.

    Each line is "<type> <uri>" e.g.:
        direct  usb://Canon/LBP6030%20Series?serial=ABC&interface=1
        network ipp
    Returns [{"scheme": str, "uri": str}, ...]
    """
    devices = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        devices.append({
            "scheme": parts[0],
            "uri": parts[1] if len(parts) == 2 else "",
        })
    return devices


# "printer <name> is idle."  /  "is printing."  /  "is stopped."
_PRINTER_STATE_RE = re.compile(
    r"^printer\s+(\S+)\s+is\s+(idle|printing|stopped)"
)


def parse_lpstat_p(output: str) -> list[dict]:
    """
    Parse `lpstat -p` output into printer state records.
    Returns [{"name": str, "state": "idle"|"printing"|"stopped"}, ...]
    """
    statuses = []
    for line in output.splitlines():
        m = _PRINTER_STATE_RE.match(line.strip())
        if m:
            statuses.append({"name": m.group(1), "state": m.group(2)})
    return statuses


# "<printer>-<id>  <user>  <size>  <timestamp...>"
_JOB_RE = re.compile(r"^(\S+)-(\d+)\s+(\S+)\s+(\d+)\s+(.+)$")


def parse_lpstat_o(output: str) -> list[dict]:
    """
    Parse `lpstat -o [printer]` output into job records.
    Returns [{"job_id": str, "printer": str, "user": str, "size_bytes": int, "submitted_at": str}, ...]
    """
    jobs = []
    for line in output.splitlines():
        m = _JOB_RE.match(line.strip())
        if m:
            jobs.append({
                "job_id": f"{m.group(1)}-{m.group(2)}",
                "printer": m.group(1),
                "user": m.group(3),
                "size_bytes": int(m.group(4)),
                "submitted_at": m.group(5).strip(),
            })
    return jobs
