from fastapi import APIRouter, Request, Form, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
import markdown

from app.services.analysis_service import FinancialReportAnalyzer

router = APIRouter(prefix="/analysis", tags=["analysis"])
templates = Jinja2Templates(directory="templates")

# Initialize the analyzer service
analyzer = FinancialReportAnalyzer(data_dir="data")

@router.get("/")
async def analysis_page(request: Request):
    """Render the analysis page"""
    return templates.TemplateResponse("analysis.html", {"request": request})

@router.post("/basic")
async def basic_analysis(
    stock_code: str = Form(...),
    year: int = Form(...),
    report_type: str = Form(...)
):
    """Perform basic analysis on a financial report"""
    try:
        # Validate input
        if not stock_code or not year or not report_type:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Perform analysis using the analyzer service
        analysis_result = analyzer.analyze_report(stock_code, year, report_type)
        
        if analysis_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=analysis_result.get("message", "Analysis failed"))
            
        # Handle supplementary announcements
        if analysis_result.get("status") == "partial" and analysis_result.get("report_type") == "补充公告":
            # We'll still process it, but mark it as a supplementary announcement
            pass
        
        # Generate analysis summary
        summary = analyzer.generate_analysis_summary(analysis_result)
        
        # Add the summary to the result
        analysis_result["summary"] = summary
        
        # Add basic text info for backward compatibility
        report_folder = Path("data") / stock_code / str(year)
        text_path = report_folder / f"{stock_code}_{year}_{report_type.replace('报告', '')}.txt"
        
        if text_path.exists():
            with open(text_path, "r", encoding="utf-8") as f:
                text_content = f.read()
            
            analysis_result["report_info"] = {
                "stock_code": stock_code,
                "year": year,
                "report_type": report_type,
                "text_length": len(text_content),
                "preview": text_content[:500] + "..." if len(text_content) > 500 else text_content
            }
        
        return JSONResponse(content=analysis_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/{stock_code}/{year}/{report_type}")
async def get_analysis_summary(
    stock_code: str,
    year: int,
    report_type: str,
    format: str = Query("html", description="Output format: html or text")
):
    """Get a summary of the financial report analysis"""
    try:
        # Perform analysis
        analysis_result = analyzer.analyze_report(stock_code, year, report_type)
        
        if analysis_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=analysis_result.get("message", "Analysis failed"))
            
        # Handle supplementary announcements - we'll still process it, but it will be marked as a supplementary announcement
        pass
        
        # Generate summary
        summary = analyzer.generate_analysis_summary(analysis_result)
        
        if format.lower() == "html":
            # Convert markdown to HTML
            html_content = markdown.markdown(summary)
            return HTMLResponse(content=html_content)
        else:
            return JSONResponse(content={"summary": summary})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/json/{stock_code}/{year}/{report_type}")
async def get_analysis_json(
    stock_code: str,
    year: int,
    report_type: str
):
    """Get the full JSON analysis of a financial report"""
    try:
        # Perform analysis
        analysis_result = analyzer.analyze_report(stock_code, year, report_type)
        
        if analysis_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=analysis_result.get("message", "Analysis failed"))
            
        # Handle supplementary announcements - we'll still process it, but it will be marked as a supplementary announcement
        pass
        
        return JSONResponse(content=analysis_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))