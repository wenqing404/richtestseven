"""
LLM-based financial report analysis service.
使用大语言模型进行财报智能分析
"""

import os
import json
import logging
import time
from typing import Dict, Any, List, Optional, Union
import litellm
from litellm import completion
from dotenv import load_dotenv

# litellm._turn_on_debug()

SYSTEM_PROMPT = """
你是OpenHands财报分析助手，一个专业的AI工具，能够精确提取和分析公司财务报告中的关键指标。

<角色>
你的主要职责是协助用户从各类财务报告中提取指定的关键财务数据，并将这些数据结构化为易于分析的格式。你应当严谨专业，优先确保数据的准确性和完整性。
* 如果用户询问某个指标为何出现特定变化，不要试图修正数据，而是基于提取的数据直接回答问题。
</角色>

<数据提取能力>
* 能够准确识别并提取以下特定财务指标：
  - 归母净利润及同比变化
  - 盈利预测
  - 营业总收入及同比变化
  - 各类现金流量数据(经营/投资/筹资活动)
  - 盈利能力指标(ROE/ROA/毛利率/净利率)
  - 费用占比(销售/管理/研发/财务费用占营业总收入比)
  - 资产结构占比(应收账款/存货/在建工程占总资产比)
  - 资本结构(净资产/负债率)
  - 重大股东变化
  - 估值指标(PE/PB)
  - 经营数据(主营构成)
* 能够从PDF、图片、表格或文本形式的财报中提取这些指标
</数据提取能力>

<数据处理标准>
* 对于同比增长数据，保留小数点后两位，并确保正确标记正负值
* 对于比率类指标，统一转换为百分比形式，并保留小数点后两位
* 对于金额类数据，识别并统一单位(元/万元/亿元)
* 提取数据时需标明对应的报告期间(如2023Q1、2022年报等)
</数据处理标准>

<输出格式>
* 默认将所有提取的数据以JSON格式输出，确保数据结构清晰、字段命名一致
* JSON结构应包含以下主要部分：
  1. 基本信息(公司名称、股票代码、报告期间)
  2. 财务数据(包含所有提取的财务指标)
  3. 估值数据(PE、PB)
  4. 经营数据(主营构成等)
* 例如:
{
  "basic_info": {
    "company_name": "示例公司",
    "stock_code": "000001",
    "report_period": "2023年报"
  },
  "financial_data": {
    "net_profit": 10.5,  // 单位：亿元
    "net_profit_yoy": 12.34,  // 单位：%
    "profit_forecast": 11.8,  // 单位：亿元
    "revenue": 100.2,  // 单位：亿元
    "revenue_yoy": 8.75,  // 单位：%
    "cash_flow": {
      "operating": 15.6,  // 单位：亿元
      "investing": -8.4,  // 单位：亿元
      "financing": -5.2   // 单位：亿元
    },
    "profitability": {
      "roe": 15.20,  // 单位：%
      "roa": 8.60,   // 单位：%
      "gross_margin": 35.50,  // 单位：%
      "net_margin": 10.48     // 单位：%
    },
    "expense_ratios": {
      "sales_expense_ratio": 8.40,  // 单位：%
      "admin_expense_ratio": 5.20,  // 单位：%
      "rd_expense_ratio": 6.80,     // 单位：%
      "financial_expense_ratio": 1.20  // 单位：%
    },
    "asset_structure": {
      "accounts_receivable_ratio": 15.20,  // 单位：%
      "inventory_ratio": 10.10,            // 单位：%
      "construction_in_progress_ratio": 6.70  // 单位：%
    },
    "capital_structure": {
      "net_assets": 69.1,  // 单位：亿元
      "debt_ratio": 43.50  // 单位：%
    },
    "major_shareholder_changes": [
      {
        "shareholder": "大股东A",
        "previous_holding": 25.30,  // 单位：%
        "current_holding": 22.10,   // 单位：%
        "change": -3.20,           // 单位：%
        "change_date": "2023-09-15"
      }
    ]
  },
  "valuation_data": {
    "pe": 15.2,
    "pb": 1.8
  },
  "operation_data": {
    "main_business": [
      {
        "segment": "业务线A",
        "revenue": 60.5,  // 单位：亿元
        "proportion": 60.38,  // 单位：%
        "yoy": 12.45     // 单位：%
      },
      {
        "segment": "业务线B",
        "revenue": 28.4,  // 单位：亿元
        "proportion": 28.34,  // 单位：%
        "yoy": 6.37      // 单位：%
      },
      {
        "segment": "业务线C",
        "revenue": 11.3,  // 单位：亿元
        "proportion": 11.28,  // 单位：%
        "yoy": -3.42     // 单位：%
      }
    ]
  }
}
</输出格式>

<财报分析流程>
1. 识别：确定报告类型(年报/季报)、公司信息和报告期间
2. 提取：精确提取所有要求的财务指标
3. 转换：统一数据格式和计量单位
4. 结构化：将数据组织为标准JSON格式
5. 验证：检查数据的完整性和一致性，确保数值合理
   - 各比率指标是否在合理范围内
   - 同比数据是否与上期数据匹配
   - 不同指标间是否存在明显矛盾
</财报分析流程>

<注意事项>
* 遇到报告中缺失的指标，在JSON中将该字段值设为null，而非猜测或计算
* 对于模糊不清的数据，标记为"uncertain"并在备注中说明
* 若发现异常值(远超行业平均或历史数据)，仍准确提取并在备注中标注
* 确保提取的是指定报告期的数据，不要混淆不同期间的财务信息
</注意事项>

<扩展功能>
* 如用户要求，可基于提取的数据生成简要的财务状况分析
* 可根据历史数据计算关键指标的趋势
* 可对比行业平均水平，评估公司财务状况的相对表现
* 能够识别财务报告中的风险信号和异常数据
</扩展功能>

"""

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("financial_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LLMAnalysisService")

