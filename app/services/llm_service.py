"""
LLM服务模块，用于使用大型语言模型分析财报数据
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from litellm import completion

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("financial_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LLMService")

class LLMService:
    """LLM服务类，用于调用大型语言模型进行财报分析"""
    
    def __init__(self, model: str = "deepseek-chat", api_key: Optional[str] = None):
        """
        初始化LLM服务
        
        Args:
            model: 使用的模型名称
            api_key: API密钥，如果为None则从环境变量获取
        """
        self.model = model
        # 如果提供了API密钥，则设置环境变量
        if api_key:
            os.environ["DEEPSEEK_API_KEY"] = api_key
        
        # 检查是否设置了API密钥
        if not os.environ.get("DEEPSEEK_API_KEY"):
            logger.warning("未设置DEEPSEEK_API_KEY环境变量，LLM分析功能将不可用")
        
        # 设置DeepSeek API基础URL
        os.environ["DEEPSEEK_API_BASE"] = "https://api.deepseek.com/v1"
    
    def analyze_financial_report(self, report_text: str, company_name: str, report_period: str) -> Dict[str, Any]:
        """
        分析财务报告文本
        
        Args:
            report_text: 财务报告文本内容
            company_name: 公司名称
            report_period: 报告期间（如"2023年年度报告"）
            
        Returns:
            包含分析结果的字典
        """
        try:
            # 如果报告文本过长，截取前50000个字符进行分析
            if len(report_text) > 50000:
                logger.info(f"报告文本过长({len(report_text)}字符)，截取前50000个字符进行分析")
                analysis_text = report_text[:50000]
            else:
                analysis_text = report_text
            
            # 构建提示词
            prompt = self._build_analysis_prompt(analysis_text, company_name, report_period)
            
            # 调用LLM进行分析，指定DeepSeek作为提供商
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4000,
                custom_llm_provider="deepseek"
            )
            
            # 解析响应
            content = response.choices[0].message.content
            
            # 尝试将响应解析为JSON
            try:
                # 查找JSON部分
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    result = json.loads(json_str)
                else:
                    # 如果没有找到JSON格式，则将整个响应作为摘要返回
                    result = {
                        "summary": content,
                        "financial_data": None
                    }
            except json.JSONDecodeError:
                logger.warning("无法解析LLM响应为JSON格式，将使用原始响应")
                result = {
                    "summary": content,
                    "financial_data": None
                }
            
            return result
        
        except Exception as e:
            logger.error(f"LLM分析过程中出错: {str(e)}")
            return {
                "error": str(e),
                "summary": "分析过程中出错，请检查API密钥是否正确设置或稍后重试。",
                "financial_data": None
            }
    
    def extract_key_metrics(self, report_text: str) -> Dict[str, Any]:
        """
        从财务报告中提取关键财务指标
        
        Args:
            report_text: 财务报告文本内容
            
        Returns:
            包含关键财务指标的字典
        """
        try:
            # 如果报告文本过长，截取前30000个字符进行分析
            if len(report_text) > 30000:
                logger.info(f"报告文本过长({len(report_text)}字符)，截取前30000个字符进行指标提取")
                analysis_text = report_text[:30000]
            else:
                analysis_text = report_text
            
            # 构建提示词
            prompt = self._build_metrics_extraction_prompt(analysis_text)
            
            # 调用LLM进行分析，指定DeepSeek作为提供商
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000,
                custom_llm_provider="deepseek"
            )
            
            # 解析响应
            content = response.choices[0].message.content
            
            # 尝试将响应解析为JSON
            try:
                # 查找JSON部分
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    result = json.loads(json_str)
                else:
                    # 如果没有找到JSON格式，则返回空结果
                    result = {}
            except json.JSONDecodeError:
                logger.warning("无法解析LLM响应为JSON格式")
                result = {}
            
            return result
        
        except Exception as e:
            logger.error(f"提取关键指标过程中出错: {str(e)}")
            return {"error": str(e)}
    
    def analyze_financial_trends(self, current_report: str, previous_report: str, company_name: str) -> Dict[str, Any]:
        """
        分析财务报告的趋势变化
        
        Args:
            current_report: 当前财务报告文本
            previous_report: 上一期财务报告文本
            company_name: 公司名称
            
        Returns:
            包含趋势分析结果的字典
        """
        try:
            # 如果报告文本过长，截取前部分进行分析
            if len(current_report) > 30000:
                current_text = current_report[:30000]
            else:
                current_text = current_report
                
            if len(previous_report) > 30000:
                previous_text = previous_report[:30000]
            else:
                previous_text = previous_report
            
            # 构建提示词
            prompt = self._build_trend_analysis_prompt(current_text, previous_text, company_name)
            
            # 调用LLM进行分析，指定DeepSeek作为提供商
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=3000,
                custom_llm_provider="deepseek"
            )
            
            # 解析响应
            content = response.choices[0].message.content
            
            # 尝试将响应解析为JSON
            try:
                # 查找JSON部分
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    result = json.loads(json_str)
                else:
                    # 如果没有找到JSON格式，则将整个响应作为摘要返回
                    result = {
                        "trend_summary": content,
                        "trend_data": None
                    }
            except json.JSONDecodeError:
                logger.warning("无法解析LLM响应为JSON格式，将使用原始响应")
                result = {
                    "trend_summary": content,
                    "trend_data": None
                }
            
            return result
        
        except Exception as e:
            logger.error(f"趋势分析过程中出错: {str(e)}")
            return {
                "error": str(e),
                "trend_summary": "分析过程中出错，请检查API密钥是否正确设置或稍后重试。",
                "trend_data": None
            }
    
    def identify_risk_factors(self, report_text: str, company_name: str) -> Dict[str, Any]:
        """
        识别财务报告中的风险因素
        
        Args:
            report_text: 财务报告文本内容
            company_name: 公司名称
            
        Returns:
            包含风险因素分析的字典
        """
        try:
            # 如果报告文本过长，截取前40000个字符进行分析
            if len(report_text) > 40000:
                analysis_text = report_text[:40000]
            else:
                analysis_text = report_text
            
            # 构建提示词
            prompt = self._build_risk_analysis_prompt(analysis_text, company_name)
            
            # 调用LLM进行分析，指定DeepSeek作为提供商
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2500,
                custom_llm_provider="deepseek"
            )
            
            # 解析响应
            content = response.choices[0].message.content
            
            # 尝试将响应解析为JSON
            try:
                # 查找JSON部分
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    result = json.loads(json_str)
                else:
                    # 如果没有找到JSON格式，则将整个响应作为摘要返回
                    result = {
                        "risk_summary": content,
                        "risk_factors": []
                    }
            except json.JSONDecodeError:
                logger.warning("无法解析LLM响应为JSON格式，将使用原始响应")
                result = {
                    "risk_summary": content,
                    "risk_factors": []
                }
            
            return result
        
        except Exception as e:
            logger.error(f"风险分析过程中出错: {str(e)}")
            return {
                "error": str(e),
                "risk_summary": "分析过程中出错，请检查API密钥是否正确设置或稍后重试。",
                "risk_factors": []
            }
    
    def _build_analysis_prompt(self, report_text: str, company_name: str, report_period: str) -> str:
        """构建财报分析提示词"""
        return f"""你是一位专业的财务分析师，请对以下公司的财务报告进行详细分析。

