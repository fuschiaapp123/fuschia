from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ServiceNowTable(BaseModel):
    label: str
    name: str
    primary: str


class ServiceNowColumn(BaseModel):
    element: str
    column_label: str


class ServiceNowRecord(BaseModel):
    data: Dict[str, Any]


class ServiceNowTableResponse(BaseModel):
    tables: List[ServiceNowTable]


class ServiceNowColumnsResponse(BaseModel):
    columns: List[ServiceNowColumn]


class ServiceNowRecordsResponse(BaseModel):
    records: List[Dict[str, Any]]
    total: Optional[int] = None
    page: Optional[int] = None
    size: Optional[int] = None


class ServiceNowExportRequest(BaseModel):
    table: str
    fields: Optional[str] = None
    filters: Optional[str] = None
    limit: Optional[int] = 100


class ServiceNowExportResponse(BaseModel):
    message: str
    exported_count: int
    table_name: str


class ServiceNowConnectionStatus(BaseModel):
    connected: bool
    message: str
    instance_url: Optional[str] = None
    tables_count: Optional[int] = None