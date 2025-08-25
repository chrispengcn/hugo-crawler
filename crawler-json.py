import os
import re
import json
import sys
import logging
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from datetime import datetime
from urllib.parse import urljoin
from lxml import etree  # 用于XPath解析

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(config_path):
    """加载指定路径的JSON配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查必要的配置项
        if 'project_root' not in config:
            logger.error("配置文件中缺少 project_root")
            raise ValueError("Missing required configuration: project_root")
            
        if 'fields' not in config or not isinstance(config['fields'], dict):
            logger.error("配置文件中缺少有效的 fields 配置")
            raise ValueError("Missing or invalid fields configuration")
            
        # 检查是否包含必要字段
        required_fields = ['title', 'content']
        for field in required_fields:
            if field not in config['fields']:
                logger.error(f"配置文件中缺少必要字段: {field}")
                raise ValueError(f"Missing required field configuration: {field}")
        
        return config
    except FileNotFoundError:
        logger.error(f"配置文件 {config_path} 不存在")
        raise
    except json.JSONDecodeError:
        logger.error(f"配置文件 {config_path} 格式错误")
        raise
    except Exception as e:
        logger.error(f"加载配置文件时出错: {str(e)}")
        raise

def read_url_list(project_root, file_name='urllist.txt'):
    """从项目根目录读取URL列表文件"""
    file_path = os.path.join(project_root, file_name)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        logger.info(f"从项目目录成功读取 {len(urls)} 个URL: {file_path}")
        return urls
    except FileNotFoundError:
        logger.error(f"项目目录下未找到URL列表文件: {file_path}")
        raise
    except Exception as e:
        logger.error(f"读取URL列表时出错: {str(e)}")
        raise

def get_downloaded_urls(project_root):
    """获取已下载的URL列表"""
    downloaded_log_path = os.path.join(project_root, 'downloaded.log')
    if not os.path.exists(downloaded_log_path):
        return set()
    
    try:
        with open(downloaded_log_path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    except Exception as e:
        logger.error(f"读取已下载URL记录时出错: {str(e)}")
        return set()

def mark_as_downloaded(project_root, url):
    """将URL标记为已下载"""
    downloaded_log_path = os.path.join(project_root, 'downloaded.log')
    try:
        with open(downloaded_log_path, 'a', encoding='utf-8') as f:
            f.write(f"{url}\n")
        logger.info(f"已标记URL为已下载: {url}")
    except Exception as e:
        logger.error(f"标记URL为已下载时出错: {str(e)}")

def fetch_page_content(url):
    """获取网页内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 抛出HTTP错误
        return response.text, url
    except requests.exceptions.RequestException as e:
        logger.error(f"获取网页内容失败 {url}: {str(e)}")
        return None, url

def extract_field(html_content, xpath, attribute, base_url):
    """使用XPath提取字段内容"""
    try:
        # 使用XPath解析
        tree = etree.HTML(html_content)
        elements = tree.xpath(xpath)
        if not elements:
            logger.warning(f"XPath未找到匹配的元素: {xpath}")
            return None
        
        # 处理XPath结果
        element = elements[0]
        if isinstance(element, etree._Element):
            element_html = etree.tostring(element, encoding='unicode')
            element_soup = BeautifulSoup(element_html, 'html.parser')
        else:
            # 如果是文本节点
            return str(element).strip()
        
        # 提取属性
        if attribute == 'text':
            return element_soup.get_text(strip=True)
        elif attribute == 'html':
            return str(element_soup)
        else:
            value = element_soup.get(attribute, None)
            # 如果是URL且是相对路径，转换为绝对路径
            if value and attribute in ['src', 'href'] and (value.startswith('/') or not value.startswith('http')):
                return urljoin(base_url, value)
            return value
            
    except Exception as e:
        logger.error(f"XPath提取字段出错 {xpath}: {str(e)}")
        return None

def sanitize_filename(name):
    """清理文件名，生成SEO友好的名称"""
    # 首先将空格转换为横线
    sanitized = name.replace(' ', '-')
    
    # 移除所有标点符号和特殊字符（保留字母、数字和横线）
    sanitized = re.sub(r'[^\w\-]', '', sanitized)
    
    # 合并多个连续横线为一个
    sanitized = re.sub(r'-+', '-', sanitized)
    
    # 转换为小写并截断过长的文件名（最多100个字符）
    # 同时移除可能的开头和结尾横线
    return sanitized.lower().strip('-')[:100]

def download_image(image_url, save_dir, base_url):
    """下载图片并保存到指定目录"""
    if not image_url:
        return None
    
    try:
        # 确保保存目录存在
        os.makedirs(save_dir, exist_ok=True)
        
        # 处理相对URL
        if not image_url.startswith('http'):
            image_url = urljoin(base_url, image_url)
        
        # 获取图片文件名
        image_name = os.path.basename(image_url.split('?')[0])  # 移除URL参数
        if not image_name or '.' not in image_name:
            image_name = f"image_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        
        save_path = os.path.join(save_dir, image_name)
        
        # 检查图片是否已存在
        if os.path.exists(save_path):
            logger.info(f"图片已存在，跳过下载: {image_name}")
            return image_name
        
        # 下载图片
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(image_url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"图片下载成功: {image_name}")
        return image_name
    except Exception as e:
        logger.error(f"图片下载失败 {image_url}: {str(e)}")
        return None