公司名称: {company_name}
报告期间: {report_period}

请基于以下财务报告内容，提供全面的财务分析，包括但不限于：
1. 公司整体财务状况概述
2. 盈利能力分析（净利润、毛利率、净资产收益率等）
3. 营收构成及变化趋势
4. 成本费用结构分析
5. 现金流状况分析
6. 资产负债情况分析
7. 主要财务风险点识别
8. 未来发展前景展望

请尽可能提取具体的财务数据，并给出专业的分析见解。如果某些信息在报告中未提及，请注明。

请以JSON格式返回分析结果，包含以下字段：
1. summary: 财务分析摘要（Markdown格式）
2. financial_data: 包含关键财务指标的对象，至少应包含以下子字段：
   - net_profit: 净利润
   - net_profit_yoy: 净利润同比增长率
   - revenue: 营业收入
   - revenue_yoy: 营业收入同比增长率
   - profitability: 盈利能力指标对象（包含roe、roa、gross_margin、net_margin等）
   - cash_flow: 现金流量对象（包含operating、investing、financing等）
   - capital_structure: 资本结构对象（包含net_assets、debt_ratio等）
   - expense_ratios: 费用率对象（包含销售/管理/研发/财务费用率）
   - operation_data: 经营数据对象（包含main_business数组等）

