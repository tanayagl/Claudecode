"""
PPD resolution pipeline for USB printers that don't support driverless printing.

Resolution order:
  1. Exact make + model match from lpinfo -m
  2. Model-only partial match (catches gutenprint / foomatic entries)
  3. Generic PostScript fallback (works for most laser printers)
  4. None — caller must request a manual PPD upload via the setup UI
"""

import subprocess


def _lpinfo_models(keyword: str | None = None) -> list[str]:
    """
    Return model URIs from `lpinfo -m`, optionally filtered by keyword
    (case-insensitive substring match on the full line).
    """
    result = subprocess.run(
        ["lpinfo", "-m"],
        capture_output=True, text=True, check=False,
    )
    lines = result.stdout.splitlines()
    if keyword:
        kw = keyword.lower()
        lines = [l for l in lines if kw in l.lower()]
    # Each line: "<model-uri>  <human name>" — return just the URI
    return [l.split(None, 1)[0] for l in lines if l.strip()]


def resolve_ppd(make: str, model: str) -> str | None:
    """
    Resolve the best CUPS model URI for a USB printer by make and model string.

    Returns a model URI suitable for `lpadmin -m <uri>`, or None if nothing
    usable is found (caller should surface a manual-upload prompt).
    """
    # Step 1: exact make + model
    matches = _lpinfo_models(f"{make} {model}".strip())
    if matches:
        return matches[0]

    # Step 2: model name only (catches gutenprint / foomatic variants)
    if model:
        matches = _lpinfo_models(model)
        if matches:
            return matches[0]

    # Step 3: generic PostScript — safe default for lasers
    matches = _lpinfo_models("Generic PostScript")
    if matches:
        return matches[0]

    return None