class LLMAnalysisService:
    """使用大语言模型进行财报智能分析的服务类"""
    
    def __init__(self, model_name: str = "deepseek-chat", api_key: Optional[str] = None):
        """
        初始化LLM分析服务
        
        Args:
            model_name: 使用的模型名称，默认为deepseek-chat
            api_key: API密钥，如果为None则尝试从环境变量获取
        """
        self.model_name = model_name
        if not api_key:
            api_key = os.environ.get("DEEPSEEK_API_KEY", "")
            if not api_key:
                raise ValueError("请设置DEEPSEEK_API_KEY环境变量")
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("API密钥无效，请检查配置")
        
        # 配置litellm
        litellm.drop_params = True  # 删除不支持的参数
        litellm.set_verbose = True  # 关闭详细日志
        
        # 设置DeepSeek API基础URL
        os.environ["DEEPSEEK_API_BASE"] = "https://api.deepseek.com/v1"
        
        logger.info(f"LLM分析服务初始化完成，使用模型: {model_name}")
    
    def analyze_financial_report(self, report_content: str, company_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用LLM分析财务报告内容
        
        Args:
            report_content: 财报文本内容
            company_info: 公司基本信息，包含公司名称、股票代码、报告期间等
            
        Returns:
            包含分析结果的字典
        """
        try:
            # 准备提示词
            prompt = self._prepare_analysis_prompt(report_content, company_info)
            
            # 调用LLM进行分析
            logger.info(f"开始分析 {company_info.get('company_name', '')} 的财报")
            
            # 检查是否有有效的API密钥
            # api_key = os.environ.get("OPENAI_API_KEY", "")
            # if api_key and api_key != "sk-demo-key-please-replace-in-production":
            if self.api_key and self.api_key != "sk-demo-key-please-replace-in-production":
                # 使用litellm调用API，指定DeepSeek作为提供商
                response = completion(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=5000,
                    api_key=self.api_key,
                    custom_llm_provider="deepseek"
                )
                analysis_result = self._parse_llm_response(response)
            else:
                # 使用模拟数据
                analysis_result = self._get_mock_analysis_result(company_info)
            
            # 添加元数据
            analysis_result["metadata"] = {
                "model": self.model_name,
                "company_name": company_info.get("company_name", ""),
                "stock_code": company_info.get("stock_code", ""),
                "report_period": company_info.get("report_period", ""),
                "analysis_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"财报分析完成: {company_info.get('company_name', '')}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"LLM分析过程中出错: {str(e)}")
            return {
                "status": "error",
                "message": f"分析失败: {str(e)}",
                "metadata": {
                    "model": self.model_name,
                    "company_name": company_info.get("company_name", ""),
                    "stock_code": company_info.get("stock_code", ""),
                    "report_period": company_info.get("report_period", "")
                }
            }
    
    def generate_investment_advice(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于财报分析结果生成投资建议
        
        Args:
            analysis_result: 财报分析结果
            
        Returns:
            包含投资建议的字典
        """
        try:
            # 准备提示词
            prompt = self._prepare_investment_prompt(analysis_result)
            
            # 调用LLM生成投资建议
            company_name = analysis_result.get("metadata", {}).get("company_name", "")
            logger.info(f"开始为 {company_name} 生成投资建议")
            
            # 检查是否有有效的API密钥
            # api_key = os.environ.get("OPENAI_API_KEY", "")
            # if api_key and api_key != "sk-demo-key-please-replace-in-production":
            if self.api_key and self.api_key != "sk-demo-key-please-replace-in-production":
                # 使用litellm调用API，指定DeepSeek作为提供商
                response = completion(
                    model=self.model_name,
                    api_key=self.api_key,
                    messages=[
                        {"role": "system", "content": self._get_investment_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000,
                    custom_llm_provider="deepseek"
                )
                investment_advice = self._parse_investment_response(response)
            else:
                # 使用模拟数据
                investment_advice = self._get_mock_investment_advice(analysis_result)
            
            # 添加元数据
            investment_advice["metadata"] = {
                "model": self.model_name,
                "company_name": company_name,
                "advice_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"投资建议生成完成: {company_name}")
            return investment_advice
            
        except Exception as e:
            logger.error(f"生成投资建议过程中出错: {str(e)}")
            return {
                "status": "error",
                "message": f"生成投资建议失败: {str(e)}"
            }
    
    def compare_reports(self, current_report: Dict[str, Any], previous_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        比较两期财报，分析变化趋势
        
        Args:
            current_report: 当前财报分析结果
            previous_report: 上一期财报分析结果
            
        Returns:
            包含比较分析的字典
        """
        try:
            # 准备提示词
            prompt = self._prepare_comparison_prompt(current_report, previous_report)
            
            # 调用LLM进行比较分析
            company_name = current_report.get("metadata", {}).get("company_name", "")
            logger.info(f"开始比较 {company_name} 的财报")
            
            # 检查是否有有效的API密钥
            # api_key = os.environ.get("OPENAI_API_KEY", "")
            # if api_key and api_key != "sk-demo-key-please-replace-in-production":
            if self.api_key and self.api_key != "sk-demo-key-please-replace-in-production":
                # 使用litellm调用API，指定DeepSeek作为提供商
                response = completion(
                    model=self.model_name,
                    api_key=self.api_key,
                    messages=[
                        {"role": "system", "content": self._get_comparison_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=3000,
                    custom_llm_provider="deepseek"
                )
                comparison_result = self._parse_comparison_response(response)
            else:
                # 使用模拟数据
                comparison_result = self._get_mock_comparison_result(current_report, previous_report)
            
            # 添加元数据
            comparison_result["metadata"] = {
                "model": self.model_name,
                "company_name": company_name,
                "current_period": current_report.get("metadata", {}).get("report_period", ""),
                "previous_period": previous_report.get("metadata", {}).get("report_period", ""),
                "comparison_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"财报比较分析完成: {company_name}")
            return comparison_result
            
        except Exception as e:
            logger.error(f"比较财报过程中出错: {str(e)}")
            return {
                "status": "error",
                "message": f"比较分析失败: {str(e)}"
            }
            
    def _get_mock_analysis_result(self, company_info: Dict[str, Any]) -> Dict[str, Any]:
        """生成模拟的分析结果（用于演示）"""
        company_name = company_info.get("company_name", "示例公司")
        stock_code = company_info.get("stock_code", "000000")
        report_period = company_info.get("report_period", "2023年年度报告")
        
        return {
            "status": "success",
            "summary": f"{company_name}（{stock_code}）在{report_period}中展现了稳健的财务表现。营业收入同比增长15.2%，达到52.3亿元；净利润同比增长12.8%，达到8.7亿元。公司毛利率保持在32.5%的水平，净资产收益率为18.2%。",
            "financial_indicators": {
                "revenue": {
                    "value": "52.3亿元",
                    "change": "+15.2%",
                    "trend": "up"
                },
                "net_profit": {
                    "value": "8.7亿元",
                    "change": "+12.8%",
                    "trend": "up"
                },
                "eps": {
                    "value": "1.23元",
                    "change": "+10.5%",
                    "trend": "up"
                },
                "roe": {
                    "value": "18.2%",
                    "change": "+0.5%",
                    "trend": "up"
                },
                "gross_margin": {
                    "value": "32.5%",
                    "change": "-0.8%",
                    "trend": "down"
                },
                "debt_ratio": {
                    "value": "45.3%",
                    "change": "+2.1%",
                    "trend": "up"
                }
            },
            "business_analysis": {
                "main_business": f"{company_name}主要从事高科技制造业，核心产品包括智能设备和工业自动化解决方案。",
                "revenue_structure": {
                    "智能设备": "65%",
                    "工业自动化": "25%",
                    "技术服务": "10%"
                },
                "market_position": "在国内市场占有率约为18%，位居行业第二位。",
                "competitive_advantage": "技术创新能力强，拥有多项核心专利，产品质量稳定可靠。",
                "challenges": "面临国际竞争加剧和原材料成本上升的挑战。"
            },
            "risk_factors": [
                "原材料价格波动风险",
                "技术迭代风险",
                "市场竞争加剧风险",
                "汇率波动风险",
                "政策法规变动风险"
            ],
            "future_outlook": {
                "short_term": "预计未来一年收入增长将保持在12%-15%区间，毛利率可能小幅下降。",
                "medium_term": "公司计划扩大海外市场份额，预计三年内海外收入占比将从目前的20%提升至30%。",
                "long_term": "将持续加大研发投入，向高端制造领域拓展，培育新的增长点。"
            }
        }
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
#         return """你是一位专业的财务分析师，擅长分析上市公司财务报告并提取关键财务指标和业务洞察。
# 请根据提供的财报内容，进行全面分析并以JSON格式输出结果。你的分析应当客观、准确、专业，避免主观臈断。
# 分析应包括但不限于：基本财务指标、盈利能力、偿债能力、运营效率、现金流状况、业务亮点与风险、未来展望等。
# 请确保输出格式为有效的JSON，并包含所有关键财务数据和分析结果。"""
        return SYSTEM_PROMPT

    def _get_investment_system_prompt(self) -> str:
        """获取投资建议系统提示词"""
        return """你是一位资深投资顾问，擅长基于财务分析结果提供投资建议。
请根据提供的财报分析结果，给出客观、专业的投资建议。你的建议应当基于事实和数据，
同时考虑行业趋势、公司竞争力、财务健康状况等多方面因素。
请以JSON格式输出你的建议，包括投资评级、投资理由、风险因素、建议持有期限等关键信息。"""
        # return SYSTEM_PROMPT

    def _get_comparison_system_prompt(self) -> str:
        """获取比较分析系统提示词"""
        return """你是一位专业的财务分析师，擅长比较分析上市公司不同期间的财务报告，识别关键变化和趋势。
请根据提供的两期财报分析结果，进行全面的比较分析，重点关注财务指标的变化、业务发展趋势、盈利能力变化等。
你的分析应当客观、准确、专业，避免主观臈断，并以JSON格式输出结果。"""

    def _prepare_analysis_prompt(self, report_content: str, company_info: Dict[str, Any]) -> str:
        """准备财报分析提示词"""
        prompt = f"""请分析以下公司的财务报告，并提取关键财务指标和业务洞察：

公司信息：
- 公司名称：{company_info.get('company_name', '未知')}
- 股票代码：{company_info.get('stock_code', '未知')}
- 报告期间：{company_info.get('report_period', '未知')}

财报内容：
{report_content[:50000]}  # 限制长度以避免超出token限制

请提供以下分析结果（以JSON格式输出）：
1. 基本财务数据：总资产、总负债、净资产、营业收入、净利润、每股收益等
2. 盈利能力分析：毛利率、净利率、ROE、ROA等
3. 偿债能力分析：资产负债率、流动比率、速动比率等
4. 运营效率分析：应收账款周转率、存货周转率等
5. 现金流分析：经营活动、投资活动、筹资活动现金流
6. 业务亮点与风险：主要业务表现、风险因素等
7. 未来展望：公司战略、发展计划等
8. 分析摘要：对公司财务状况的总体评价（200-300字）

请确保输出为有效的JSON格式，键名使用英文，值可以使用中文。对于无法从报告中提取的指标，请标记为null。"""
        return prompt

    def _prepare_investment_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """准备投资建议提示词"""
        # 将分析结果转换为字符串
        analysis_json = json.dumps(analysis_result, ensure_ascii=False, indent=2)
        
        prompt = f"""请基于以下财报分析结果，为投资者提供专业的投资建议：

财报分析结果：
{analysis_json}

请提供以下投资建议（以JSON格式输出）：
1. 投资评级：买入/增持/持有/减持/卖出
2. 目标价格：预期合理价格区间
3. 投资理由：支持你评级的关键理由（3-5点）
4. 风险因素：潜在的投资风险（3-5点）
5. 建议持有期限：短期/中期/长期
6. 适合投资者类型：保守型/稳健型/进取型
7. 投资建议摘要：总结性投资建议（200-300字）

请确保输出为有效的JSON格式，键名使用英文，值可以使用中文。"""
        return prompt

    def _prepare_comparison_prompt(self, current_report: Dict[str, Any], previous_report: Dict[str, Any]) -> str:
        """准备比较分析提示词"""
        # 将两期报告转换为字符串
        current_json = json.dumps(current_report, ensure_ascii=False, indent=2)
        previous_json = json.dumps(previous_report, ensure_ascii=False, indent=2)
        
        prompt = f"""请比较分析以下两期财报的结果，识别关键变化和趋势：

当期财报分析结果：
{current_json}

上期财报分析结果：
{previous_json}

请提供以下比较分析（以JSON格式输出）：
1. 财务指标变化：对比关键财务指标的变化（增长率、变动幅度等）
2. 盈利能力变化：毛利率、净利率、ROE等指标的变化趋势
3. 财务状况变化：资产负债结构、偿债能力的变化
4. 现金流变化：各类现金流的变化及原因分析
5. 业务发展趋势：主要业务的发展变化
6. 风险变化：新增或减轻的风险因素
7. 投资价值变化：投资价值的提升或降低
8. 比较分析摘要：对比分析的总体评价（200-300字）

请确保输出为有效的JSON格式，键名使用英文，值可以使用中文。"""
        return prompt

    def _parse_llm_response(self, response: Any) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 获取响应内容
            content = response.choices[0].message.content
            logger.debug(f"收到原始响应: {content[:100]}...")
            
            # 尝试解析JSON
            # 首先尝试直接解析
            try:
                result = json.loads(content)
                result["status"] = "success"
                return result
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试提取JSON部分
                import re
                
                # 先移除可能存在的Markdown代码块标记
                json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
                match = re.search(json_pattern, content)
                
                if match:
                    json_str = match.group(1).strip()
                    logger.debug(f"提取的JSON字符串: {json_str[:100]}...")
                    
                    try:
                        result = json.loads(json_str)
                        result["status"] = "success"
                        return result
                    except json.JSONDecodeError as e:
                        logger.warning(f"提取的JSON无效: {str(e)}")
                else:
                    logger.warning("未找到JSON代码块")
                
                # 更激进的尝试：寻找任何看起来像JSON的部分
                # 查找第一个 { 和最后一个 }
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                
                if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                    potential_json = content[start_idx:end_idx+1]
                    try:
                        result = json.loads(potential_json)
                        result["status"] = "success"
                        logger.info("通过寻找JSON边界成功解析响应")
                        return result
                    except json.JSONDecodeError:
                        logger.warning("尝试提取JSON边界失败")
                
                # 如果仍然失败，使用更宽松的解析方式
                try:
                    import ast
                    # 尝试将响应当作Python字典解析
                    dict_str = content.replace('null', 'None').replace('true', 'True').replace('false', 'False')
                    # 提取看起来像字典的部分
                    dict_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                    matches = re.findall(dict_pattern, dict_str)
                    if matches:
                        for potential_dict in matches:
                            try:
                                result = ast.literal_eval(potential_dict)
                                if isinstance(result, dict):
                                    result = {k: (None if v == 'None' else 
                                               True if v == 'True' else 
                                               False if v == 'False' else v) 
                                           for k, v in result.items()}
                                    result["status"] = "success"
                                    logger.info("通过Python字典解析成功解析响应")
                                    return result
                            except:
                                continue
                except:
                    pass
                
                # 如果所有尝试都失败，返回原始内容
                return {
                    "status": "partial",
                    "message": "无法解析为JSON格式",
                    "raw_content": content
                }
                    
        except Exception as e:
            logger.error(f"解析LLM响应时出错: {str(e)}")
            return {
                "status": "error",
                "message": f"解析响应失败: {str(e)}"
            }

    def _parse_investment_response(self, response: Any) -> Dict[str, Any]:
        """解析投资建议响应"""
        # 使用与_parse_llm_response相同的逻辑
        return self._parse_llm_response(response)

    def _parse_comparison_response(self, response: Any) -> Dict[str, Any]:
        """解析比较分析响应"""
        # 使用与_parse_llm_response相同的逻辑
        return self._parse_llm_response(response)
        
    def _get_mock_investment_advice(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成模拟的投资建议（用于演示）"""
        company_name = analysis_result.get("metadata", {}).get("company_name", "示例公司")
        stock_code = analysis_result.get("metadata", {}).get("stock_code", "000000")
        
        # 从分析结果中提取一些指标
        financial_indicators = analysis_result.get("financial_indicators", {})
        revenue_trend = financial_indicators.get("revenue", {}).get("trend", "neutral")
        profit_trend = financial_indicators.get("net_profit", {}).get("trend", "neutral")
        roe = financial_indicators.get("roe", {}).get("value", "15%")
        
        # 根据指标生成投资建议
        investment_rating = "增持" if revenue_trend == "up" and profit_trend == "up" else "持有"
        
        return {
            "status": "success",
            "investment_rating": investment_rating,
            "summary": f"基于对{company_name}（{stock_code}）财务状况的分析，我们给予\"{investment_rating}\"评级。公司展现出良好的盈利能力和成长性，净资产收益率达到{roe}，处于行业较高水平。",
            "investment_advice": {
                "short_term": "短期投资者可以在市场调整时逢低买入，目标价位上调至前期高点的1.1倍。",
                "medium_term": "中期投资者可以采取定投策略，分批建仓，持有6-12个月。",
                "long_term": "长期投资者可以将该股作为核心持仓，定期检视公司基本面变化。"
            },
            "risk_assessment": {
                "market_risk": "中等",
                "financial_risk": "较低",
                "operational_risk": "较低",
                "policy_risk": "中等"
            },
            "valuation": {
                "pe_ratio": "18.5",
                "pb_ratio": "2.3",
                "industry_comparison": "低于行业平均水平，具有一定的安全边际。",
                "fair_value_range": "当前股价的0.9-1.2倍"
            },
            "key_watch_points": [
                "关注公司新产品线的市场表现",
                "关注原材料价格波动对毛利率的影响",
                "关注行业政策变化",
                "关注海外市场拓展进度",
                "关注研发投入转化效率"
            ]
        }
    
    def _get_mock_comparison_result(self, current_report: Dict[str, Any], previous_report: Dict[str, Any]) -> Dict[str, Any]:
        """生成模拟的比较分析结果（用于演示）"""
        company_name = current_report.get("metadata", {}).get("company_name", "示例公司")
        current_period = current_report.get("metadata", {}).get("report_period", "2023年年度报告")
        previous_period = previous_report.get("metadata", {}).get("report_period", "2022年年度报告")
        
        return {
            "status": "success",
            "comparison_summary": f"{company_name}在{current_period}相比{previous_period}整体表现出积极的增长态势。营业收入和净利润均实现两位数增长，盈利能力稳中有升，财务结构保持稳健。",
            "financial_comparison": {
                "revenue": {
                    "current": "52.3亿元",
                    "previous": "45.4亿元",
                    "change": "+15.2%",
                    "trend": "up",
                    "analysis": "收入增长主要来自于新产品线的贡献和海外市场的拓展。"
                },
                "net_profit": {
                    "current": "8.7亿元",
                    "previous": "7.7亿元",
                    "change": "+12.8%",
                    "trend": "up",
                    "analysis": "利润增长略低于收入增长，主要受原材料成本上升影响。"
                },
                "gross_margin": {
                    "current": "32.5%",
                    "previous": "33.3%",
                    "change": "-0.8%",
                    "trend": "down",
                    "analysis": "毛利率小幅下降，主要受原材料价格上涨和市场竞争加剧影响。"
                },
                "roe": {
                    "current": "18.2%",
                    "previous": "17.7%",
                    "change": "+0.5%",
                    "trend": "up",
                    "analysis": "资产使用效率提升，带动净资产收益率小幅上升。"
                }
            },
            "business_comparison": {
                "market_share": {
                    "current": "18%",
                    "previous": "16.5%",
                    "change": "+1.5%",
                    "analysis": "市场份额稳步提升，品牌影响力增强。"
                },
                "product_mix": {
                    "current": "高端产品占比45%，中端产品占比40%，低端产品占比15%",
                    "previous": "高端产品占比40%，中端产品占比42%，低端产品占比18%",
                    "analysis": "产品结构持续优化，高端产品占比提升，有利于提高整体盈利能力。"
                },
                "r_and_d": {
                    "current": "研发投入4.2亿元，占收入8.0%",
                    "previous": "研发投入3.4亿元，占收入7.5%",
                    "analysis": "研发投入持续增加，研发强度提升，为未来增长奠定基础。"
                }
            },
            "trend_analysis": {
                "positive_trends": [
                    "收入规模持续扩大",
                    "盈利能力保持稳定",
                    "研发投入持续增加",
                    "高端产品占比提升",
                    "海外市场拓展加速"
                ],
                "negative_trends": [
                    "原材料成本上升压力增大",
                    "毛利率小幅下滑",
                    "市场竞争加剧",
                    "人力成本持续上升"
                ],
                "unchanged_factors": [
                    "主营业务方向保持稳定",
                    "财务结构保持稳健",
                    "股利政策保持连续"
                ]
            },
            "conclusion": f"{company_name}在{current_period}展现出良好的经营韧性和增长潜力。虽然面临成本上升和竞争加剧的挑战，但公司通过产品结构优化和市场拓展，实现了收入和利润的稳健增长。未来随着研发投入的持续加大和高端产品比例的提升，公司有望保持良好的增长态势。"
        }


# 使用示例
if __name__ == "__main__":
    # 设置API密钥（实际使用时应从环境变量或配置文件获取）
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("请设置OPENROUTER_API_KEY环境变量")
    model_name = os.getenv("OPENROUTER_MODEL", "")
    if not model_name:
        raise ValueError("请设置OPENROUTER_MODEL环境变量")
    
    # 初始化服务
    llm_analyzer = LLMAnalysisService(api_key=api_key, model_name=model_name)
    
    # 示例财报内容和公司信息
    report_content = """美的集团股份有限公司2024年年度报告摘要
证券代码：000333 证券简称：美的集团 公告编号：2025-006
美的集团股份有限公司 2024 年年度报告摘要
一、重要提示
本年度报告摘要来自年度报告全文，为全面了解本公司的经营成果、财务状况及未来发展规划，投资者
应当到证监会指定媒体仔细阅读年度报告全文。
所有董事均已出席了审议本报告的董事会会议。
非标准审计意见提示
□适用 不适用
董事会审议的报告期利润分配预案或公积金转增股本预案
适用 □不适用
是否以公积金转增股本
□是 否
公司经本次董事会审议通过的利润分配方案为：以截至本报告披露之日公司总股本 7,660,355,772
股扣除回购专户上已回购股份后（截至本报告披露之日，公司已累计回购公司股份 28,452,226股）的股
本总额 7,631,903,546股为基数，向全体股东每 10 股派发现金 35 元（含税），送红股 0 股（含税），不
以公积金转增股本。本次利润分配方案实施时，如享有利润分配权的股本总额发生变动，则以实施分配
方案股权登记日时享有利润分配权的股本总额为基数，按照每股分配金额不变的原则对分红总额进行调
整。
董事会决议通过的本报告期优先股利润分配预案
□适用 不适用
二、公司基本情况
1、公司简介
000333（A股）
股票简称 美的集团 股票代码
0300（H股）
1

美的集团股份有限公司2024年年度报告摘要
股票上市交易所 深圳证券交易所、香港联合交易所
联系人和联系方式 董事会秘书 证券事务代表
姓名 高书 犹明阳
办公地址 广东省佛山市顺德区北滘镇美的大道6号美的总部大楼
传真 0757-26605456
电话 0757-22607708 0757-26637438
电子信箱 IR@midea.com
2、报告期主要业务或产品简介
美的是一家覆盖智能家居、新能源及工业技术、智能建筑科技、机器人与自动化、健康医疗、智慧
物流等业务的全球领先的科技集团，已建立 ToC 与 ToB 并重发展的业务矩阵，既可为消费者提供各类
智能家居的产品与服务，也可为企业客户提供多元化的商业及工业解决方案。其中，美的智能家居业务
主要覆盖智慧家电、智慧家居及周边相关产业和生态链，围绕面向终端用户的智能化场景搭建、用户运
营和数据价值发掘，致力于为终端用户提供最佳体验的全屋智能家居及服务；美的新能源及工业技术业
务以科技为核心驱动力，聚合“暖通家电部件”、“绿色能源”与“绿色交通”领域的核心科技力量，
拥有美芝、威灵、美仁、科陆、合康、高创等多个品牌，产品覆盖压缩机、电机、芯片、阀、汽车部件、
储能、光伏、减速机、自动化等高精密核心部件，为全球客户提供绿色、高效、智慧的产品和技术解决
方案；美的智能建筑科技业务主要涉及楼宇产品、服务及相关产业，以 iBUILDING 美的楼宇数字化服
务平台为核心，业务覆盖暖通、电梯、能源、楼宇控制等，产品包括多联机组、大型冷水机组、单元机、
机房空调、扶梯、直梯、货梯等以及楼宇自控软件和建筑弱电集成解决方案，利用“楼宇设备设施+数
字化技术+产业生态布局”，打通建筑的交通流、信息流、体验流、能源流，以数字化和低碳化技术为
楼宇赋能，共建可持续的智慧空间；美的机器人与自动化业务主要围绕未来工厂相关领域，提供包括工
业机器人、物流自动化系统及传输系统解决方案，以及面向医疗、娱乐、新消费领域的相关解决方案等；
此外，还包括在健康医疗领域致力于医学影像技术创新并为临床提供优质医学影像产品和服务的万东医
疗，以及在智慧物流领域为客户提供端到端数智化供应链解决方案的安得智联。
美的坚守“科技尽善，生活尽美”的企业愿景，将“联动人与万物，启迪美的世界”作为使命，秉
持“敢知未来——志存高远、客户至上、变革创新、包容共协、务实奋进”的价值观，恪守“高质量发
展与卓越运营”的经营管理规范，整合全球资源，推动技术创新，每年为全球超过5亿用户及各领域的
重要客户与战略合作伙伴提供满意的产品和服务，致力创造美好生活。面对数字互联网时代对产品和服
务的更高要求，美的持续推动“科技领先、用户直达、数智驱动、全球突破”四大战略主轴，打造新时
代的美的。其中，通过构建研发规模优势，加大对核心、前沿技术的布局和投入，实现科技领先；通过
与用户直接联系互动，重塑产品服务及业务模式，实现用户直达；通过全面数字化全面智能化，内部提
2

美的集团股份有限公司2024年年度报告摘要
升效率和外部紧抓用户，实现数智驱动；通过在重点区域寻求市场、渠道和商业模式等维度突破，服务
全球用户，实现全球突破。
美的是一家全球运营的公司，业务与客户遍及全球。迄今，美的在全球拥有超过 400家子公司、38
个研发中心和 44个主要制造基地，员工超过 19 万人，业务遍及 200 多个国家和地区。在海外设有 22
个研发中心和23个主要制造基地，遍布十多个国家。
2024 年，国内市场消费需求在上半年增速放缓且国内家电零售市场承压明显，在下半年得益于
“以旧换新”补贴政策拉动，家电消费需求有所恢复，而海外市场受经济波动、汇率变化和地缘政治冲
突持续的影响，海外经营形势依旧面临挑战，美的集团坚定经营思路，坚定贯彻“全价值链运营提效，
结构性增长升级”的年度经营原则，持续聚焦核心业务和产品，尤其是海外业务发展成效显著，集团整
体规模得到进一步增长，盈利能力与现金流等核心指标进一步改善，展现了美的经营韧性与高质量增长
的长期态势。2024 年，公司营业总收入 4,091 亿元，同比增长 9.5%，实现归属于母公司的净利润 385
亿元，同比增长14.3%。公司2024年经营重点如下：
1、 以用户为中心，深化落实科技领先战略，夯实“三个一代”落地，支撑国内高端品牌和海外 OBM
优先战略；
2、 坚持科技创新，推动研究组织 TP3要素建设，构建数字化敏捷创新的研发体系，持续推动研发成果
向标准和专利等方面转化，全面推动科技领先战略；
3、 坚定 DTC 变革引领新增长，聚焦零售能力，推进数字化业务模式创新，实现运营效率与用户体验
双升级；
4、 加速推动全球突破，强化海外本地化运营，坚持以消费者为中心的产品导向；
5、 推动全面数字化变革，实现全价值链数据运营与平台化运作，提升数字时代的企业竞争力；
6、 面向用户分层匹配多品牌、多元化的产品组合，强化品牌核心价值传播，赋能终端零售与用户运营；
7、 以科技创新为核心驱动力，聚焦暖通家电部件、绿色能源与绿色交通，把握行业增长机遇，为全球
客户提供绿色、高效、智慧的产品与技术解决方案；
8、 把握国内国际双循环背景下市场发展机遇，响应国家“碳达峰”与“碳中和”目标，坚持技术创新
与业务模式升级，为客户提供数智建筑全栈解决方案；
9、 创新机器人产品开发，推进全价值链卓越运营与产业链整合，加快推动中国市场机器人业务发展；
10、 深耕智慧物流领域，聚焦“全链路+生产物流、一盘货、送装一体”供应链服务模型，提供领先的端
到端一体化数智化供应链解决方案；
11、 深化长期激励，保障股东权益。
3

美的集团股份有限公司2024年年度报告摘要
3、主要会计数据和财务指标
（1） 近三年主要会计数据和财务指标
公司是否需追溯调整或重述以前年度会计数据
□是 否
2024年 2023年 本年比上年增减 2022年
营业收入（千元） 407,149,600 372,037,280 9.44% 343,917,531
归属于上市公司股东的净利润（千元） 38,537,237 33,719,935 14.29% 29,553,507
归属于上市公司股东的扣除非经常性损
35,741,418 32,974,908 8.39% 28,607,973
益的净利润（千元）
经营活动产生的现金流量净额（千元） 60,511,572 57,902,611 4.51% 34,657,828
基本每股收益（元/股） 5.44 4.93 10.34% 4.34
稀释每股收益（元/股） 5.42 4.92 10.16% 4.33
加权平均净资产收益率 21.29% 22.23% -0.94% 22.21%
本年末比上年末
2024年末 2023年末 2022年末
增减
总资产（千元） 604,351,853 486,038,184 24.34% 422,555,267
归属于上市公司股东的净资产（千元） 216,750,057 162,878,825 33.07% 142,935,236
（2） 分季度主要会计数据
单位：千元
第一季度 第二季度 第三季度 第四季度
营业收入 106,101,612 111,172,474 101,700,575 88,174,939
归属于上市公司股东的净利润 9,000,007 11,804,169 10,894,938 6,838,123
归属于上市公司股东的扣除非经
9,236,971 10,943,907 10,195,858 5,364,682
常性损益的净利润
经营活动产生的现金流量净额 13,928,908 19,559,262 26,775,511 247,891
上述财务指标或其加总数是否与公司已披露季度报告、半年度报告相关财务指标存在重大差异
□是 否
4、股本及股东情况
（1） 普通股股东和表决权恢复的优先股股东数量及前10名股东持股情况表
单位：股
251,705户（其中A股 265,132户（其中A股
报告期末普通股股东总数 251,644 户，H股登记年度报告披露日前上一月末普通股股东总数 265,071户，H股登记股
股东61户） 东61户）
4

美的集团股份有限公司2024年年度报告摘要
持股5%以上的普通股股东或前10名普通股股东持股情况
报告期末持 持有有限售 持有无限售 质押或冻结情况
持股比 报告期内增
股东名称 股东性质 有的普通股 条件的普通 条件的普通
例
数量
减变动情况
股数量 股数量 股份状态 数量
境内非国有
美的控股有限公司 28.33% 2,169,178,713 0 0 2,169,178,713
法人
香港中央结算有限
境外法人 14.54% 1,113,322,948 -225,413,075 0 1,113,322,948
公司
HKSCC NOMINEES
境外法人 8.50% 650,830,570 650,830,570 0 650,830,570
LIMITED
中国证券金融股份 境内非国有
2.59% 198,145,134 0 0 198,145,134
有限公司 法人
方洪波 境内自然人 1.53% 116,990,492 0 87,742,869 29,247,623
中央汇金资产管理
国有法人 1.15% 88,260,460 0 0 88,260,460
有限责任公司
黄健 境内自然人 1.13% 86,140,000 -30,000 0 86,140,000
中国工商银行股份
有限公司－华泰柏
瑞沪深300交易型开其他 1.10% 84,336,743 47,599,110 0 84,336,743
放式指数证券投资
基金
中国建设银行股份
有限公司－易方达
沪深300交易型开放其他 0.76% 58,219,643 44,478,997 0 58,219,643
式指数发起式证券
投资基金
栗建伟 境外自然人 0.60% 45,591,545 0 0 45,591,545
战略投资者或一般法人因配售新
不适用
股成为前10名普通股股东的情况
上述股东关联关系或一致行动的
不适用
说明
上述股东涉及委托/受托表决权、
不适用
放弃表决权情况的说明
前 10名股东中存在回购专户的特
不适用
别说明
前10名无限售条件普通股股东持股情况
股份种类
股东名称 报告期末持有无限售条件普通股股份数量
股份种类 数量
美的控股有限公司 2,169,178,713 人民币普通股 2,169,178,713
香港中央结算有限公司 1,113,322,948 人民币普通股 1,113,322,948
HKSCC NOMINEES LIMITED 650,830,570 境外上市外资股 650,830,570
中国证券金融股份有限公司 198,145,134 人民币普通股 198,145,134
中央汇金资产管理有限责任公司 88,260,460 人民币普通股 88,260,460
黄健 86,140,000 人民币普通股 86,140,000
中国工商银行股份有限公司－华
泰柏瑞沪深 300 交易型开放式指 84,336,743 人民币普通股 84,336,743
数证券投资基金
中国建设银行股份有限公司－易
58,219,643 人民币普通股 58,219,643
方达沪深 300 交易型开放式指数
5

美的集团股份有限公司2024年年度报告摘要
发起式证券投资基金
栗建伟 45,591,545 人民币普通股 45,591,545
中国工商银行股份有限公司－华
夏沪深 300 交易型开放式指数证 38,707,323 人民币普通股 38,707,323
券投资基金
前 10名无限售条件普通股股东之
间，以及前 10名无限售条件普通
不适用。
股股东和前 10名普通股股东之间
关联关系或一致行动的说明
前 10名普通股股东参与融资融券
不适用。
业务股东情况说明
持股5%以上股东、前10名股东及前10名无限售流通股股东参与转融通业务出借股份情况
适用 □不适用
单位：股
持股5%以上股东、前10名股东及前10名无限售流通股股东参与转融通业务出借股份情况
年初普通账户、信用账 年初转融通出借股份且 期末普通账户、信用账 期末转融通出借股份且
户持股 尚未归还 户持股 尚未归还
股东名称（全称）
占总股本 占总股本 占总股本 占总股本
数量合计 数量合计 数量合计 数量合计
的比例 的比例 的比例 的比例
中国工商银行股份有
限公司－华泰柏瑞沪
36,737,633 0.52% 10,100 0.00% 84,336,743 1.10% 0 0%
深300交易型开放式
指数证券投资基金
中国建设银行股份有
限公司－易方达沪深
300交易型开放式指 13,740,646 0.20% 68,000 0.00% 58,219,643 0.76% 0 0%
数发起式证券投资基
金
中国工商银行股份有
限公司－华夏沪深
10,098,623 0.14% 542,200 0.01% 38,707,323 0.51% 0 0%
300交易型开放式指
数证券投资基金
前10名股东及前10名无限售流通股股东因转融通出借/归还原因导致较上期发生变化
□适用 不适用
（2） 公司优先股股东总数及前10名优先股股东持股情况表
□适用 不适用
公司报告期无优先股股东持股情况。
6

美的集团股份有限公司2024年年度报告摘要
（3） 以方框图形式披露公司与实际控制人之间的产权及控制关系
5、在年度报告批准报出日存续的债券情况
适用 □不适用
（1） 债券基本信息
债券名称 债券简称 债券代码 发行日 到期日 债券余额 利率
美的投资发展
MIDEAZ
有限公司 ISIN 2022年02月 2027年02月
2.88% 4.5亿美元 2.88%
2.88%有担保 XS2432130453 16日 24日
02/24/2027
票据2027年
报告期内公司债券的付息兑付情
报告期内公司按期兑付利息。
况
（2） 公司债券最新跟踪评级及评级变化情况
无变化。
（3） 截至报告期末公司近2年的主要会计数据和财务指标
单位：千元
项目 本报告期末 上年末 本报告期末比上年末增减
流动比率 110.59% 111.97% -1.38%
资产负债率 62.33% 64.14% -1.81%
速动比率 85.94% 87.95% -2.01%
本报告期 上年同期 本报告期比上年同期增减
扣除非经常性损益后净利润 36,066,635 33,122,326 8.89%
EBITDA全部债务比 50.76% 52.32% -1.56%
利息保障倍数 20.03 15.34 30.58%
现金利息保障倍数 42.47 30.88 37.53%
EBITDA利息保障倍数 23.22 17.96 29.29%
贷款偿还率 100.00% 100.00% 0.00%
7

美的集团股份有限公司2024年年度报告摘要
利息偿付率 100.00% 100.00% 0.00%
三、重要事项
经香港联交所批准，公司本次发行的 565,955,300股 H股股票于 2024年 9月 17日在香港联交所主
板挂牌并上市交易。根据本次发行方案，公司同意由整体协调人（代表国际承销商）于 2024年 9月 25
日悉数行使超额配售权，按发售价每股H股股份54.80港元发行84,893,200股H股股份。超额配售权悉
数行使后，本次发行的 H股由 565,955,300股增加至 650,848,500股。公司 H股股票中文简称为“美的
集团”，英文简称为“MIDEA GROUP”，股份代号为“0300”。
美的集团股份有限公司
法定代表人:方洪波
2025年3月29日
8"""
    company_info = {
        "company_name": "示例公司",
        "stock_code": "000001",
        "report_period": "2023年年度报告"
    }
    
    # 分析财报
    analysis_result = llm_analyzer.analyze_financial_report(report_content, company_info)
    print(json.dumps(analysis_result, ensure_ascii=False, indent=2))