财务报告内容如下：
{report_text}
"""

    def _build_metrics_extraction_prompt(self, report_text: str) -> str:
        """构建指标提取提示词"""
        return f"""你是一位专业的财务数据提取专家，请从以下财务报告中提取关键财务指标。

请仅提取明确在报告中出现的数据，不要进行推断或计算。如果某项指标在报告中未明确提及，请将其值设为null。

请以JSON格式返回以下关键财务指标：
{{
  "basic_indicators": {{
    "revenue": "营业收入（元）",
    "net_profit": "净利润（元）",
    "eps": "每股收益（元）",
    "total_assets": "总资产（元）",
    "net_assets": "净资产（元）",
    "operating_cash_flow": "经营活动现金流量（元）"
  }},
  "profitability": {{
    "gross_margin": "毛利率（%）",
    "net_margin": "净利率（%）",
    "roe": "净资产收益率（%）",
    "roa": "总资产收益率（%）"
  }},
  "growth": {{
    "revenue_yoy": "营业收入同比增长率（%）",
    "net_profit_yoy": "净利润同比增长率（%）",
    "total_assets_growth": "总资产增长率（%）"
  }},
  "solvency": {{
    "debt_ratio": "资产负债率（%）",
    "current_ratio": "流动比率",
    "quick_ratio": "速动比率"
  }},
  "operational": {{
    "inventory_turnover": "存货周转率",
    "receivables_turnover": "应收账款周转率",
    "total_assets_turnover": "总资产周转率"
  }},
  "per_share": {{
    "eps": "每股收益（元）",
    "bvps": "每股净资产（元）",
    "ocfps": "每股经营现金流（元）"
  }},
  "cash_flow": {{
    "operating": "经营活动现金流量净额（元）",
    "investing": "投资活动现金流量净额（元）",
    "financing": "筹资活动现金流量净额（元）"
  }}
}}

财务报告内容如下：
{report_text}
"""

    def _build_trend_analysis_prompt(self, current_report: str, previous_report: str, company_name: str) -> str:
        """构建趋势分析提示词"""
        return f"""你是一位专业的财务分析师，请对比分析以下公司当前财务报告与上期财务报告，识别关键财务指标的变化趋势。

公司名称: {company_name}

请重点关注以下方面的变化趋势：
1. 营业收入和净利润的变化及原因
2. 毛利率、净利率等盈利能力指标的变化
3. 费用结构的变化
4. 现金流状况的变化
5. 资产负债结构的变化
6. 主营业务构成的变化
7. 重大投资或融资活动的变化

请以JSON格式返回分析结果，包含以下字段：
1. trend_summary: 趋势分析摘要（Markdown格式）
2. trend_data: 包含关键指标变化的对象，至少应包含以下子字段：
   - revenue_change: 营业收入变化情况
   - profit_change: 利润变化情况
   - margin_change: 利润率变化情况
   - expense_change: 费用结构变化情况
   - cash_flow_change: 现金流变化情况
   - significant_changes: 其他重大变化数组

当前财务报告内容：
{current_report}

上期财务报告内容：
{previous_report}
"""

    def _build_risk_analysis_prompt(self, report_text: str, company_name: str) -> str:
        """构建风险分析提示词"""
        return f"""你是一位专业的财务风险分析师，请从以下公司的财务报告中识别潜在的财务风险因素。

公司名称: {company_name}

请重点关注以下方面的风险：
1. 流动性风险（现金流、短期偿债能力等）
2. 盈利能力风险（利润下滑、成本上升等）
3. 资产质量风险（应收账款、存货、商誉等）
4. 负债风险（高负债率、债务结构不合理等）
5. 经营风险（主营业务波动、依赖单一客户等）
6. 行业风险（行业竞争、政策变化等）
7. 公司披露的风险提示部分

请以JSON格式返回分析结果，包含以下字段：
1. risk_summary: 风险分析摘要（Markdown格式）
2. risk_factors: 风险因素数组，每个风险因素包含：
   - category: 风险类别
   - description: 风险描述
   - severity: 风险严重程度（high/medium/low）
   - evidence: 报告中的相关证据
   - suggestion: 应对建议

财务报告内容如下：
{report_text}
"""
