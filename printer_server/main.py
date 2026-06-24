import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from models import (
    CreatePrinterRequest,
    JobStatus,
    PrinterStatus,
    PrintJob,
    SubmitJobRequest,
)
from queue_worker import queue_worker
from store import store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(queue_worker())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Printer Server",
    description="REST API for managing printers and print jobs",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Printers
# ---------------------------------------------------------------------------

@app.post("/printers", status_code=201, tags=["Printers"])
def create_printer(req: CreatePrinterRequest):
    from models import Printer
    printer = store.add_printer(Printer(**req.model_dump()))
    return printer


@app.get("/printers", tags=["Printers"])
def list_printers():
    return store.list_printers()


@app.get("/printers/{printer_id}", tags=["Printers"])
def get_printer(printer_id: str):
    printer = store.get_printer(printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    return printer


@app.patch("/printers/{printer_id}/status", tags=["Printers"])
def update_printer_status(printer_id: str, status: PrinterStatus):
    printer = store.update_printer_status(printer_id, status)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    return printer


@app.delete("/printers/{printer_id}", status_code=204, tags=["Printers"])
def delete_printer(printer_id: str):
    active = store.list_jobs(printer_id=printer_id, status=JobStatus.PRINTING)
    if active:
        raise HTTPException(status_code=409, detail="Printer has active jobs")
    if not store.delete_printer(printer_id):
        raise HTTPException(status_code=404, detail="Printer not found")


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

@app.post("/jobs", status_code=201, tags=["Jobs"])
def submit_job(req: SubmitJobRequest):
    printer = store.get_printer(req.printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    if printer.status == PrinterStatus.OFFLINE:
        raise HTTPException(status_code=409, detail="Printer is offline")

    job = store.add_job(PrintJob(**req.model_dump()))
    return job


@app.get("/jobs", tags=["Jobs"])
def list_jobs(
    printer_id: Optional[str] = Query(default=None),
    status: Optional[JobStatus] = Query(default=None),
):
    return store.list_jobs(printer_id=printer_id, status=status)


@app.get("/jobs/{job_id}", tags=["Jobs"])
def get_job(job_id: str):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/jobs/{job_id}/cancel", tags=["Jobs"])
def cancel_job(job_id: str):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in (JobStatus.QUEUED,):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel a job in '{job.status}' state",
        )
    updated = job.model_copy(update={"status": JobStatus.CANCELLED})
    return store.update_job(updated)


@app.delete("/jobs/{job_id}", status_code=204, tags=["Jobs"])
def delete_job(job_id: str):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status == JobStatus.PRINTING:
        raise HTTPException(status_code=409, detail="Cannot delete a job that is currently printing")
    store.delete_job(job_id)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
