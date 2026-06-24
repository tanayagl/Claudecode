from typing import Dict, Optional
from models import Printer, PrintJob, PrinterStatus, JobStatus


class InMemoryStore:
    def __init__(self):
        self._printers: Dict[str, Printer] = {}
        self._jobs: Dict[str, PrintJob] = {}

    # --- Printers ---

    def add_printer(self, printer: Printer) -> Printer:
        self._printers[printer.id] = printer
        return printer

    def get_printer(self, printer_id: str) -> Optional[Printer]:
        return self._printers.get(printer_id)

    def list_printers(self) -> list[Printer]:
        return list(self._printers.values())

    def update_printer_status(self, printer_id: str, status: PrinterStatus) -> Optional[Printer]:
        printer = self._printers.get(printer_id)
        if printer:
            self._printers[printer_id] = printer.model_copy(update={"status": status})
            return self._printers[printer_id]
        return None

    def delete_printer(self, printer_id: str) -> bool:
        return self._printers.pop(printer_id, None) is not None

    # --- Jobs ---

    def add_job(self, job: PrintJob) -> PrintJob:
        self._jobs[job.id] = job
        return job

    def get_job(self, job_id: str) -> Optional[PrintJob]:
        return self._jobs.get(job_id)

    def list_jobs(self, printer_id: Optional[str] = None, status: Optional[JobStatus] = None) -> list[PrintJob]:
        jobs = list(self._jobs.values())
        if printer_id:
            jobs = [j for j in jobs if j.printer_id == printer_id]
        if status:
            jobs = [j for j in jobs if j.status == status]
        return sorted(jobs, key=lambda j: (-j.priority, j.submitted_at))

    def update_job(self, job: PrintJob) -> PrintJob:
        self._jobs[job.id] = job
        return job

    def delete_job(self, job_id: str) -> bool:
        return self._jobs.pop(job_id, None) is not None


store = InMemoryStore()
