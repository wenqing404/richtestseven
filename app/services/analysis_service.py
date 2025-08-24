import re
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

# 导入LLM服务
from app.services.llm_service import LLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("financial_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FinancialReportAnalysis")

class FinancialReportAnalyzer:
    """财务报告分析类"""
    
    def __init__(self, data_dir: str = "./data", llm_api_key: Optional[str] = None):
        self.data_dir = Path(data_dir)
        
        # 初始化LLM服务
        self.llm_service = LLMService(api_key=llm_api_key)
        self.use_llm = os.environ.get("USE_LLM", "false").lower() == "true" or llm_api_key is not None
    
    def get_report_text(self, stock_code: str, year: int, report_type: str) -> Optional[str]:
        """获取报告文本内容"""
        try:
            # 构造文本文件路径
            report_folder = self.data_dir / stock_code / str(year)
            text_path = report_folder / f"{stock_code}_{year}_{report_type.replace('报告', '')}.txt"
            
            if not text_path.exists():
                logger.error(f"报告文本文件不存在: {text_path}")
                return None
            
            # 读取文本内容
            with open(text_path, "r", encoding="utf-8") as f:
                text_content = f.read()
            
            return text_content
        except Exception as e:
            logger.error(f"获取报告文本时出错: {str(e)}")
            return None
    
    def get_report_metadata(self, stock_code: str, year: int, report_type: str) -> Optional[Dict[str, Any]]:
        """获取报告元数据"""
        try:
            # 构造元数据文件路径
            report_folder = self.data_dir / stock_code / str(year)
            metadata_path = report_folder / f"{stock_code}_{year}_{report_type.replace('报告', '')}_metadata.json"
            
            if not metadata_path.exists():
                logger.error(f"报告元数据文件不存在: {metadata_path}")
                return None
            
            # 读取元数据
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            return metadata
        except Exception as e:
            logger.error(f"获取报告元数据时出错: {str(e)}")
            return None
    
    def extract_net_profit(self, text: str) -> Tuple[Optional[float], Optional[float]]:
        """提取归母净利润及同比变化"""
        try:
            # 尝试匹配归母净利润
            net_profit_patterns = [
                r"归属于上市公司股东的净利润[^\d]*([\d,\.]+)[^\d%]*?元",
                r"归属于母公司所有者的净利润[^\d]*([\d,\.]+)[^\d%]*?元",
                r"归属于母公司股东的净利润[^\d]*([\d,\.]+)[^\d%]*?元",
                r"归母净利润[^\d]*([\d,\.]+)[^\d%]*?元"
            ]
            
            net_profit = None
            for pattern in net_profit_patterns:
                match = re.search(pattern, text)
                if match:
                    net_profit_str = match.group(1).replace(',', '')
                    net_profit = float(net_profit_str)
                    break
            
            # 尝试匹配同比变化
            yoy_patterns = [
                r"归属于上市公司股东的净利润[^%]*同比[增减变动]*[^\d-]*([-\d\.]+)%",
                r"归属于母公司所有者的净利润[^%]*同比[增减变动]*[^\d-]*([-\d\.]+)%",
                r"归属于母公司股东的净利润[^%]*同比[增减变动]*[^\d-]*([-\d\.]+)%",
                r"归母净利润[^%]*同比[增减变动]*[^\d-]*([-\d\.]+)%"
            ]
            
            net_profit_yoy = None
            for pattern in yoy_patterns:
                match = re.search(pattern, text)
                if match:
                    net_profit_yoy = float(match.group(1))
                    break
            
            return net_profit, net_profit_yoy
        except Exception as e:
            logger.error(f"提取归母净利润时出错: {str(e)}")
            return None, None
    
    def extract_revenue(self, text: str) -> Tuple[Optional[float], Optional[float]]:
        """提取营业总收入及同比变化"""
        try:
            # 尝试匹配营业总收入
            revenue_patterns = [
                r"营业总收入[^\d]*([\d,\.]+)[^\d%]*?元",
                r"营业收入[^\d]*([\d,\.]+)[^\d%]*?元",
                r"总收入[^\d]*([\d,\.]+)[^\d%]*?元"
            ]
            
            revenue = None
            for pattern in revenue_patterns:
                match = re.search(pattern, text)
                if match:
                    revenue_str = match.group(1).replace(',', '')
                    revenue = float(revenue_str)
                    break
            
            # 尝试匹配同比变化
            yoy_patterns = [
                r"营业总收入[^%]*同比[增减变动]*[^\d-]*([-\d\.]+)%",
                r"营业收入[^%]*同比[增减变动]*[^\d-]*([-\d\.]+)%",
                r"总收入[^%]*同比[增减变动]*[^\d-]*([-\d\.]+)%"
            ]
            
            revenue_yoy = None
            for pattern in yoy_patterns:
                match = re.search(pattern, text)
                if match:
                    revenue_yoy = float(match.group(1))
                    break
            
            return revenue, revenue_yoy
        except Exception as e:
            logger.error(f"提取营业总收入时出错: {str(e)}")
            return None, None
    
    def extract_cash_flow(self, text: str) -> Dict[str, Optional[float]]:
        """提取现金流量数据"""
        try:
            cash_flow = {
                "operating": None,
                "investing": None,
                "financing": None
            }
            
            # 经营活动现金流
            operating_patterns = [
                r"经营活动[产生|获得]的现金流量净额[^\d]*([-\d,\.]+)[^\d%]*?元",
                r"经营活动现金流量净额[^\d]*([-\d,\.]+)[^\d%]*?元"
            ]
            
            for pattern in operating_patterns:
                match = re.search(pattern, text)
                if match:
                    operating_str = match.group(1).replace(',', '')
                    cash_flow["operating"] = float(operating_str)
                    break
            
            # 投资活动现金流
            investing_patterns = [
                r"投资活动[产生|使用]的现金流量净额[^\d]*([-\d,\.]+)[^\d%]*?元",
                r"投资活动现金流量净额[^\d]*([-\d,\.]+)[^\d%]*?元"
            ]
            
            for pattern in investing_patterns:
                match = re.search(pattern, text)
                if match:
                    investing_str = match.group(1).replace(',', '')
                    cash_flow["investing"] = float(investing_str)
                    break
            
            # 筹资活动现金流
            financing_patterns = [
                r"筹资活动[产生|使用]的现金流量净额[^\d]*([-\d,\.]+)[^\d%]*?元",
                r"筹资活动现金流量净额[^\d]*([-\d,\.]+)[^\d%]*?元"
            ]
            
            for pattern in financing_patterns:
                match = re.search(pattern, text)
                if match:
                    financing_str = match.group(1).replace(',', '')
                    cash_flow["financing"] = float(financing_str)
                    break
            
            return cash_flow
        except Exception as e:
            logger.error(f"提取现金流量数据时出错: {str(e)}")
            return {
                "operating": None,
                "investing": None,
                "financing": None
            }
    
    def extract_profitability(self, text: str) -> Dict[str, Optional[float]]:
        """提取盈利能力指标"""
        try:
            profitability = {
                "roe": None,
                "roa": None,
                "gross_margin": None,
                "net_margin": None
            }
            
            # ROE
            roe_patterns = [
                r"净资产收益率[^\d]*([\d\.]+)%",
                r"ROE[^\d]*([\d\.]+)%",
                r"加权平均净资产收益率[^\d]*([\d\.]+)%"
            ]
            
            for pattern in roe_patterns:
                match = re.search(pattern, text)
                if match:
                    profitability["roe"] = float(match.group(1))
                    break
            
            # ROA
            roa_patterns = [
                r"总资产收益率[^\d]*([\d\.]+)%",
                r"ROA[^\d]*([\d\.]+)%",
                r"加权平均总资产收益率[^\d]*([\d\.]+)%"
            ]
            
            for pattern in roa_patterns:
                match = re.search(pattern, text)
                if match:
                    profitability["roa"] = float(match.group(1))
                    break
            
            # 毛利率
            gross_margin_patterns = [
                r"毛利率[^\d]*([\d\.]+)%",
                r"销售毛利率[^\d]*([\d\.]+)%",
                r"营业毛利率[^\d]*([\d\.]+)%"
            ]
            
            for pattern in gross_margin_patterns:
                match = re.search(pattern, text)
                if match:
                    profitability["gross_margin"] = float(match.group(1))
                    break
            
            # 净利率
            net_margin_patterns = [
                r"净利率[^\d]*([\d\.]+)%",
                r"销售净利率[^\d]*([\d\.]+)%",
                r"营业净利率[^\d]*([\d\.]+)%"
            ]
            
            for pattern in net_margin_patterns:
                match = re.search(pattern, text)
                if match:
                    profitability["net_margin"] = float(match.group(1))
                    break
            
            return profitability
        except Exception as e:
            logger.error(f"提取盈利能力指标时出错: {str(e)}")
            return {
                "roe": None,
                "roa": None,
                "gross_margin": None,
                "net_margin": None
            }
    
    def extract_expense_ratios(self, text: str) -> Dict[str, Optional[float]]:
        """提取费用占比"""
        try:
            expense_ratios = {
                "sales_expense_ratio": None,
                "admin_expense_ratio": None,
                "rd_expense_ratio": None,
                "financial_expense_ratio": None
            }
            
            # 销售费用占比
            sales_patterns = [
                r"销售费用[^%]*占营业收入[^\d]*([\d\.]+)%",
                r"销售费用率[^\d]*([\d\.]+)%"
            ]
            
            for pattern in sales_patterns:
                match = re.search(pattern, text)
                if match:
                    expense_ratios["sales_expense_ratio"] = float(match.group(1))
                    break
            
            # 管理费用占比
            admin_patterns = [
                r"管理费用[^%]*占营业收入[^\d]*([\d\.]+)%",
                r"管理费用率[^\d]*([\d\.]+)%"
            ]
            
            for pattern in admin_patterns:
                match = re.search(pattern, text)
                if match:
                    expense_ratios["admin_expense_ratio"] = float(match.group(1))
                    break
            
            # 研发费用占比
            rd_patterns = [
                r"研发费用[^%]*占营业收入[^\d]*([\d\.]+)%",
                r"研发费用率[^\d]*([\d\.]+)%",
                r"研发投入[^%]*占营业收入[^\d]*([\d\.]+)%"
            ]
            
            for pattern in rd_patterns:
                match = re.search(pattern, text)
                if match:
                    expense_ratios["rd_expense_ratio"] = float(match.group(1))
                    break
            
            # 财务费用占比
            financial_patterns = [
                r"财务费用[^%]*占营业收入[^\d]*([\d\.]+)%",
                r"财务费用率[^\d]*([\d\.]+)%"
            ]
            
            for pattern in financial_patterns:
                match = re.search(pattern, text)
                if match:
                    expense_ratios["financial_expense_ratio"] = float(match.group(1))
                    break
            
            return expense_ratios
        except Exception as e:
            logger.error(f"提取费用占比时出错: {str(e)}")
            return {
                "sales_expense_ratio": None,
                "admin_expense_ratio": None,
                "rd_expense_ratio": None,
                "financial_expense_ratio": None
            }
    
    def extract_asset_structure(self, text: str) -> Dict[str, Optional[float]]:
        """提取资产结构占比"""
        try:
            asset_structure = {
                "accounts_receivable_ratio": None,
                "inventory_ratio": None,
                "construction_in_progress_ratio": None
            }
            
            # 应收账款占比
            ar_patterns = [
                r"应收账款[^%]*占总资产[^\d]*([\d\.]+)%",
                r"应收账款占比[^\d]*([\d\.]+)%"
            ]
            
            for pattern in ar_patterns:
                match = re.search(pattern, text)
                if match:
                    asset_structure["accounts_receivable_ratio"] = float(match.group(1))
                    break
            
            # 存货占比
            inventory_patterns = [
                r"存货[^%]*占总资产[^\d]*([\d\.]+)%",
                r"存货占比[^\d]*([\d\.]+)%"
            ]
            
            for pattern in inventory_patterns:
                match = re.search(pattern, text)
                if match:
                    asset_structure["inventory_ratio"] = float(match.group(1))
                    break
            
            # 在建工程占比
            cip_patterns = [
                r"在建工程[^%]*占总资产[^\d]*([\d\.]+)%",
                r"在建工程占比[^\d]*([\d\.]+)%"
            ]
            
            for pattern in cip_patterns:
                match = re.search(pattern, text)
                if match:
                    asset_structure["construction_in_progress_ratio"] = float(match.group(1))
                    break
            
            return asset_structure
        except Exception as e:
            logger.error(f"提取资产结构占比时出错: {str(e)}")
            return {
                "accounts_receivable_ratio": None,
                "inventory_ratio": None,
                "construction_in_progress_ratio": None
            }
    
    def extract_capital_structure(self, text: str) -> Dict[str, Optional[float]]:
        """提取资本结构"""
        try:
            capital_structure = {
                "net_assets": None,
                "debt_ratio": None
            }
            
            # 净资产
            net_assets_patterns = [
                r"净资产[^\d]*([\d,\.]+)[^\d%]*?元",
                r"所有者权益[^\d]*([\d,\.]+)[^\d%]*?元",
                r"股东权益[^\d]*([\d,\.]+)[^\d%]*?元"
            ]
            
            for pattern in net_assets_patterns:
                match = re.search(pattern, text)
                if match:
                    net_assets_str = match.group(1).replace(',', '')
                    capital_structure["net_assets"] = float(net_assets_str)
                    break
            
            # 负债率
            debt_ratio_patterns = [
                r"资产负债率[^\d]*([\d\.]+)%",
                r"负债率[^\d]*([\d\.]+)%"
            ]
            
            for pattern in debt_ratio_patterns:
                match = re.search(pattern, text)
                if match:
                    capital_structure["debt_ratio"] = float(match.group(1))
                    break
            
            return capital_structure
        except Exception as e:
            logger.error(f"提取资本结构时出错: {str(e)}")
            return {
                "net_assets": None,
                "debt_ratio": None
            }
    
    def extract_major_shareholder_changes(self, text: str) -> List[Dict[str, Any]]:
        """提取重大股东变化"""
        try:
            # 这部分需要更复杂的逻辑来提取表格数据
            # 简化版本，仅提取文本中明确提到的股东变化
            major_shareholder_changes = []
            
            # 尝试匹配股东变化的模式
            shareholder_pattern = r"([\u4e00-\u9fa5]+公司|[\u4e00-\u9fa5]+集团|[\u4e00-\u9fa5]+有限公司)[^%]*持股比例[^%]*从[^\d]*([\d\.]+)%[^%]*变[^\d]*([\d\.]+)%"
            
            for match in re.finditer(shareholder_pattern, text):
                shareholder = match.group(1)
                previous_holding = float(match.group(2))
                current_holding = float(match.group(3))
                change = round(current_holding - previous_holding, 2)
                
                major_shareholder_changes.append({
                    "shareholder": shareholder,
                    "previous_holding": previous_holding,
                    "current_holding": current_holding,
                    "change": change,
                    "change_date": None  # 日期通常需要更复杂的逻辑提取
                })
            
            return major_shareholder_changes
        except Exception as e:
            logger.error(f"提取重大股东变化时出错: {str(e)}")
            return []
    
    def extract_valuation_data(self, text: str) -> Dict[str, Optional[float]]:
        """提取估值指标"""
        try:
            valuation_data = {
                "pe": None,
                "pb": None
            }
            
            # PE
            pe_patterns = [
                r"市盈率[^\d]*([\d\.]+)",
                r"PE[^\d]*([\d\.]+)",
                r"P/E[^\d]*([\d\.]+)"
            ]
            
            for pattern in pe_patterns:
                match = re.search(pattern, text)
                if match:
                    valuation_data["pe"] = float(match.group(1))
                    break
            
            # PB
            pb_patterns = [
                r"市净率[^\d]*([\d\.]+)",
                r"PB[^\d]*([\d\.]+)",
                r"P/B[^\d]*([\d\.]+)"
            ]
            
            for pattern in pb_patterns:
                match = re.search(pattern, text)
                if match:
                    valuation_data["pb"] = float(match.group(1))
                    break
            
            return valuation_data
        except Exception as e:
            logger.error(f"提取估值指标时出错: {str(e)}")
            return {
                "pe": None,
                "pb": None
            }
    
    def extract_operation_data(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """提取经营数据"""
        try:
            operation_data = {
                "main_business": []
            }
            
            # 尝试匹配主营业务构成
            # 这部分通常在表格中，需要更复杂的表格解析逻辑
            # 简化版本，尝试匹配文本中的业务线描述
            business_pattern = r"([\u4e00-\u9fa5]+业务|[\u4e00-\u9fa5]+板块)[^%]*营业收入[^\d]*([\d,\.]+)[^\d%]*?元[^%]*占比[^\d]*([\d\.]+)%[^%]*同比[^\d-]*([-\d\.]+)%"
            
            for match in re.finditer(business_pattern, text):
                segment = match.group(1)
                revenue_str = match.group(2).replace(',', '')
                revenue = float(revenue_str)
                proportion = float(match.group(3))
                yoy = float(match.group(4))
                
                operation_data["main_business"].append({
                    "segment": segment,
                    "revenue": revenue,
                    "proportion": proportion,
                    "yoy": yoy
                })
            
            return operation_data
        except Exception as e:
            logger.error(f"提取经营数据时出错: {str(e)}")
            return {
                "main_business": []
            }
    
    def normalize_unit(self, value: float, unit_text: str) -> float:
        """统一金额单位"""
        if value is None:
            return None
        
        if "亿" in unit_text:
            return value  # 已经是亿元
        elif "万" in unit_text:
            return value / 10000  # 转换为亿元
        elif "元" in unit_text:
            return value / 100000000  # 转换为亿元
        else:
            return value  # 默认不变
    
    def analyze_report(self, stock_code: str, year: int, report_type: str) -> Dict[str, Any]:
        """分析财务报告"""
        try:
            # 获取报告文本
            text_content = self.get_report_text(stock_code, year, report_type)
            if not text_content:
                return {
                    "status": "error",
                    "message": "无法获取报告文本"
                }
            
            # 获取报告元数据
            metadata = self.get_report_metadata(stock_code, year, report_type)
            if not metadata:
                return {
                    "status": "error",
                    "message": "无法获取报告元数据"
                }
            
            # 提取基本信息
            company_name = metadata.get("report_metadata", {}).get("company_name", "未知公司")
            report_period = f"{year}年{report_type}"
            
            # 检查是否为补充公告
            if "补充公告" in text_content[:500]:
                logger.info(f"检测到补充公告: {stock_code} {year}年{report_type}")
                return {
                    "status": "partial",
                    "message": "检测到补充公告，非完整财务报告",
                    "basic_info": {
                        "company_name": company_name,
                        "stock_code": stock_code,
                        "report_period": report_period
                    },
                    "report_type": "补充公告",
                    "report_content": text_content[:1000] + "..." if len(text_content) > 1000 else text_content
                }
            
            # 提取财务数据
            net_profit, net_profit_yoy = self.extract_net_profit(text_content)
            revenue, revenue_yoy = self.extract_revenue(text_content)
            cash_flow = self.extract_cash_flow(text_content)
            profitability = self.extract_profitability(text_content)
            expense_ratios = self.extract_expense_ratios(text_content)
            asset_structure = self.extract_asset_structure(text_content)
            capital_structure = self.extract_capital_structure(text_content)
            major_shareholder_changes = self.extract_major_shareholder_changes(text_content)
            valuation_data = self.extract_valuation_data(text_content)
            operation_data = self.extract_operation_data(text_content)
            
            # 构建分析结果
            analysis_result = {
                "basic_info": {
                    "company_name": company_name,
                    "stock_code": stock_code,
                    "report_period": report_period
                },
                "financial_data": {
                    "net_profit": net_profit,  # 单位：元，后续需要统一单位
                    "net_profit_yoy": net_profit_yoy,  # 单位：%
                    "profit_forecast": None,  # 需要更复杂的逻辑提取
                    "revenue": revenue,  # 单位：元，后续需要统一单位
                    "revenue_yoy": revenue_yoy,  # 单位：%
                    "cash_flow": cash_flow,
                    "profitability": profitability,
                    "expense_ratios": expense_ratios,
                    "asset_structure": asset_structure,
                    "capital_structure": capital_structure,
                    "major_shareholder_changes": major_shareholder_changes
                },
                "valuation_data": valuation_data,
                "operation_data": operation_data
            }
            
            # 如果启用了LLM分析，则添加LLM分析结果
            if self.use_llm:
                try:
                    logger.info(f"使用LLM分析 {company_name} {report_period} 财务报告")
                    llm_analysis = self.llm_service.analyze_financial_report(
                        text_content, company_name, report_period
                    )
                    
                    # 提取关键指标
                    llm_metrics = self.llm_service.extract_key_metrics(text_content)
                    
                    # 添加LLM分析结果
                    analysis_result["llm_analysis"] = {
                        "summary": llm_analysis.get("summary", ""),
                        "financial_data": llm_analysis.get("financial_data", {}),
                        "metrics": llm_metrics
                    }
                    
                    # 如果规则提取的数据不完整，尝试使用LLM提取的数据补充
                    self._merge_llm_data_with_rule_based_data(analysis_result)
                    
                except Exception as llm_error:
                    logger.error(f"LLM分析过程中出错: {str(llm_error)}")
                    analysis_result["llm_analysis"] = {
                        "error": str(llm_error),
                        "status": "error"
                    }
            
            # 添加分析状态
            analysis_result["status"] = "success"
            analysis_result["message"] = "分析完成"
            
            return analysis_result
        except Exception as e:
            logger.error(f"分析报告时出错: {str(e)}")
            return {
                "status": "error",
                "message": f"分析报告时出错: {str(e)}"
            }
            
    def _merge_llm_data_with_rule_based_data(self, analysis_result: Dict[str, Any]) -> None:
        """将LLM提取的数据与规则提取的数据合并"""
        try:
            if "llm_analysis" not in analysis_result:
                return
                
            llm_financial_data = analysis_result["llm_analysis"].get("financial_data", {})
            llm_metrics = analysis_result["llm_analysis"].get("metrics", {})
            
            # 合并基本财务数据
            rule_financial_data = analysis_result["financial_data"]
            
            # 如果规则提取的净利润为空，但LLM提取到了，则使用LLM的数据
            if rule_financial_data.get("net_profit") is None and llm_financial_data.get("net_profit") is not None:
                try:
                    rule_financial_data["net_profit"] = float(str(llm_financial_data["net_profit"]).replace(",", ""))
                except (ValueError, TypeError):
                    pass
                    
            # 同理处理其他指标
            if rule_financial_data.get("net_profit_yoy") is None and llm_financial_data.get("net_profit_yoy") is not None:
                try:
                    rule_financial_data["net_profit_yoy"] = float(str(llm_financial_data["net_profit_yoy"]).replace("%", ""))
                except (ValueError, TypeError):
                    pass
                    
            if rule_financial_data.get("revenue") is None and llm_financial_data.get("revenue") is not None:
                try:
                    rule_financial_data["revenue"] = float(str(llm_financial_data["revenue"]).replace(",", ""))
                except (ValueError, TypeError):
                    pass
                    
            if rule_financial_data.get("revenue_yoy") is None and llm_financial_data.get("revenue_yoy") is not None:
                try:
                    rule_financial_data["revenue_yoy"] = float(str(llm_financial_data["revenue_yoy"]).replace("%", ""))
                except (ValueError, TypeError):
                    pass
                    
            # 合并盈利能力指标
            rule_profitability = rule_financial_data.get("profitability", {})
            llm_profitability = llm_financial_data.get("profitability", {})
            
            for key in ["roe", "roa", "gross_margin", "net_margin"]:
                if rule_profitability.get(key) is None and llm_profitability.get(key) is not None:
                    try:
                        rule_profitability[key] = float(str(llm_profitability[key]).replace("%", ""))
                    except (ValueError, TypeError):
                        pass
                        
            # 合并现金流数据
            rule_cash_flow = rule_financial_data.get("cash_flow", {})
            llm_cash_flow = llm_financial_data.get("cash_flow", {})
            
            for key in ["operating", "investing", "financing"]:
                if rule_cash_flow.get(key) is None and llm_cash_flow.get(key) is not None:
                    try:
                        rule_cash_flow[key] = float(str(llm_cash_flow[key]).replace(",", ""))
                    except (ValueError, TypeError):
                        pass
                        
            # 合并资本结构数据
            rule_capital = rule_financial_data.get("capital_structure", {})
            llm_capital = llm_financial_data.get("capital_structure", {})
            
            for key in ["net_assets", "debt_ratio"]:
                if rule_capital.get(key) is None and llm_capital.get(key) is not None:
                    try:
                        value = str(llm_capital[key])
                        if key == "debt_ratio":
                            rule_capital[key] = float(value.replace("%", ""))
                        else:
                            rule_capital[key] = float(value.replace(",", ""))
                    except (ValueError, TypeError):
                        pass
                        
            # 从LLM指标中提取更多数据
            basic_indicators = llm_metrics.get("basic_indicators", {})
            for key, value in basic_indicators.items():
                if value is not None and key not in ["revenue", "net_profit"]:
                    analysis_result["llm_metrics"] = analysis_result.get("llm_metrics", {})
                    analysis_result["llm_metrics"][key] = value
                    
        except Exception as e:
            logger.error(f"合并LLM数据时出错: {str(e)}")
    
    def generate_analysis_summary(self, analysis_result: Dict[str, Any]) -> str:
        """生成分析摘要"""
        try:
            if analysis_result.get("status") == "error":
                return "无法生成分析摘要，分析结果不完整。"
                
            if analysis_result.get("status") == "partial" and analysis_result.get("report_type") == "补充公告":
                basic_info = analysis_result.get("basic_info", {})
                company_name = basic_info.get("company_name", "未知公司")
                report_period = basic_info.get("report_period", "未知期间")
                report_content = analysis_result.get("report_content", "")
                
                summary = f"## {company_name} {report_period} 补充公告\n\n"
                summary += "### 公告内容摘要\n\n"
                summary += f"{report_content[:500]}...\n\n"
                summary += "### 注意事项\n\n"
                summary += "- 这是一份补充公告，不是完整的财务报告\n"
                summary += "- 补充公告通常用于更正或补充已发布的财务报告中的特定信息\n"
                summary += "- 请参考完整的财务报告以获取全面的财务信息\n"
                
                return summary
            
            # 如果有LLM分析结果，优先使用LLM生成的摘要
            if "llm_analysis" in analysis_result and analysis_result["llm_analysis"].get("summary"):
                logger.info("使用LLM生成的分析摘要")
                return analysis_result["llm_analysis"]["summary"]
            
            # 如果没有LLM分析结果，使用规则生成摘要
            basic_info = analysis_result.get("basic_info", {})
            financial_data = analysis_result.get("financial_data", {})
            
            company_name = basic_info.get("company_name", "未知公司")
            report_period = basic_info.get("report_period", "未知期间")
            
            net_profit = financial_data.get("net_profit")
            net_profit_yoy = financial_data.get("net_profit_yoy")
            revenue = financial_data.get("revenue")
            revenue_yoy = financial_data.get("revenue_yoy")
            
            profitability = financial_data.get("profitability", {})
            roe = profitability.get("roe")
            
            cash_flow = financial_data.get("cash_flow", {})
            operating_cash_flow = cash_flow.get("operating")
            
            # 构建摘要
            summary = f"## {company_name} {report_period} 财务分析摘要\n\n"
            
            # 业绩概览
            summary += "### 业绩概览\n\n"
            
            if net_profit is not None:
                net_profit_text = f"{net_profit:.2f}元"
                if net_profit_yoy is not None:
                    direction = "增长" if net_profit_yoy > 0 else "下降"
                    summary += f"- 归母净利润: {net_profit_text}，同比{direction} {abs(net_profit_yoy):.2f}%\n"
                else:
                    summary += f"- 归母净利润: {net_profit_text}\n"
            
            if revenue is not None:
                revenue_text = f"{revenue:.2f}元"
                if revenue_yoy is not None:
                    direction = "增长" if revenue_yoy > 0 else "下降"
                    summary += f"- 营业总收入: {revenue_text}，同比{direction} {abs(revenue_yoy):.2f}%\n"
                else:
                    summary += f"- 营业总收入: {revenue_text}\n"
            
            if roe is not None:
                summary += f"- 净资产收益率(ROE): {roe:.2f}%\n"
            
            if operating_cash_flow is not None:
                cash_flow_status = "正" if operating_cash_flow > 0 else "负"
                summary += f"- 经营活动现金流: {operating_cash_flow:.2f}元，呈{cash_flow_status}向\n"
            
            # 财务健康状况
            summary += "\n### 财务健康状况\n\n"
            
            debt_ratio = financial_data.get("capital_structure", {}).get("debt_ratio")
            if debt_ratio is not None:
                debt_level = "较高" if debt_ratio > 60 else "适中" if debt_ratio > 40 else "较低"
                summary += f"- 资产负债率: {debt_ratio:.2f}%，负债水平{debt_level}\n"
            
            # 主营业务分析
            main_business = analysis_result.get("operation_data", {}).get("main_business", [])
            if main_business:
                summary += "\n### 主营业务分析\n\n"
                for business in main_business:
                    segment = business.get("segment", "未知业务")
                    proportion = business.get("proportion")
                    yoy = business.get("yoy")
                    
                    if proportion is not None:
                        business_text = f"- {segment}: 占比 {proportion:.2f}%"
                        if yoy is not None:
                            direction = "增长" if yoy > 0 else "下降"
                            business_text += f"，同比{direction} {abs(yoy):.2f}%"
                        summary += business_text + "\n"
            
            # 风险提示
            summary += "\n### 风险提示\n\n"
            
            risks = []
            if net_profit_yoy is not None and net_profit_yoy < 0:
                risks.append(f"净利润同比下降 {abs(net_profit_yoy):.2f}%")
            
            if revenue_yoy is not None and revenue_yoy < 0:
                risks.append(f"营业收入同比下降 {abs(revenue_yoy):.2f}%")
            
            if operating_cash_flow is not None and operating_cash_flow < 0:
                risks.append("经营活动现金流为负")
            
            if debt_ratio is not None and debt_ratio > 70:
                risks.append(f"资产负债率较高 ({debt_ratio:.2f}%)")
            
            if risks:
                for risk in risks:
                    summary += f"- {risk}\n"
            else:
                summary += "- 未发现明显财务风险\n"
            
            return summary
        except Exception as e:
            logger.error(f"生成分析摘要时出错: {str(e)}")
            return "生成分析摘要时出错，请检查分析结果的完整性。"
            
    def analyze_financial_trends(self, stock_code: str, current_year: int, previous_year: int, report_type: str) -> Dict[str, Any]:
        """分析财务趋势变化"""
        try:
            # 获取当前报告和上一年报告
            current_text = self.get_report_text(stock_code, current_year, report_type)
            previous_text = self.get_report_text(stock_code, previous_year, report_type)
            
            if not current_text or not previous_text:
                return {
                    "status": "error",
                    "message": "无法获取完整的报告文本进行对比分析"
                }
            
            # 获取公司名称
            current_metadata = self.get_report_metadata(stock_code, current_year, report_type)
            company_name = current_metadata.get("report_metadata", {}).get("company_name", "未知公司") if current_metadata else "未知公司"
            
            # 如果启用了LLM分析，使用LLM进行趋势分析
            if self.use_llm:
                try:
                    logger.info(f"使用LLM分析 {company_name} {current_year}年与{previous_year}年{report_type} 财务趋势")
                    trend_analysis = self.llm_service.analyze_financial_trends(
                        current_text, previous_text, company_name
                    )
                    
                    return {
                        "status": "success",
                        "message": "趋势分析完成",
                        "company_name": company_name,
                        "current_year": current_year,
                        "previous_year": previous_year,
                        "report_type": report_type,
                        "trend_summary": trend_analysis.get("trend_summary", ""),
                        "trend_data": trend_analysis.get("trend_data", {})
                    }
                except Exception as llm_error:
                    logger.error(f"LLM趋势分析过程中出错: {str(llm_error)}")
                    # 如果LLM分析失败，回退到规则分析
            
            # 规则分析（简化版）
            # 分析两年的报告
            current_analysis = self.analyze_report(stock_code, current_year, report_type)
            previous_analysis = self.analyze_report(stock_code, previous_year, report_type)
            
            if current_analysis.get("status") != "success" or previous_analysis.get("status") != "success":
                return {
                    "status": "error",
                    "message": "无法完成对比分析，报告分析不完整"
                }
            
            # 提取关键指标进行对比
            current_financial = current_analysis.get("financial_data", {})
            previous_financial = previous_analysis.get("financial_data", {})
            
            # 计算变化
            changes = {
                "net_profit_change": self._calculate_change(
                    current_financial.get("net_profit"), 
                    previous_financial.get("net_profit")
                ),
                "revenue_change": self._calculate_change(
                    current_financial.get("revenue"), 
                    previous_financial.get("revenue")
                ),
                "roe_change": self._calculate_change(
                    current_financial.get("profitability", {}).get("roe"), 
                    previous_financial.get("profitability", {}).get("roe")
                ),
                "debt_ratio_change": self._calculate_change(
                    current_financial.get("capital_structure", {}).get("debt_ratio"), 
                    previous_financial.get("capital_structure", {}).get("debt_ratio")
                ),
                "operating_cash_flow_change": self._calculate_change(
                    current_financial.get("cash_flow", {}).get("operating"), 
                    previous_financial.get("cash_flow", {}).get("operating")
                )
            }
            
            # 生成趋势摘要
            trend_summary = self._generate_trend_summary(company_name, current_year, previous_year, report_type, changes)
            
            return {
                "status": "success",
                "message": "趋势分析完成",
                "company_name": company_name,
                "current_year": current_year,
                "previous_year": previous_year,
                "report_type": report_type,
                "trend_summary": trend_summary,
                "trend_data": changes
            }
        except Exception as e:
            logger.error(f"分析财务趋势时出错: {str(e)}")
            return {
                "status": "error",
                "message": f"分析财务趋势时出错: {str(e)}"
            }
    
    def _calculate_change(self, current_value, previous_value) -> Dict[str, Any]:
        """计算指标变化"""
        if current_value is None or previous_value is None:
            return {
                "current": current_value,
                "previous": previous_value,
                "change": None,
                "change_percent": None,
                "direction": None
            }
        
        change = current_value - previous_value
        if previous_value == 0:
            change_percent = None  # 避免除以零
        else:
            change_percent = (change / previous_value) * 100
            
        direction = "上升" if change > 0 else "下降" if change < 0 else "持平"
        
        return {
            "current": current_value,
            "previous": previous_value,
            "change": change,
            "change_percent": change_percent,
            "direction": direction
        }
    
    def _generate_trend_summary(self, company_name, current_year, previous_year, report_type, changes) -> str:
        """生成趋势分析摘要"""
        try:
            summary = f"## {company_name} {current_year}年vs{previous_year}年{report_type} 趋势分析\n\n"
            
            # 业绩变化
            summary += "### 业绩变化\n\n"
            
            # 净利润变化
            net_profit_change = changes.get("net_profit_change", {})
            if net_profit_change.get("change_percent") is not None:
                direction = net_profit_change.get("direction", "")
                change_percent = abs(net_profit_change.get("change_percent", 0))
                summary += f"- 净利润: {direction} {change_percent:.2f}%，从 {net_profit_change.get('previous', 0):.2f}元 变为 {net_profit_change.get('current', 0):.2f}元\n"
            
            # 营收变化
            revenue_change = changes.get("revenue_change", {})
            if revenue_change.get("change_percent") is not None:
                direction = revenue_change.get("direction", "")
                change_percent = abs(revenue_change.get("change_percent", 0))
                summary += f"- 营业收入: {direction} {change_percent:.2f}%，从 {revenue_change.get('previous', 0):.2f}元 变为 {revenue_change.get('current', 0):.2f}元\n"
            
            # ROE变化
            roe_change = changes.get("roe_change", {})
            if roe_change.get("change") is not None:
                direction = roe_change.get("direction", "")
                change = abs(roe_change.get("change", 0))
                summary += f"- 净资产收益率(ROE): {direction} {change:.2f}个百分点，从 {roe_change.get('previous', 0):.2f}% 变为 {roe_change.get('current', 0):.2f}%\n"
            
            # 财务状况变化
            summary += "\n### 财务状况变化\n\n"
            
            # 资产负债率变化
            debt_ratio_change = changes.get("debt_ratio_change", {})
            if debt_ratio_change.get("change") is not None:
                direction = debt_ratio_change.get("direction", "")
                change = abs(debt_ratio_change.get("change", 0))
                summary += f"- 资产负债率: {direction} {change:.2f}个百分点，从 {debt_ratio_change.get('previous', 0):.2f}% 变为 {debt_ratio_change.get('current', 0):.2f}%\n"
            
            # 经营现金流变化
            cash_flow_change = changes.get("operating_cash_flow_change", {})
            if cash_flow_change.get("change_percent") is not None:
                direction = cash_flow_change.get("direction", "")
                change_percent = abs(cash_flow_change.get("change_percent", 0))
                summary += f"- 经营活动现金流: {direction} {change_percent:.2f}%，从 {cash_flow_change.get('previous', 0):.2f}元 变为 {cash_flow_change.get('current', 0):.2f}元\n"
            
            # 趋势总结
            summary += "\n### 趋势总结\n\n"
            
            # 判断整体趋势
            positive_trends = 0
            negative_trends = 0
            
            for change_key in ["net_profit_change", "revenue_change", "roe_change"]:
                change_data = changes.get(change_key, {})
                if change_data.get("direction") == "上升":
                    positive_trends += 1
                elif change_data.get("direction") == "下降":
                    negative_trends += 1
            
            if positive_trends > negative_trends:
                summary += "- 整体趋势: 向好 ⬆️\n"
                summary += "- 公司主要财务指标呈现上升趋势，业绩表现良好\n"
            elif negative_trends > positive_trends:
                summary += "- 整体趋势: 下滑 ⬇️\n"
                summary += "- 公司主要财务指标呈现下降趋势，业绩表现不佳\n"
            else:
                summary += "- 整体趋势: 稳定 ↔️\n"
                summary += "- 公司主要财务指标变化不大，业绩表现稳定\n"
            
            return summary
        except Exception as e:
            logger.error(f"生成趋势分析摘要时出错: {str(e)}")
            return "生成趋势分析摘要时出错，请检查分析结果的完整性。"
            
    def identify_risk_factors(self, stock_code: str, year: int, report_type: str) -> Dict[str, Any]:
        """识别财务报告中的风险因素"""
        try:
            # 获取报告文本
            text_content = self.get_report_text(stock_code, year, report_type)
            if not text_content:
                return {
                    "status": "error",
                    "message": "无法获取报告文本"
                }
            
            # 获取报告元数据
            metadata = self.get_report_metadata(stock_code, year, report_type)
            if not metadata:
                return {
                    "status": "error",
                    "message": "无法获取报告元数据"
                }
            
            # 提取基本信息
            company_name = metadata.get("report_metadata", {}).get("company_name", "未知公司")
            
            # 如果启用了LLM分析，使用LLM进行风险分析
            if self.use_llm:
                try:
                    logger.info(f"使用LLM分析 {company_name} {year}年{report_type} 风险因素")
                    risk_analysis = self.llm_service.identify_risk_factors(
                        text_content, company_name
                    )
                    
                    return {
                        "status": "success",
                        "message": "风险分析完成",
                        "company_name": company_name,
                        "year": year,
                        "report_type": report_type,
                        "risk_summary": risk_analysis.get("risk_summary", ""),
                        "risk_factors": risk_analysis.get("risk_factors", [])
                    }
                except Exception as llm_error:
                    logger.error(f"LLM风险分析过程中出错: {str(llm_error)}")
                    # 如果LLM分析失败，回退到规则分析
            
            # 规则分析（简化版）
            # 尝试提取风险提示部分
            risk_section = self._extract_risk_section(text_content)
            
            # 提取财务风险指标
            analysis_result = self.analyze_report(stock_code, year, report_type)
            financial_data = analysis_result.get("financial_data", {}) if analysis_result.get("status") == "success" else {}
            
            risk_factors = []
            
            # 检查净利润同比下降
            net_profit_yoy = financial_data.get("net_profit_yoy")
            if net_profit_yoy is not None and net_profit_yoy < 0:
                risk_factors.append({
                    "category": "盈利能力风险",
                    "description": f"净利润同比下降 {abs(net_profit_yoy):.2f}%",
                    "severity": "high" if net_profit_yoy < -20 else "medium" if net_profit_yoy < -10 else "low",
                    "evidence": f"财务数据显示净利润同比变化为 {net_profit_yoy:.2f}%",
                    "suggestion": "关注成本控制和收入增长策略"
                })
            
            # 检查营收同比下降
            revenue_yoy = financial_data.get("revenue_yoy")
            if revenue_yoy is not None and revenue_yoy < 0:
                risk_factors.append({
                    "category": "营收风险",
                    "description": f"营业收入同比下降 {abs(revenue_yoy):.2f}%",
                    "severity": "high" if revenue_yoy < -15 else "medium" if revenue_yoy < -5 else "low",
                    "evidence": f"财务数据显示营业收入同比变化为 {revenue_yoy:.2f}%",
                    "suggestion": "关注市场份额和产品竞争力"
                })
            
            # 检查经营现金流为负
            operating_cash_flow = financial_data.get("cash_flow", {}).get("operating")
            if operating_cash_flow is not None and operating_cash_flow < 0:
                risk_factors.append({
                    "category": "现金流风险",
                    "description": "经营活动现金流为负",
                    "severity": "high",
                    "evidence": f"财务数据显示经营活动现金流为 {operating_cash_flow:.2f}元",
                    "suggestion": "关注应收账款管理和存货周转"
                })
            
            # 检查资产负债率过高
            debt_ratio = financial_data.get("capital_structure", {}).get("debt_ratio")
            if debt_ratio is not None and debt_ratio > 70:
                risk_factors.append({
                    "category": "负债风险",
                    "description": f"资产负债率较高 ({debt_ratio:.2f}%)",
                    "severity": "high" if debt_ratio > 80 else "medium",
                    "evidence": f"财务数据显示资产负债率为 {debt_ratio:.2f}%",
                    "suggestion": "关注债务结构和偿债能力"
                })
            
            # 生成风险摘要
            risk_summary = self._generate_risk_summary(company_name, year, report_type, risk_factors, risk_section)
            
            return {
                "status": "success",
                "message": "风险分析完成",
                "company_name": company_name,
                "year": year,
                "report_type": report_type,
                "risk_summary": risk_summary,
                "risk_factors": risk_factors,
                "risk_section": risk_section[:2000] if risk_section else None
            }
        except Exception as e:
            logger.error(f"识别风险因素时出错: {str(e)}")
            return {
                "status": "error",
                "message": f"识别风险因素时出错: {str(e)}"
            }
    
    def _extract_risk_section(self, text_content: str) -> Optional[str]:
        """提取风险提示部分"""
        try:
            # 尝试匹配风险提示部分
            risk_section_patterns = [
                r"(?:第[三四五]节|三、|四、|五、)\s*(?:重大风险提示|风险因素|风险提示)(.*?)(?:第[四五六]节|四、|五、|六、)",
                r"风险提示(.*?)(?:一、|二、|三、)",
                r"风险因素(.*?)(?:一、|二、|三、)"
            ]
            
            for pattern in risk_section_patterns:
                match = re.search(pattern, text_content, re.DOTALL)
                if match:
                    return match.group(1).strip()
            
            return None
        except Exception as e:
            logger.error(f"提取风险提示部分时出错: {str(e)}")
            return None
    
    def _generate_risk_summary(self, company_name: str, year: int, report_type: str, risk_factors: List[Dict[str, Any]], risk_section: Optional[str]) -> str:
        """生成风险分析摘要"""
        try:
            summary = f"## {company_name} {year}年{report_type} 风险分析\n\n"
            
            # 风险因素概述
            summary += "### 风险因素概述\n\n"
            
            if not risk_factors:
                summary += "- 未发现明显财务风险\n"
            else:
                for risk in risk_factors:
                    severity = risk.get("severity", "medium")
                    severity_icon = "🔴" if severity == "high" else "🟠" if severity == "medium" else "🟡"
                    summary += f"- {severity_icon} **{risk.get('category', '未知风险')}**: {risk.get('description', '')}\n"
            
            # 风险详情
            if risk_factors:
                summary += "\n### 风险详情\n\n"
                
                for i, risk in enumerate(risk_factors, 1):
                    summary += f"#### {i}. {risk.get('category', '未知风险')}\n\n"
                    summary += f"- **描述**: {risk.get('description', '')}\n"
                    summary += f"- **严重程度**: {risk.get('severity', 'medium')}\n"
                    summary += f"- **证据**: {risk.get('evidence', '')}\n"
                    summary += f"- **建议**: {risk.get('suggestion', '')}\n\n"
            
            # 公司风险提示摘录
            if risk_section:
                summary += "\n### 公司风险提示摘录\n\n"
                summary += f"{risk_section[:1000]}...\n" if len(risk_section) > 1000 else f"{risk_section}\n"
            
            return summary
        except Exception as e:
            logger.error(f"生成风险分析摘要时出错: {str(e)}")
            return "生成风险分析摘要时出错，请检查分析结果的完整性。"