import requests
import json
import os
import time
import random
import hashlib
from pathlib import Path
import logging
from typing import Dict, Any, Tuple, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("financial_crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FinancialReportCrawler")

class CrawlerService:
    """爬虫服务类，提供爬取财报的接口"""
    
    def __init__(self, output_dir: str = "./data"):
        self.crawler = FinancialReportCrawler(output_dir)
        self.output_dir = Path(output_dir)
    
    def crawl_report(self, stock_code: str, year: int, report_type: str = "年度报告") -> Dict[str, Any]:
        """爬取财报"""
        return self.crawler.crawl_annual_report_from_cninfo(stock_code, year, report_type)
    
    def get_report_content(self, stock_code: str, year: int, report_type: str = "年度报告") -> Dict[str, Any]:
        """获取财报内容"""
        # 构造文件路径
        file_path = self.output_dir / stock_code / str(year) / f"{stock_code}_{year}_{report_type.replace('报告', '')}.txt"
        
        if not file_path.exists():
            # 如果文件不存在，尝试爬取
            result = self.crawl_report(stock_code, year, report_type)
            
            if result.get("crawler_metadata", {}).get("status") != "success":
                return {
                    "status": "failed",
                    "error_message": result.get("error_message", "获取财报失败")
                }
        
        # 读取文本内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 获取元数据
            metadata_path = self.output_dir / stock_code / str(year) / f"{stock_code}_{year}_{report_type.replace('报告', '')}_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {
                    "report_metadata": {
                        "company_name": "",
                        "stock_code": stock_code,
                        "report_type": report_type,
                        "report_period": f"{year}年{report_type}"
                    }
                }
            
            return {
                "status": "success",
                "report_content": content,
                "basic_info": {
                    "company_name": metadata.get("report_metadata", {}).get("company_name", ""),
                    "stock_code": stock_code,
                    "report_period": f"{year}年{report_type}"
                },
                "file_info": {
                    "text_path": str(file_path)
                }
            }
            
        except Exception as e:
            logger.error(f"读取财报内容时出错: {str(e)}")
            return {
                "status": "failed",
                "error_message": f"读取财报内容失败: {str(e)}"
            }
    
    def list_reports(self) -> List[Dict[str, Any]]:
        """列出所有已爬取的报告"""
        reports = []
        
        try:
            # 遍历数据目录
            for stock_dir in self.output_dir.iterdir():
                if stock_dir.is_dir():
                    for year_dir in stock_dir.iterdir():
                        if year_dir.is_dir():
                            # 查找元数据文件
                            for metadata_file in year_dir.glob("*_metadata.json"):
                                try:
                                    with open(metadata_file, 'r', encoding='utf-8') as f:
                                        metadata = json.load(f)
                                        reports.append(metadata)
                                except Exception as e:
                                    logger.error(f"读取元数据文件时出错: {metadata_file}, {str(e)}")
            
            return reports
            
        except Exception as e:
            logger.error(f"列出报告时出错: {str(e)}")
            return []

