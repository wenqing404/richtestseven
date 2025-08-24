from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class CrawlerRequest(BaseModel):
    """Model for crawler request"""
    stock_code: str = Field(..., description="Stock code of the company")
    year: int = Field(..., description="Year of the report")
    report_type: str = Field(..., description="Type of the report (e.g., 年度报告, 半年报, 季报)")

class FileInfo(BaseModel):
    """Model for file information"""
    file_name: str
    file_size: int
    file_path: str
    text_path: Optional[str] = None

class ReportMetadata(BaseModel):
    """Model for report metadata"""
    company_name: str
    stock_code: str
    report_type: str
    report_period: str
    publish_date: str

class CrawlerMetadata(BaseModel):
    """Model for crawler metadata"""
    source: str
    crawl_time: str
    url: str
    status: str
    checksum: Optional[str] = None
    error_message: Optional[str] = None

class CrawlerResponse(BaseModel):
    """Model for crawler response"""
    crawler_metadata: CrawlerMetadata
    report_metadata: Optional[ReportMetadata] = None
    file_info: Optional[FileInfo] = None