from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class PrinterStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"


class JobStatus(str, Enum):
    QUEUED = "queued"
    PRINTING = "printing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(int, Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 10


class Printer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    location: Optional[str] = None
    status: PrinterStatus = PrinterStatus.ONLINE
    capabilities: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PrintJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    printer_id: str
    document_name: str
    content: str
    copies: int = Field(default=1, ge=1, le=100)
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.QUEUED
    submitted_by: Optional[str] = None
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    pages: int = Field(default=1, ge=1)


class CreatePrinterRequest(BaseModel):
    name: str
    location: Optional[str] = None
    capabilities: list[str] = Field(default_factory=list)


class SubmitJobRequest(BaseModel):
    printer_id: str
    document_name: str
    content: str
    copies: int = Field(default=1, ge=1, le=100)
    priority: JobPriority = JobPriority.NORMAL
    submitted_by: Optional[str] = None
    pages: int = Field(default=1, ge=1)
