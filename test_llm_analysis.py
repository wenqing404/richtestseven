#!/usr/bin/env python3
"""
测试LLM财报分析功能
"""

import os
import json
import logging
from app.services.llm_analysis_service import LLMAnalysisService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("llm_analysis_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LLMAnalysisTest")

def test_llm_analysis():
    """测试LLM分析服务"""
    # 设置API密钥（实际使用时应从环境变量获取）
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    
    if not api_key:
        logger.error("未设置DEEPSEEK_API_KEY环境变量")
        return
    
    # 初始化LLM分析服务
    llm_analyzer = LLMAnalysisService(api_key=api_key)
    
    # 示例财报内容
    report_content = """
    平安银行股份有限公司2023年年度报告摘要
    
    一、重要提示
    本年度报告摘要来自年度报告全文，为全面了解本公司的经营成果、财务状况及未来发展规划，投资者应当到证监会指定媒体仔细阅读年度报告全文。
    
    二、公司基本情况
    1、公司简介
    股票简称：平安银行
    股票代码：000001
    股票上市证券交易所：深圳证券交易所
    
    2、主要财务数据和财务指标
    公司是否需追溯调整或重述以前年度会计数据：否
    
    本报告期末：资产总额（百万元）4,899,596
    归属于普通股股东的净资产（百万元）468,315
    
    本报告期：营业收入（百万元）196,586
    归属于普通股股东的净利润（百万元）45,514
    归属于普通股股东的扣除非经常性损益的净利润（百万元）45,272
    经营活动产生的现金流量净额（百万元）-31,851
    基本每股收益（元/股）2.15
    稀释每股收益（元/股）2.15
    加权平均净资产收益率(%) 10.19
    
    3、公司业务概要
    平安银行是一家总部设在深圳的全国性股份制商业银行，前身为深圳发展银行，于2012年6月完成与原平安银行的合并，并更名为平安银行。本行业务范围包括公司业务、零售业务和金融市场业务。
    
    4、经营情况讨论与分析
    2023年，面对复杂多变的国内外经济形势，本行坚持"科技引领、零售突破、对公做精"十二字策略方针，持续深化数字化经营，加快推进全渠道经营，强化风险管控，实现了稳健发展。
    
    报告期内，本行实现营业收入1,965.86亿元，同比增长7.8%；净利润455.14亿元，同比增长8.1%；不良贷款率1.05%，较上年末下降0.02个百分点；拨备覆盖率290.28%，较上年末上升2.39个百分点。
    
    5、未来发展展望
    2024年，本行将继续坚持"科技引领、零售突破、对公做精"的十二字策略方针，持续深化数字化经营，加快推进全渠道经营，强化风险管控，实现高质量发展。
    """
    
    # 公司信息
    company_info = {
        "company_name": "平安银行",
        "stock_code": "000001",
        "report_period": "2023年年度报告"
    }
    
    try:
        # 分析财报
        logger.info("开始分析财报...")
        analysis_result = llm_analyzer.analyze_financial_report(report_content, company_info)
        
        # 保存分析结果
        with open("llm_analysis_result.json", "w", encoding="utf-8") as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        logger.info("分析结果已保存到 llm_analysis_result.json")
        
        # 生成投资建议
        logger.info("开始生成投资建议...")
        investment_advice = llm_analyzer.generate_investment_advice(analysis_result)
        
        # 保存投资建议
        with open("llm_investment_advice.json", "w", encoding="utf-8") as f:
            json.dump(investment_advice, f, ensure_ascii=False, indent=2)
        
        logger.info("投资建议已保存到 llm_investment_advice.json")
        
        logger.info("测试完成")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")

if __name__ == "__main__":
    test_llm_analysis()
