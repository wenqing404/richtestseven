from fastapi import APIRouter, Request, Form, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
import os

from app.services.crawler_service import FinancialReportCrawler
from app.models.crawler_models import CrawlerRequest, CrawlerResponse

router = APIRouter(prefix="/crawler", tags=["crawler"])
templates = Jinja2Templates(directory="templates")

# Initialize the crawler service
crawler = FinancialReportCrawler(output_dir="data")

@router.get("/")
async def crawler_page(request: Request):
    """Render the crawler page"""
    return templates.TemplateResponse("crawler.html", {"request": request})

@router.post("/crawl")
async def crawl_report(
    background_tasks: BackgroundTasks,
    stock_code: str = Form(...),
    year: int = Form(...),
    report_type: str = Form(...)
):
    """API endpoint to crawl a financial report"""
    try:
        # Validate input
        if not stock_code or not year or not report_type:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Start crawling in the background
        background_tasks.add_task(
            crawler.crawl_annual_report_from_cninfo,
            stock_code=stock_code,
            year=year,
            report_type=report_type
        )
        
        return JSONResponse(
            status_code=202,
            content={
                "message": f"Crawling started for {stock_code} {year} {report_type}",
                "status": "processing"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{stock_code}/{year}/{report_type}")
async def check_status(stock_code: str, year: int, report_type: str):
    """Check the status of a crawling task"""
    try:
        # Construct the path to the metadata file
        report_folder = Path("data") / stock_code / str(year)
        metadata_path = report_folder / f"{stock_code}_{year}_{report_type.replace('报告', '')}_metadata.json"
        
        if metadata_path.exists():
            # Read the metadata file
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            return JSONResponse(
                content={
                    "status": "completed",
                    "metadata": metadata
                }
            )
        else:
            # Check if the task is still in progress
            return JSONResponse(
                content={
                    "status": "processing",
                    "message": f"Still processing {stock_code} {year} {report_type}"
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{stock_code}/{year}/{report_type}")
async def download_report(stock_code: str, year: int, report_type: str):
    """Download a financial report"""
    try:
        # Construct the path to the PDF file
        report_folder = Path("data") / stock_code / str(year)
        file_name = f"{stock_code}_{year}_{report_type.replace('报告', '')}.pdf"
        pdf_path = report_folder / file_name
        
        if pdf_path.exists():
            return FileResponse(
                path=str(pdf_path),
                filename=file_name,
                media_type="application/pdf"
            )
        else:
            raise HTTPException(status_code=404, detail="Report not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_reports():
    """List all available reports"""
    try:
        data_dir = Path("data")
        if not data_dir.exists():
            return JSONResponse(content={"reports": []})
        
        reports = []
        
        # Walk through the data directory
        for company_dir in data_dir.iterdir():
            if company_dir.is_dir():
                stock_code = company_dir.name
                
                for year_dir in company_dir.iterdir():
                    if year_dir.is_dir():
                        year = year_dir.name
                        
                        # Find all metadata files
                        for metadata_file in year_dir.glob("*_metadata.json"):
                            with open(metadata_file, "r", encoding="utf-8") as f:
                                metadata = json.load(f)
                            
                            reports.append(metadata)
        
        return JSONResponse(content={"reports": reports})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/text/{stock_code}/{year}/{report_type}")
async def get_report_text(stock_code: str, year: int, report_type: str):
    """Get the extracted text from a financial report"""
    try:
        # Construct the path to the text file
        report_folder = Path("data") / stock_code / str(year)
        text_path = report_folder / f"{stock_code}_{year}_{report_type.replace('报告', '')}.txt"
        
        if text_path.exists():
            with open(text_path, "r", encoding="utf-8") as f:
                text_content = f.read()
            
            return JSONResponse(
                content={
                    "text": text_content
                }
            )
        else:
            # Try to extract text from PDF if text file doesn't exist
            pdf_path = report_folder / f"{stock_code}_{year}_{report_type.replace('报告', '')}.pdf"
            
            if pdf_path.exists():
                text_content = crawler.extract_text_from_pdf(pdf_path)
                
                if text_content:
                    return JSONResponse(
                        content={
                            "text": text_content
                        }
                    )
                else:
                    raise HTTPException(status_code=500, detail="Failed to extract text from PDF")
            else:
                raise HTTPException(status_code=404, detail="Report not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))