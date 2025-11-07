"""
Pydantic models for job management in the books data pipeline.

This module defines the data structures for ETL job processing, including
status tracking, error handling, and retry logic.
"""

from enum import Enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Enumeration of possible job statuses."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreate(BaseModel):
    """Model for creating a new job from CSV data."""

    title: str = Field(..., description="Book title")
    author: str = Field(..., description="Book author")
    isbn: Optional[str] = Field(None, description="ISBN identifier")


class JobUpdate(BaseModel):
    """Model for updating an existing job's status and error information."""

    status: JobStatus = Field(..., description="Current job status")
    error_message: Optional[str] = Field(
        None, description="Error message if job failed"
    )
    retry_count: int = Field(0, ge=0, description="Number of retry attempts")


class Job(BaseModel):
    """Model representing a job in the ETL pipeline."""

    title: str = Field(..., description="Book title")
    author: str = Field(..., description="Book author")
    isbn: Optional[str] = Field(None, description="ISBN identifier")
    status: JobStatus = Field(..., description="Current job status")
    error_message: Optional[str] = Field(
        None, description="Error message if job failed"
    )
    retry_count: int = Field(0, ge=0, description="Number of retry attempts")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Job last update timestamp")

    class Config:
        """Pydantic model configuration."""

        from_attributes = True  # Enable reading from ORM objects
