"""STEP 50: Data Integrity schemas."""

from datetime import datetime
from pydantic import BaseModel


class DataQualityRecordResponse(BaseModel):
    device_id: int
    metric: str
    period_start: datetime
    expected_count: int
    received_count: int
    invalid_count: int
    duplicate_count: int
    quality_score: float
    model_config = {"from_attributes": True}


class ReconciliationResponse(BaseModel):
    id: int
    factory_id: int
    period_start: datetime
    period_end: datetime
    generation_kwh: float
    consumption_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float
    difference_kwh: float
    tolerance_kwh: float
    status: str
    model_config = {"from_attributes": True}


class DataAnomalyResponse(BaseModel):
    id: int
    device_id: int | None
    factory_id: int
    metric: str
    type: str
    severity: str
    detected_value: float | None
    expected_value: float | None
    status: str
    detected_at: datetime
    model_config = {"from_attributes": True}


class DataCorrectionResponse(BaseModel):
    id: int
    device_id: int
    metric: str
    timestamp: datetime
    old_value: float
    new_value: float
    reason: str
    corrected_by: int
    created_at: datetime
    model_config = {"from_attributes": True}


class FactoryDataHealthResponse(BaseModel):
    factory_id: int
    total_devices: int
    online_devices: int
    data_quality_pct: float
    missing_pct: float
    anomaly_count: int
    reconciliation_status: str
