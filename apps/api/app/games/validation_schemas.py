"""Pydantic schemas for validation endpoints."""

from datetime import datetime

from pydantic import BaseModel


class ValidationRunResponse(BaseModel):
    id: str
    game_version_id: str
    status: str
    scan_passed: bool | None = None
    report_json_path: str | None = None
    screenshot_path: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ValidationCreatedResponse(BaseModel):
    validation_id: str
    status: str
    message: str


class ScanFindingResponse(BaseModel):
    line: int
    pattern: str
    severity: str
    message: str


class ScanResultResponse(BaseModel):
    passed: bool
    findings: list[ScanFindingResponse]
    critical_count: int
    high_count: int
