#!/usr/bin/env python3
"""
测试补充公告检测功能
"""

import requests
import json
import sys

def test_analysis_api():
    """测试分析API对补充公告的处理"""
    print("测试分析API对补充公告的处理...")
    
    # 测试参数
    stock_code = "000001"
    year = 2023
    report_type = "年度报告"
    
    # 发送分析请求
    url = "http://localhost:12000/analysis/basic"
    data = {
        "stock_code": stock_code,
        "year": year,
        "report_type": report_type
    }
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        
        result = response.json()
        print(f"API响应状态码: {response.status_code}")
        
        # 检查是否为补充公告
        if result.get("status") == "partial" and result.get("report_type") == "补充公告":
            print("✅ 成功检测到补充公告")
            print(f"公司名称: {result.get('basic_info', {}).get('company_name')}")
            print(f"报告期间: {result.get('basic_info', {}).get('report_period')}")
            print(f"内容预览: {result.get('report_content', '')[:100]}...")
        else:
            print("❌ 未检测到补充公告")
            print(f"状态: {result.get('status')}")
            print(f"消息: {result.get('message')}")
        
        # 保存完整响应到文件
        with open("supplementary_test_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"完整响应已保存到 supplementary_test_result.json")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_analysis_api()
    print("测试完成")