class FinancialReportCrawler:
    """财务报告爬虫类"""
    
    def __init__(self, output_dir: str = "./data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "http://www.cninfo.com.cn/new/fulltextSearch"
        }
        
    def calculate_checksum(self, file_path: Path) -> str:
        """计算文件SHA256校验和"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def download_file(self, url: str, save_path: Path) -> Tuple[bool, str]:
        """下载文件并返回成功状态和校验和"""
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            response = requests.get(url, headers=self.headers, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # 验证文件是否成功下载
            if save_path.exists() and save_path.stat().st_size > 0:
                checksum = self.calculate_checksum(save_path)
                logger.info(f"文件已成功下载: {save_path}")
                return True, checksum
            else:
                logger.error(f"文件下载失败: {save_path}")
                return False, ""
                
        except Exception as e:
            logger.error(f"下载文件时出错: {str(e)}")
            return False, ""
    
    def crawl_annual_report_from_cninfo(self, stock_code: str, year: int, report_type: str = "年度报告") -> Dict[str, Any]:
        """从巨潮资讯网爬取财务报告"""
        logger.info(f"开始爬取 {stock_code} {year}年 {report_type}")
        
        # 构建搜索关键词
        search_key = f"{stock_code} {year}年{report_type}"
        
        # 构造巨潮资讯网搜索URL和参数
        base_url = "http://www.cninfo.com.cn/new/fulltextSearch/full"
        params = {
            "searchkey": search_key,
            "sdate": "",
            "edate": "",
            "isfulltext": "false",
            "sortName": "pubdate",
            "sortType": "desc",
            "pageNum": 1,
            "pageSize": 10
        }
        
        try:
            # 增加随机延迟，避免反爬
            delay = random.uniform(2, 5)
            logger.info(f"等待 {delay:.2f} 秒后发送请求")
            time.sleep(delay)
            
            # 发送请求
            response = requests.post(base_url, headers=self.headers, data=params, timeout=30)
            response.raise_for_status()
            
            # 解析JSON响应
            result = response.json()
            
            if result.get("announcements") and len(result["announcements"]) > 0:
                # 获取第一条结果
                announcement = result["announcements"][0]
                
                # 获取公司名称、发布日期等信息
                company_name = announcement.get("secName", "")
                publish_date = announcement.get("announcementTime", "")
                
                # 构造PDF下载URL
                pdf_url = f"http://static.cninfo.com.cn/{announcement['adjunctUrl']}"
                
                # 构造保存路径
                report_folder = self.output_dir / stock_code / str(year)
                report_folder.mkdir(parents=True, exist_ok=True)
                
                # 文件名使用标准格式
                file_name = f"{stock_code}_{year}_{report_type.replace('报告', '')}.pdf"
                pdf_path = report_folder / file_name
                
                # 下载PDF文件
                download_success, checksum = self.download_file(pdf_url, pdf_path)
                
                if not download_success:
                    return {
                        "crawler_metadata": {
                            "source": "巨潮资讯网",
                            "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "url": pdf_url,
                            "status": "failed"
                        },
                        "error_message": "文件下载失败"
                    }
                
                # 创建并保存元数据
                metadata = {
                    "crawler_metadata": {
                        "source": "巨潮资讯网",
                        "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "url": pdf_url,
                        "status": "success",
                        "checksum": checksum
                    },
                    "report_metadata": {
                        "company_name": company_name,
                        "stock_code": stock_code,
                        "report_type": report_type,
                        "report_period": f"{year}年{report_type}",
                        "publish_date": publish_date
                    },
                    "file_info": {
                        "file_name": file_name,
                        "file_size": pdf_path.stat().st_size,
                        "file_path": str(pdf_path),
                        "text_path": str(pdf_path).replace(".pdf", ".txt")
                    }
                }
                
                # 将元数据保存为JSON文件
                metadata_path = report_folder / f"{stock_code}_{year}_{report_type.replace('报告', '')}_metadata.json"
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                
                # 提取文本内容
                self.extract_text_from_pdf(pdf_path)
                
                logger.info(f"成功爬取并保存 {company_name} {year}年{report_type}")
                return metadata
            else:
                logger.warning(f"未找到 {stock_code} {year}年{report_type}")
                return {
                    "crawler_metadata": {
                        "source": "巨潮资讯网",
                        "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "url": "",
                        "status": "failed"
                    },
                    "error_message": f"未找到 {stock_code} {year}年{report_type}"
                }
        
        except Exception as e:
            logger.error(f"爬取过程中出错: {str(e)}")
            return {
                "crawler_metadata": {
                    "source": "巨潮资讯网",
                    "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "url": "",
                    "status": "failed"
                },
                "error_message": str(e)
            }
    
    def extract_text_from_pdf(self, pdf_path: Path, save_text: bool = True) -> Optional[str]:
        """从PDF提取文本内容"""
        try:
            import pdfplumber
            
            logger.info(f"开始从PDF提取文本: {pdf_path}")
            text_content = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text_content.append(page.extract_text() or "")
            
            full_text = "\n\n".join(text_content)
            
            if save_text:
                text_path = pdf_path.with_suffix('.txt')
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(full_text)
                logger.info(f"文本内容已保存至: {text_path}")
            
            return full_text
            
        except ImportError:
            logger.warning("未安装pdfplumber库，无法提取PDF文本。请运行: pip install pdfplumber")
            return None
        except Exception as e:
            logger.error(f"提取PDF文本时出错: {str(e)}")
            return None