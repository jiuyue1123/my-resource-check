import os
import re
import logging
import concurrent.futures
import argparse
from datetime import datetime
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import markdown
from tqdm import tqdm
import random

class LinkChecker:
    def __init__(self, max_workers=16, timeout=20, enable_logging=True):
        self.max_workers = max_workers
        self.timeout = timeout
        self.enable_logging = enable_logging
        self.results = {
            'success': [],
            'failed': [],
            'skipped': []
        }
        # 添加常见的浏览器 User-Agent
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
        ]
        
        # 配置日志
        if self.enable_logging:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(f'link_check_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                    logging.StreamHandler()
                ]
            )
        else:
            # 如果禁用日志，设置一个空的处理器
            logging.basicConfig(
                level=logging.CRITICAL,  # 只显示严重错误
                handlers=[logging.NullHandler()]
            )
        
    def get_headers(self):
        """生成请求头"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
    def extract_links_from_md(self, file_path):
        """从markdown文件中提取链接"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 将markdown转换为HTML
            html = markdown.markdown(content)
            soup = BeautifulSoup(html, 'html.parser')
            
            # 提取链接
            links = []
            for a in soup.find_all('a'):
                href = a.get('href')
                if href and href.startswith(('http://', 'https://')):
                    links.append(href)
            
            return links
        except Exception as e:
            if self.enable_logging:
                logging.error(f"处理文件 {file_path} 时出错: {str(e)}")
            return []

    def check_link(self, url):
        """检查链接是否可访问"""
        try:
            # 使用GET请求替代HEAD请求，并添加请求头
            response = requests.get(
                url, 
                timeout=self.timeout, 
                allow_redirects=True,
                headers=self.get_headers(),
                verify=False  # 忽略SSL证书验证
            )
            
            # 放宽成功条件：只要不是明显的错误状态码就认为是成功的
            if response.status_code < 500:  # 修改为500，因为有些网站会返回403但实际可访问
                return True, url, response.status_code
            return False, url, response.status_code
        except requests.exceptions.RequestException as e:
            # 对于连接错误，尝试使用不同的User-Agent重试一次
            try:
                response = requests.get(
                    url, 
                    timeout=self.timeout, 
                    allow_redirects=True,
                    headers=self.get_headers(),  # 使用新的随机User-Agent
                    verify=False
                )
                if response.status_code < 500:
                    return True, url, response.status_code
            except:
                pass
            return False, url, str(e)

    def process_file(self, file_path):
        """处理单个markdown文件"""
        if self.enable_logging:
            logging.info(f"正在处理文件: {file_path}")
        links = self.extract_links_from_md(file_path)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.check_link, url): url for url in links}
            
            for future in tqdm(concurrent.futures.as_completed(future_to_url), 
                             total=len(links), 
                             desc=f"正在检查 {os.path.basename(file_path)} 中的链接"):
                url = future_to_url[future]
                try:
                    success, url, status = future.result()
                    if success:
                        self.results['success'].append((url, status))
                        if self.enable_logging:
                            logging.info(f"成功: {url} (状态码: {status})")
                    else:
                        self.results['failed'].append((url, status))
                        if self.enable_logging:
                            logging.error(f"失败: {url} (状态码: {status})")
                except Exception as e:
                    self.results['skipped'].append((url, str(e)))
                    if self.enable_logging:
                        logging.error(f"检查 {url} 时出错: {str(e)}")

    def save_results(self):
        """保存结果到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f'link_check_results_{timestamp}.txt', 'w', encoding='utf-8') as f:
            f.write("=== 成功的链接 ===\n")
            for url, status in self.results['success']:
                f.write(f"{url} (状态码: {status})\n")
            
            f.write("\n=== 失败的链接 ===\n")
            for url, status in self.results['failed']:
                f.write(f"{url} (状态码: {status})\n")
            
            f.write("\n=== 跳过的链接 ===\n")
            for url, error in self.results['skipped']:
                f.write(f"{url} (错误: {error})\n")

def main():
    # 禁用SSL警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    parser = argparse.ArgumentParser(description='检查markdown文件中的链接')
    parser.add_argument('path', help='markdown文件或目录的路径')
    parser.add_argument('--threads', type=int, default=16, help='使用的线程数（默认：16）')
    parser.add_argument('--timeout', type=int, default=20, help='请求超时时间（秒）（默认：20）')
    parser.add_argument('--no-log', action='store_true', help='禁用日志记录')
    
    args = parser.parse_args()
    
    checker = LinkChecker(
        max_workers=args.threads, 
        timeout=args.timeout,
        enable_logging=not args.no_log
    )
    
    if os.path.isfile(args.path):
        if args.path.endswith('.md'):
            checker.process_file(args.path)
        else:
            if not args.no_log:
                logging.error("输入文件必须是markdown文件（.md）")
    elif os.path.isdir(args.path):
        for root, _, files in os.walk(args.path):
            for file in files:
                if file.endswith('.md'):
                    checker.process_file(os.path.join(root, file))
    else:
        if not args.no_log:
            logging.error("提供的路径无效")
    
    checker.save_results()
    if not args.no_log:
        logging.info("链接检查完成。结果已保存。")

if __name__ == "__main__":
    main()
