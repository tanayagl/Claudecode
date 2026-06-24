import asyncio
import logging
from datetime import datetime
from models import JobStatus, PrinterStatus
from store import store

logger = logging.getLogger(__name__)


async def process_next_job():
    """Pick the highest-priority queued job for an online printer and "print" it."""
    queued = store.list_jobs(status=JobStatus.QUEUED)
    for job in queued:
        printer = store.get_printer(job.printer_id)
        if printer and printer.status == PrinterStatus.ONLINE:
            # Mark printer busy and job printing
            store.update_printer_status(printer.id, PrinterStatus.BUSY)
            updated = job.model_copy(update={
                "status": JobStatus.PRINTING,
                "started_at": datetime.utcnow(),
            })
            store.update_job(updated)
            logger.info(f"Printing job {job.id} ({job.document_name}) on printer {printer.name}")

            # Simulate print time: 0.5s per page per copy
            await asyncio.sleep(0.5 * job.pages * job.copies)

            finished = store.get_job(job.id)
            if finished and finished.status == JobStatus.PRINTING:
                store.update_job(finished.model_copy(update={
                    "status": JobStatus.COMPLETED,
                    "completed_at": datetime.utcnow(),
                }))
                logger.info(f"Job {job.id} completed")

            store.update_printer_status(printer.id, PrinterStatus.ONLINE)
            return


async def queue_worker():
    """Background loop that continuously processes print jobs."""
    while True:
        try:
            await process_next_job()
        except Exception as exc:
            logger.error(f"Queue worker error: {exc}")
        await asyncio.sleep(1)
