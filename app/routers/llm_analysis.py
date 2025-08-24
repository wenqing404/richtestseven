"""
LLM-based financial report analysis router.
基于大语言模型的财报分析路由
"""

import os
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Form, Query, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path

from app.services.crawler_service import CrawlerService
from app.services.llm_analysis_service import LLMAnalysisService
from app.models.crawler_models import CrawlerRequest

# 加载环境变量
load_dotenv()

# 创建路由
router = APIRouter(
    prefix="/llm-analysis",
    tags=["llm-analysis"],
    responses={404: {"description": "Not found"}},
)

# 初始化模板引擎
templates = Jinja2Templates(directory="templates")

# 初始化服务
crawler_service = CrawlerService()

# 从环境变量获取API密钥，如果没有则使用默认值（实际使用时应当配置真实的API密钥）
api_key = os.environ.get("DEEPSEEK_API_KEY", "")
default_model = os.environ.get("DEFAULT_LLM_MODEL", "deepseek-chat")
llm_analyzer = LLMAnalysisService(api_key=api_key, model_name=default_model)


class LLMAnalysisRequest(BaseModel):
    """LLM分析请求模型"""
    stock_code: str
    year: int
    report_type: str = "年度报告"
    model_name: Optional[str] = "deepseek-chat"


@router.get("/", response_class=HTMLResponse)
async def get_llm_analysis_page(request: Request):
    """获取LLM分析页面"""
    return templates.TemplateResponse(
        "llm_analysis.html", 
        {"request": request, "title": "智能财报分析"}
    )


@router.post("/analyze")
async def analyze_report(analysis_request: LLMAnalysisRequest):
    """使用LLM分析财报，直接从已爬取的数据中获取内容"""
    try:
        # 构建文件路径，类似于 analysis.py 中的逻辑
        report_folder = Path("data") / analysis_request.stock_code / str(analysis_request.year)
        text_path = report_folder / f"{analysis_request.stock_code}_{analysis_request.year}_{analysis_request.report_type.replace('报告', '')}.txt"
        
        # 检查文件是否存在
        if not text_path.exists():
            # 如果文件不存在，则尝试爬取
            crawl_request = CrawlerRequest(
                stock_code=analysis_request.stock_code,
                year=analysis_request.year,
                report_type=analysis_request.report_type
            )
            
            # 爬取财报
            crawl_result = crawler_service.crawl_report(
                crawl_request.stock_code,
                crawl_request.year,
                crawl_request.report_type
            )
            
            if crawl_result.get("status") == "failed":
                raise HTTPException(status_code=404, detail=crawl_result.get("error_message", "财报获取失败"))
            
            # 提取财报内容
            report_content = crawl_result.get("report_content", "")
            company_name = crawl_result.get("basic_info", {}).get("company_name", "")
        else:
            # 如果文件存在，直接读取内容
            with open(text_path, "r", encoding="utf-8") as f:
                report_content = f.read()
            
            # 尝试读取元数据文件以获取公司名称
            metadata_path = report_folder / f"{analysis_request.stock_code}_{analysis_request.year}_{analysis_request.report_type.replace('报告', '')}_meta.json"
            company_name = ""
            if metadata_path.exists():
                try:
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                        company_name = metadata.get("report_metadata", {}).get("company_name", "")
                except json.JSONDecodeError:
                    pass
        
        if not report_content:
            raise HTTPException(status_code=404, detail="财报内容为空")
        
        # 准备公司信息
        company_info = {
            "company_name": company_name,
            "stock_code": analysis_request.stock_code,
            "report_period": f"{analysis_request.year}年{analysis_request.report_type}"
        }
        
        # 使用LLM分析财报
        # 如果用户指定了模型，则使用指定的模型
        model_to_use = analysis_request.model_name if analysis_request.model_name else default_model
        if model_to_use != llm_analyzer.model_name:
            llm_analyzer.model_name = model_to_use
        print(f"使用模型: {llm_analyzer.model_name}")
            
        analysis_result = llm_analyzer.analyze_financial_report(report_content, company_info)
        
        if analysis_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=analysis_result.get("message", "分析失败"))
        
        # 添加报告基本信息
        analysis_result["report_info"] = {
            "stock_code": analysis_request.stock_code,
            "year": analysis_request.year,
            "report_type": analysis_request.report_type,
            "company_name": company_info["company_name"],
            "report_period": company_info["report_period"],
            "text_length": len(report_content),
            "preview": report_content[:500] + "..." if len(report_content) > 500 else report_content
        }
        
        return JSONResponse(content=analysis_result)
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/investment-advice")
async def get_investment_advice(analysis_result: Dict[str, Any]):
    """基于分析结果获取投资建议"""
    try:
        # 使用LLM生成投资建议
        investment_advice = llm_analyzer.generate_investment_advice(analysis_result)
        
        if investment_advice.get("status") == "error":
            raise HTTPException(status_code=500, detail=investment_advice.get("message", "生成投资建议失败"))
        
        return JSONResponse(content=investment_advice)
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_reports(
    current_stock_code: str = Form(...),
    current_year: int = Form(...),
    current_report_type: str = Form("年度报告"),
    previous_stock_code: str = Form(...),
    previous_year: int = Form(...),
    previous_report_type: str = Form("年度报告"),
    model_name: str = Form("deepseek-chat")
):
    """比较两期财报"""
    try:
        # 分析当期财报
        current_request = LLMAnalysisRequest(
            stock_code=current_stock_code,
            year=current_year,
            report_type=current_report_type,
            model_name=model_name
        )
        current_analysis = await analyze_report(current_request)
        current_result = current_analysis.body
        
        # 分析上期财报
        previous_request = LLMAnalysisRequest(
            stock_code=previous_stock_code,
            year=previous_year,
            report_type=previous_report_type,
            model_name=model_name
        )
        previous_analysis = await analyze_report(previous_request)
        previous_result = previous_analysis.body
        
        # 比较两期财报
        comparison_result = llm_analyzer.compare_reports(
            json.loads(current_result),
            json.loads(previous_result)
        )
        
        if comparison_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=comparison_result.get("message", "比较分析失败"))
        
        return JSONResponse(content=comparison_result)
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_available_models():
    """获取可用的LLM模型列表"""
    # 从环境变量获取可用的模型列表，如果没有则使用默认列表
    try:
        # 获取 DeepSeek 的可用模型
        models = [
            {"id": "deepseek-chat", 
             "name": "DeepSeek Chat", 
             "description": "DeepSeek 通用聊天模型，适用于财报分析和投资建议"},
            {"id": "deepseek-coder", 
             "name": "DeepSeek Coder", 
             "description": "DeepSeek 代码专用模型，适用于技术分析"},
            {"id": "deepseek-llm", 
             "name": "DeepSeek LLM", 
             "description": "DeepSeek 基础大语言模型"}
        ]
        
        # 添加一些可能的替代模型
        additional_models = os.environ.get("ADDITIONAL_LLM_MODELS", "")
        if additional_models:
            try:
                additional_models_list = json.loads(additional_models)
                models.extend(additional_models_list)
            except json.JSONDecodeError:
                pass
    except Exception as e:
        # 出错时使用默认列表
        models = [
            {"id": "deepseek-chat", 
             "name": "DeepSeek Chat", 
             "description": "DeepSeek 通用聊天模型，适用于财报分析和投资建议"}
        ]
    
    return JSONResponse(content={"models": models})
