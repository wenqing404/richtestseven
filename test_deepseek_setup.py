#!/usr/bin/env python3
"""
测试DeepSeek API配置是否正确
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_deepseek_config():
    """测试DeepSeek配置"""
    print("=== DeepSeek API 配置测试 ===\n")
    
    # 检查API密钥
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if api_key:
        print(f"✅ DEEPSEEK_API_KEY: 已设置 ({api_key[:10]}...{api_key[-4:]})")
    else:
        print("❌ DEEPSEEK_API_KEY: 未设置")
        return False
    
    # 检查默认模型
    default_model = os.environ.get("DEFAULT_LLM_MODEL", "deepseek-chat")
    print(f"✅ DEFAULT_LLM_MODEL: {default_model}")
    
    # 检查API基础URL
    api_base = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    print(f"✅ DEEPSEEK_API_BASE: {api_base}")
    
    # 测试环境变量是否在llm_analysis_service中正确读取
    try:
        from app.services.llm_analysis_service import LLMAnalysisService
        
        # 尝试初始化服务
        llm_service = LLMAnalysisService()
        print("✅ LLMAnalysisService: 初始化成功")
        print(f"✅ 当前使用模型: {llm_service.model_name}")
        
    except Exception as e:
        print(f"❌ LLMAnalysisService 初始化失败: {e}")
        return False
    
    print("\n=== 测试完成 ===")
    print("✅ 所有配置检查通过！")
    print("\n下一步:")
    print("1. 运行应用: python main.py")
    print("2. 访问 http://localhost:12000/llm-analysis")
    print("3. 测试财报分析功能")
    
    return True

if __name__ == "__main__":
    success = test_deepseek_config()
    sys.exit(0 if success else 1)