def download_content_images(content_html, save_dir, base_url):
    """下载内容中的所有图片并替换为本地路径"""
    if not content_html:
        return content_html
    
    soup = BeautifulSoup(content_html, 'html.parser')
    images = soup.find_all('img')
    
    for img in images:
        img_url = img.get('src')
        if img_url:
            img_name = download_image(img_url, save_dir, base_url)
            if img_name:
                # 修改图片路径，使其指向/static/images/目录
                img['src'] = f"/static/images/{img_name}"
    
    return str(soup)

def create_markdown_file(save_path, front_matter, content):
    """创建Markdown文件"""
    # 确保保存目录存在
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # 构建Markdown内容
    md_content = "---\n"
    # 添加front-matter字段
    for key, value in front_matter.items():
        if value is not None:
            # 处理包含双引号的值
            escaped_value = str(value).replace('"', '\\"')
            md_content += f"{key}: \"{escaped_value}\"\n"
    md_content += "---\n\n"
    md_content += content
    
    try:
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        logger.info(f"Markdown文件创建成功: {save_path}")
        return True
    except Exception as e:
        logger.error(f"创建Markdown文件失败: {str(e)}")
        return False

def process_url(url, config):
    """处理单个URL的采集流程"""
    logger.info(f"开始处理URL: {url}")
    
    # 获取网页内容
    html_content, base_url = fetch_page_content(url)
    if not html_content:
        return False
    
    # 提取所有配置的字段
    extracted_fields = {}
    for field_name, field_config in config['fields'].items():
        # 检查字段配置是否完整
        if 'xpath' not in field_config or 'attribute' not in field_config:
            logger.warning(f"字段 {field_name} 配置不完整，跳过提取")
            continue
            
        # 提取字段值
        extracted_value = extract_field(
            html_content, 
            field_config['xpath'], 
            field_config['attribute'], 
            base_url
        )
        extracted_fields[field_name] = extracted_value
    
    # 检查必要字段
    if not extracted_fields.get('title') or not extracted_fields.get('content'):
        logger.error(f"缺少必要字段(title或content)，跳过URL: {url}")
        return False
    
    # 处理日期字段，如果未提取到则使用当前日期
    if 'date' not in extracted_fields or not extracted_fields['date']:
        extracted_fields['date'] = datetime.now().strftime('%Y-%m-%d')
    
    # 生成slug（SEO友好名称，基于标题）
    title = extracted_fields['title']
    slug = sanitize_filename(title)
    extracted_fields['slug'] = slug
    
    # 创建Markdown文件保存路径：/$projectroot/content/blog/YYYY-MM-DD-$seotitle.md
    date_prefix = extracted_fields['date']  # 格式为YYYY-MM-DD
    md_filename = f"{date_prefix}-{slug}.md"
    md_save_path = os.path.join(config['project_root'], 'content', 'blog', md_filename)
    
    # 图片保存路径：/$projectroot/static/images/*.*
    image_save_dir = os.path.join(config['project_root'], 'static', 'images')
    
    # 处理内容中的图片
    content_html = extracted_fields['content']
    content_with_local_images = download_content_images(content_html, image_save_dir, base_url)
    
    # 转换为Markdown
    content_md = md(content_with_local_images)
    
    # 准备front-matter（不包含url字段，包含slug字段）
    front_matter = {k: v for k, v in extracted_fields.items() if k != 'content' and k != 'url'}
    
    # 创建Markdown文件
    success = create_markdown_file(md_save_path, front_matter, content_md)
    
    if success:
        mark_as_downloaded(config['project_root'], url)
        logger.info(f"URL处理成功: {url}，保存路径: {md_save_path}")
        return True
    else:
        logger.error(f"URL处理失败: {url}")
        return False

def main(config_path):
    """主函数"""
    try:
        # 加载配置
        config = load_config(config_path)
        
        # 确保项目所需目录存在
        os.makedirs(config['project_root'], exist_ok=True)
        os.makedirs(os.path.join(config['project_root'], 'content', 'blog'), exist_ok=True)
        os.makedirs(os.path.join(config['project_root'], 'static', 'images'), exist_ok=True)
        
        # 从项目根目录读取URL列表
        urls = read_url_list(config['project_root'])
        if not urls:
            logger.warning("没有要处理的URL")
            return
        
        # 获取已下载的URL
        downloaded_urls = get_downloaded_urls(config['project_root'])
        
        # 处理未下载的URL
        for url in urls:
            if url in downloaded_urls:
                logger.info(f"URL已下载，跳过: {url}")
                continue
            
            # 处理URL
            process_url(url, config)
            
            # 可以添加延迟，避免请求过于频繁
            # time.sleep(1)
            
        logger.info("所有URL处理完毕")
        
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python crawler-json.py <配置文件路径>")
        sys.exit(1)
    
    main(sys.argv[1])
    