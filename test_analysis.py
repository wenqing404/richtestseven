#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from app.services.analysis_service import FinancialReportAnalyzer

def main():
    """Test the financial report analyzer"""
    analyzer = FinancialReportAnalyzer(data_dir="data")
    
    # Test parameters
    stock_code = "600765"
    year = 2025
    report_type = "第一季度"  # Note: The actual file uses "年度" instead of "年度报告"
    
    # Analyze the report
    print(f"Analyzing report for {stock_code} {year} {report_type}...")
    result = analyzer.analyze_report(stock_code, year, report_type)
    
    # Print the result
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # Generate summary
    if result.get("status") == "success":
        print("\nGenerating summary...")
        summary = analyzer.generate_analysis_summary(result)
        print(summary)

if __name__ == "__main__":
    main()