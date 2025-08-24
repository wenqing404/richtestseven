# 财报数据爬虫与智能分析系统

一个基于FastAPI的财务报告爬虫与智能分析系统，用于从各种公开渠道获取企业财务报告原始文件，并提供基于规则和大语言模型的智能分析功能。

## 功能特点

- 从巨潮资讯网等公开渠道爬取财务报告PDF文件
- 提取PDF文本内容，便于后续分析
- 提供Web界面，方便用户操作
- 支持报告下载和预览
- 基于规则的财报分析功能，提取关键财务指标
- 基于大语言模型(LLM)的智能财报分析，提供深度洞察和投资建议

## 技术栈

- **后端**: FastAPI, Python 3.9+
- **前端**: Bootstrap 5, JavaScript, Chart.js
- **数据处理**: pdfplumber, requests, litellm
- **AI模型**: DeepSeek Chat/Coder/LLM (支持多种模型)
- **部署**: Docker

## 快速开始

### 使用Docker

```bash
# 构建Docker镜像
docker build -t financial-platform .

# 运行容器
docker run -p 12000:12000 -v $(pwd)/data:/app/data financial-platform
```

### 本地开发

1. 克隆仓库

```bash
git clone https://github.com/yourusername/financial-platform.git
cd financial-platform
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 运行应用

```bash
uvicorn main:app --host 0.0.0.0 --port 12000 --reload
```

4. 访问应用

打开浏览器，访问 http://localhost:12000

## 使用指南

### 爬取财报

1. 在导航栏中点击"爬取财报"
2. 输入股票代码（例如：000001）
3. 选择报告年份
4. 选择报告类型（年度报告、半年度报告等）
5. 点击"开始爬取"按钮
6. 等待爬取完成，可以下载或分析报告

### 基础财报分析

1. 在导航栏中点击"财报分析"
2. 选择已爬取的报告
3. 点击"开始分析"按钮
4. 查看分析结果，包括关键财务指标和可视化图表

### LLM智能分析

1. 在导航栏中点击"智能分析"
2. 输入股票代码、选择报告年份和类型
3. 选择分析模型（GPT-3.5或GPT-4）
4. 点击"开始智能分析"按钮
5. 查看深度分析结果，包括财务指标解读、业务分析和投资建议

## 数据来源

- 巨潮资讯网 (www.cninfo.com.cn)
- 上海证券交易所 (www.sse.com.cn)
- 深圳证券交易所 (www.szse.cn)
- 其他公开渠道

## 注意事项

- 本系统仅用于学习和研究目的
- 请遵守相关网站的使用条款和robots.txt规定
- 请合理控制爬取频率，避免对目标网站造成过大负载
- 仅获取公开披露的财务数据
- 使用LLM分析功能需要配置DeepSeek API密钥（在.env文件中设置）
- LLM分析结果仅供参考，不构成投资建议，请自行判断投资风险

## 许可证

MIT
