#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cào dữ liệu từ website Fotek.com.tw
Phát triển bởi: Assistant AI
Chức năng: Cào dữ liệu sản phẩm từ Fotek.com.tw với đa luồng và AI Gemini
"""

import requests
import json
import os
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
from pathlib import Path
import pandas as pd
from PIL import Image, ImageDraw
import io
import base64
import re
from typing import List, Dict, Optional, Tuple
import logging

# Thư viện cho web scraping
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Thư viện cho AI Gemini
import google.generativeai as genai

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FotekScraper:
    """Class chính cho việc cào dữ liệu từ Fotek.com.tw"""
    
    def __init__(self, max_workers: int = 5):
        """
        Khởi tạo FotekScraper
        
        Args:
            max_workers: Số lượng luồng tối đa để xử lý song song
        """
        self.base_url = "https://www.fotek.com.tw"
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Cấu hình Selenium WebDriver
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Cấu hình Gemini AI với API key được embed
        gemini_api_key = "AIzaSyBEUiHyq0bBFW_6TRF9g-pmjG3_jQfPpBY"
        try:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("✅ Gemini AI đã được khởi tạo thành công")
        except Exception as e:
            self.gemini_model = None
            logger.warning(f"⚠️ Không thể khởi tạo Gemini AI: {e}")
        
        # Tạo thư mục lưu trữ
        self.output_dir = Path("fotek_data")
        self.images_dir = self.output_dir / "images"
        self.specs_dir = self.output_dir / "specifications"
        self.excel_dir = self.output_dir / "excel"
        
        for dir_path in [self.output_dir, self.images_dir, self.specs_dir, self.excel_dir]:
            dir_path.mkdir(exist_ok=True, parents=True)
        
        logger.info("FotekScraper đã được khởi tạo thành công")
    
    def get_driver(self) -> webdriver.Chrome:
        """Tạo một WebDriver Chrome mới"""
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.implicitly_wait(10)
            return driver
        except Exception as e:
            logger.error(f"Không thể khởi tạo WebDriver: {e}")
            raise
    
    def close_driver(self, driver: webdriver.Chrome):
        """Đóng WebDriver"""
        try:
            driver.quit()
        except Exception as e:
            logger.warning(f"Lỗi khi đóng WebDriver: {e}")
    
    def safe_request(self, url: str, timeout: int = 30) -> Optional[requests.Response]:
        """Thực hiện request an toàn với retry"""
        for attempt in range(3):
            try:
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Lỗi request (lần {attempt + 1}): {e}")
                if attempt == 2:
                    return None
                time.sleep(2 ** attempt)
        return None
    
    def extract_series_links(self, category_url: str) -> List[Dict[str, str]]:
        """
        Trích xuất các link series sản phẩm từ trang danh mục
        
        Args:
            category_url: URL của trang danh mục
            
        Returns:
            List các dict chứa thông tin series (name, url, image)
        """
        logger.info(f"Bắt đầu trích xuất series từ: {category_url}")
        
        response = self.safe_request(category_url)
        if not response:
            logger.error(f"Không thể truy cập trang danh mục: {category_url}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        series_list = []
        
        # Tìm section chứa các series
        bg_light_section = soup.find('section', class_='bg-light')
        if not bg_light_section:
            logger.error("Không tìm thấy section bg-light")
            return []
        
        # Tìm tất cả các card series
        cards = bg_light_section.find_all('div', class_='card mb-4')
        logger.info(f"Tìm thấy {len(cards)} series cards")
        
        for card in cards:
            try:
                # Trích xuất tên series
                title_element = card.find('h4')
                series_name = title_element.text.strip() if title_element else "Unknown Series"
                
                # Trích xuất link
                link_element = card.find('a', class_='stretched-link')
                if not link_element or not link_element.get('href'):
                    continue
                
                series_url = urljoin(self.base_url, link_element['href'])
                
                # Trích xuất ảnh series
                img_div = card.find('div', class_='box-img')
                series_image = ""
                if img_div and img_div.get('style'):
                    style = img_div['style']
                    match = re.search(r"background-image:url\('([^']+)'\)", style)
                    if match:
                        series_image = urljoin(self.base_url, match.group(1))
                
                # Trích xuất mô tả
                description_element = card.find('p', class_='txt-l3')
                description = description_element.text.strip() if description_element else ""
                
                series_info = {
                    'name': series_name,
                    'url': series_url,
                    'image': series_image,
                    'description': description
                }
                
                series_list.append(series_info)
                logger.info(f"Đã trích xuất series: {series_name}")
                
            except Exception as e:
                logger.error(f"Lỗi khi trích xuất thông tin series: {e}")
                continue
        
        logger.info(f"Hoàn thành trích xuất {len(series_list)} series")
        return series_list
    
    def extract_products_from_series(self, series_url: str) -> List[Dict[str, str]]:
        """
        Trích xuất danh sách sản phẩm từ trang series
        
        Args:
            series_url: URL của trang series
            
        Returns:
            List các dict chứa thông tin sản phẩm cơ bản
        """
        logger.info(f"Bắt đầu trích xuất sản phẩm từ series: {series_url}")
        
        # Sử dụng Selenium thay vì requests để xử lý JavaScript
        driver = self.get_driver()
        try:
            driver.get(series_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Lấy HTML sau khi JavaScript đã load
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            products_list = []
            
            # Tìm container chứa các sản phẩm với selector linh hoạt hơn
            container = soup.find('div', class_='container') or soup.find('div', {'class': re.compile(r'.*container.*')})
            if not container:
                logger.error("Không tìm thấy container sản phẩm")
                return []
            
            # Tìm tất cả các item-type (nhóm sản phẩm) với selector linh hoạt
            item_types = (container.find_all('div', class_='item-type') or 
                         container.find_all('div', {'class': re.compile(r'.*item.*type.*')}) or
                         container.find_all('div', {'class': re.compile(r'.*product.*group.*')}))
            
            logger.info(f"Tìm thấy {len(item_types)} nhóm sản phẩm")
            
            # Nếu không tìm thấy item-type, thử tìm trực tiếp danh sách sản phẩm
            if not item_types:
                logger.warning("Không tìm thấy item-type, thử tìm trực tiếp sản phẩm...")
                # Tìm tất cả các link có chứa "product" hoặc "View specs"
                product_links = soup.find_all('a', href=re.compile(r'/product/\d+'))
                
                for link in product_links:
                    try:
                        product_url = urljoin(self.base_url, link['href'])
                        
                        # Tìm thông tin sản phẩm từ context
                        parent = link.find_parent('li') or link.find_parent('div')
                        if parent:
                            spans = parent.find_all('span')
                            if len(spans) >= 2:
                                product_code = spans[0].text.strip()
                                features = spans[1].text.strip() if len(spans) > 1 else ""
                                
                                product_info = {
                                    'code': product_code,
                                    'features': features,
                                    'url': product_url,
                                    'group_name': "Unknown Group",
                                    'group_image': "",
                                    'series_url': series_url
                                }
                                
                                products_list.append(product_info)
                                logger.debug(f"Đã trích xuất sản phẩm: {product_code}")
                    except Exception as e:
                        logger.warning(f"Lỗi khi trích xuất sản phẩm từ link: {e}")
                        continue
            else:
                # Xử lý theo cách cũ nếu tìm thấy item-type
                for item_type in item_types:
                    try:
                        # Lấy tên nhóm sản phẩm
                        group_name_element = item_type.find('h5') or item_type.find('h4') or item_type.find('h3')
                        group_name = group_name_element.text.strip() if group_name_element else "Unknown Group"
                        
                        # Lấy ảnh nhóm
                        img_div = item_type.find('div', class_='box-img') or item_type.find('div', {'class': re.compile(r'.*img.*')})
                        group_image = ""
                        if img_div and img_div.get('style'):
                            style = img_div['style']
                            match = re.search(r"background-image:url\('([^']+)'\)", style)
                            if match:
                                group_image = urljoin(self.base_url, match.group(1))
                        
                        # Tìm tất cả sản phẩm trong nhóm
                        product_items = item_type.find_all('li')
                        
                        for li in product_items:
                            spans = li.find_all('span')
                            if len(spans) >= 3:
                                product_code = spans[0].text.strip()
                                features = spans[1].text.strip()
                                
                                # Tìm link "View specs"
                                specs_link_element = spans[2].find('a')
                                if specs_link_element and specs_link_element.get('href'):
                                    product_url = urljoin(self.base_url, specs_link_element['href'])
                                    
                                    product_info = {
                                        'code': product_code,
                                        'features': features,
                                        'url': product_url,
                                        'group_name': group_name,
                                        'group_image': group_image,
                                        'series_url': series_url
                                    }
                                    
                                    products_list.append(product_info)
                                    logger.debug(f"Đã trích xuất sản phẩm: {product_code}")
                        
                    except Exception as e:
                        logger.error(f"Lỗi khi trích xuất nhóm sản phẩm: {e}")
                        continue
            
            logger.info(f"Hoàn thành trích xuất {len(products_list)} sản phẩm từ series")
            return products_list
            
        except Exception as e:
            logger.error(f"Lỗi khi trích xuất sản phẩm từ series {series_url}: {e}")
            return []
        finally:
            self.close_driver(driver)
    
    def extract_product_details(self, product_url: str, product_code: str) -> Dict:
        """
        Trích xuất chi tiết sản phẩm từ trang sản phẩm
        
        Args:
            product_url: URL của trang sản phẩm
            product_code: Mã sản phẩm
            
        Returns:
            Dict chứa thông tin chi tiết sản phẩm
        """
        logger.info(f"Bắt đầu trích xuất chi tiết sản phẩm: {product_code}")
        
        driver = self.get_driver()
        try:
            driver.get(product_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Lấy HTML sau khi JavaScript đã load
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            product_details = {
                'code': product_code,
                'url': product_url,
                'name': '',
                'name_vietnamese': '',
                'images': {
                    'product': [],
                    'specifications': '',
                    'wiring_diagram': '',
                    'dimensions': ''
                },
                'specifications_table': '',
                'specifications_raw': ''
            }
            
            # Trích xuất tên sản phẩm
            title_element = (soup.find('p', class_='title-card') or 
                            soup.find('h1') or 
                            soup.find('h2') or
                            soup.find('div', {'class': re.compile(r'.*title.*')}))
            if title_element:
                product_details['name'] = title_element.text.strip()
            
            # Trích xuất ảnh sản phẩm chính
            gallery = soup.find('div', class_='gallery') or soup.find('div', {'class': re.compile(r'.*gallery.*')})
            if gallery:
                product_images = []
                for item in gallery.find_all('div', class_='item'):
                    link = item.find('a')
                    if link and link.get('href'):
                        img_url = urljoin(self.base_url, link['href'])
                        product_images.append(img_url)
                product_details['images']['product'] = product_images
            
            # Trích xuất thông tin từ các tab
            tab_content = soup.find('div', class_='tab-content') or soup.find('div', {'id': 'myTabContent'})
            if tab_content:
                # Tab specifications (tab1)
                tab1 = tab_content.find('div', id='tab1')
                if tab1:
                    img_element = tab1.find('img')
                    if img_element and img_element.get('src'):
                        product_details['images']['specifications'] = urljoin(self.base_url, img_element['src'])
                
                # Tab wiring diagram (tab2)
                tab2 = tab_content.find('div', id='tab2')
                if tab2:
                    img_element = tab2.find('img')
                    if img_element and img_element.get('src'):
                        product_details['images']['wiring_diagram'] = urljoin(self.base_url, img_element['src'])
                
                # Tab dimensions (tab3)
                tab3 = tab_content.find('div', id='tab3')
                if tab3:
                    img_element = tab3.find('img')
                    if img_element and img_element.get('src'):
                        product_details['images']['dimensions'] = urljoin(self.base_url, img_element['src'])
            
            logger.info(f"Hoàn thành trích xuất chi tiết sản phẩm: {product_code}")
            return product_details
            
        except Exception as e:
            logger.error(f"Lỗi khi trích xuất chi tiết sản phẩm {product_code}: {e}")
            return {}
        finally:
            self.close_driver(driver)
    
    def translate_with_gemini(self, text: str, target_language: str = "Vietnamese") -> str:
        """
        Dịch văn bản bằng Gemini AI
        
        Args:
            text: Văn bản cần dịch
            target_language: Ngôn ngữ đích
            
        Returns:
            Văn bản đã dịch
        """
        if not self.gemini_model:
            logger.warning("Gemini AI không khả dụng")
            return text
        
        try:
            prompt = f"Translate the following text to {target_language}: {text}"
            response = self.gemini_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Lỗi khi dịch văn bản: {e}")
            return text
    
    def extract_specs_from_image_with_gemini(self, image_path: str, product_code: str) -> str:
        """
        Trích xuất thông số kỹ thuật từ ảnh local bằng Gemini AI và tạo bảng HTML
        
        Args:
            image_path: Đường dẫn local của ảnh thông số kỹ thuật
            product_code: Mã sản phẩm
            
        Returns:
            HTML table chứa thông số kỹ thuật
        """
        if not self.gemini_model:
            logger.warning("Gemini AI không khả dụng")
            return ""
        
        try:
            # Kiểm tra file tồn tại
            image_file = Path(image_path)
            if not image_file.exists():
                logger.warning(f"File ảnh không tồn tại: {image_path}")
                return ""
            
            # Đọc file ảnh local
            with open(image_file, 'rb') as f:
                image_content = f.read()
            
            # Chuyển ảnh thành base64
            image_data = base64.b64encode(image_content).decode()
            
            # Xác định MIME type dựa trên extension
            mime_type = "image/jpeg"
            if image_file.suffix.lower() in ['.png', '.webp']:
                mime_type = f"image/{image_file.suffix.lower()[1:]}"
            
            prompt = f"""
            Phân tích ảnh thông số kỹ thuật này và trích xuất tất cả thông tin kỹ thuật.
            Dịch sang tiếng Việt và tạo bảng HTML theo định dạng sau:
            
            <table id="specifications" border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; font-family: Arial; width: 100%;">
            <thead>
            <tr style="background-color: #f2f2f2;">
            <th>Thông số</th>
            <th>Giá trị</th>
            </tr>
            </thead>
            <tbody>
            <tr><td style="font-weight: bold;">Mã sản phẩm</td><td>{product_code}</td></tr>
            [Thêm các thông số kỹ thuật khác ở đây]
            <tr><td style="font-weight: bold;">Copyright</td><td>Haiphongtech.vn</td></tr>
            </tbody>
            </table>
            
            Lưu ý: 
            - Hàng Copyright là bắt buộc phải có cuối bảng.
            - CHỈ TRẢ VỀ HTML TABLE THUẦN TÚY, KHÔNG CÓ ```html, ```, hoặc bất kỳ markdown formatting nào
            - Không thêm text giải thích hoặc mô tả trước/sau table
            """
            
            # Gửi request tới Gemini với ảnh
            response = self.gemini_model.generate_content([
                prompt,
                {"mime_type": mime_type, "data": image_data}
            ])
            
            if response and response.text:
                # Loại bỏ markdown formatting nếu có
                html_content = response.text.strip()
                
                # Loại bỏ ```html và ``` nếu có
                if '```html' in html_content:
                    html_content = html_content.split('```html')[1].split('```')[0].strip()
                elif '```' in html_content:
                    html_content = html_content.replace('```', '').strip()
                
                # Loại bỏ các text mô tả thường gặp
                unwanted_texts = [
                    "Here's the HTML table representing the technical specifications from the image:",
                    "This HTML code creates a nicely formatted table with the technical specifications translated into Vietnamese.",
                    "Remember to replace",
                    "The table includes all the specifications from the image and the required copyright information.",
                    "Dưới đây là bảng HTML chứa thông số kỹ thuật được trích xuất từ hình ảnh, được dịch sang tiếng Việt:",
                    "with the actual product code if it's different"
                ]
                
                for unwanted in unwanted_texts:
                    if unwanted in html_content:
                        html_content = html_content.replace(unwanted, "").strip()
                
                logger.info(f"Đã trích xuất thông số kỹ thuật cho sản phẩm {product_code}")
                return html_content
            else:
                logger.warning(f"Gemini không trả về kết quả cho {product_code}")
                return ""
            
        except Exception as e:
            logger.error(f"Lỗi khi trích xuất thông số từ ảnh {image_path}: {e}")
            return ""
    
    def fix_vietnamese_name_with_gemini(self, english_name: str) -> str:
        """
        Sử dụng Gemini AI để sửa và chuẩn hóa tên sản phẩm tiếng Việt + thêm hậu tố FOTEK
        
        Args:
            english_name: Tên sản phẩm tiếng Anh
            
        Returns:
            Tên sản phẩm tiếng Việt đã được chuẩn hóa + hậu tố FOTEK
        """
        if not self.gemini_model:
            logger.warning("Gemini AI không khả dụng")
            return f"{english_name} FOTEK"
        
        try:
            prompt = f"""
            Dịch tên sản phẩm sau sang tiếng Việt một cách chính xác và ngắn gọn nhất:
            "{english_name}"
            
            Yêu cầu:
            - Chỉ trả về 1 tên duy nhất, không có các lựa chọn Option 1, 2, 3...
            - Tên phải ngắn gọn, chính xác và dễ hiểu
            - Không thêm text giải thích hoặc mô tả
            - Không bao gồm hậu tố FOTEK (sẽ được thêm sau)
            - Ví dụ: "PS Series Inductive Proximity Sensor" → "Cảm biến tiệm cận cảm ứng dòng PS"
            
            CHỈ TRẢ VỀ TÊN TIẾNG VIỆT DUY NHẤT:
            """
            
            response = self.gemini_model.generate_content(prompt)
            
            if response and response.text:
                vietnamese_name = response.text.strip()
                
                # Loại bỏ các text không mong muốn
                unwanted_patterns = [
                    "Option 1", "Option 2", "Option 3",
                    "**", "*", 
                    "There are several ways to translate",
                    "depending on the desired level",
                    "Formal", "less formal", "descriptive",
                    "suitable for technical documentation",
                    ">"
                ]
                
                for pattern in unwanted_patterns:
                    if pattern in vietnamese_name:
                        # Lấy phần đầu tiên trước khi gặp pattern
                        vietnamese_name = vietnamese_name.split(pattern)[0].strip()
                        break
                
                # Loại bỏ ký tự đặc biệt
                vietnamese_name = vietnamese_name.replace("*", "").replace(">", "").strip()
                
                # Nếu có nhiều dòng, chỉ lấy dòng đầu tiên
                if '\n' in vietnamese_name:
                    vietnamese_name = vietnamese_name.split('\n')[0].strip()
                
                # Thêm hậu tố FOTEK
                final_name = f"{vietnamese_name} FOTEK"
                
                logger.info(f"Đã sửa tên tiếng Việt: {english_name} → {final_name}")
                return final_name
            else:
                logger.warning(f"Gemini không trả về kết quả cho tên: {english_name}")
                return f"{english_name} FOTEK"
                
        except Exception as e:
            logger.error(f"Lỗi khi sửa tên tiếng Việt: {e}")
            return f"{english_name} FOTEK"
    
    def download_and_process_image(self, image_url: str, save_path: str, add_white_background: bool = False) -> bool:
        """
        Tải xuống và xử lý ảnh (chuyển sang WebP, thêm nền trắng nếu cần)
        
        Args:
            image_url: URL của ảnh
            save_path: Đường dẫn lưu ảnh
            add_white_background: Có thêm nền trắng không
            
        Returns:
            True nếu thành công
        """
        try:
            response = self.safe_request(image_url)
            if not response:
                return False
            
            # Mở ảnh
            original_image = Image.open(io.BytesIO(response.content))
            
            # Chuyển sang RGBA nếu cần
            if original_image.mode != 'RGBA':
                original_image = original_image.convert('RGBA')
            
            processed_image = original_image
            
            # Thêm nền trắng nếu yêu cầu
            if add_white_background:
                # Tạo ảnh nền trắng cùng kích thước
                white_background = Image.new('RGBA', original_image.size, (255, 255, 255, 255))
                # Ghép ảnh gốc lên nền trắng
                processed_image = Image.alpha_composite(white_background, original_image)
            
            # Chuyển sang RGB để lưu WebP
            if processed_image.mode == 'RGBA':
                processed_image = processed_image.convert('RGB')
            
            # Đảm bảo thư mục tồn tại
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Lưu dưới định dạng WebP
            processed_image.save(save_path, 'WEBP', quality=85, optimize=True)
            
            logger.debug(f"Đã lưu ảnh: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý ảnh {image_url}: {e}")
            return False
    
    def process_series_parallel(self, series_list: List[Dict]) -> List[Dict]:
        """
        Xử lý nhiều series song song bằng đa luồng
        
        Args:
            series_list: Danh sách series cần xử lý
            
        Returns:
            Danh sách tất cả sản phẩm từ các series
        """
        all_products = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit các task
            future_to_series = {
                executor.submit(self.extract_products_from_series, series['url']): series
                for series in series_list
            }
            
            # Xử lý kết quả
            for future in as_completed(future_to_series):
                series = future_to_series[future]
                try:
                    products = future.result()
                    for product in products:
                        product['series_name'] = series['name']
                        product['series_image'] = series['image']
                    all_products.extend(products)
                    logger.info(f"Hoàn thành series: {series['name']} - {len(products)} sản phẩm")
                except Exception as e:
                    logger.error(f"Lỗi khi xử lý series {series['name']}: {e}")
        
        return all_products
    
    def process_products_parallel(self, products_list: List[Dict]) -> List[Dict]:
        """
        Xử lý chi tiết nhiều sản phẩm song song bằng đa luồng
        
        Args:
            products_list: Danh sách sản phẩm cần xử lý chi tiết
            
        Returns:
            Danh sách sản phẩm đã xử lý chi tiết
        """
        detailed_products = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit các task
            future_to_product = {
                executor.submit(self.extract_product_details, product['url'], product['code']): product
                for product in products_list
            }
            
            # Xử lý kết quả
            for future in as_completed(future_to_product):
                base_product = future_to_product[future]
                try:
                    detailed_product = future.result()
                    if detailed_product:
                        # Merge thông tin cơ bản với chi tiết
                        detailed_product.update(base_product)
                        detailed_products.append(detailed_product)
                        logger.info(f"Hoàn thành chi tiết sản phẩm: {detailed_product['code']}")
                except Exception as e:
                    logger.error(f"Lỗi khi xử lý chi tiết sản phẩm {base_product['code']}: {e}")
        
        return detailed_products
    
    def process_images_parallel(self, products_list: List[Dict]) -> List[Dict]:
        """
        Xử lý tải xuống và chuyển đổi ảnh song song
        
        Args:
            products_list: Danh sách sản phẩm có chứa URLs ảnh
            
        Returns:
            Danh sách sản phẩm đã cập nhật đường dẫn ảnh local
        """
        def download_product_images(product):
            """Download và xử lý tất cả ảnh của một sản phẩm với cấu trúc file đơn giản"""
            product_code = product['code']
            
            # Đảm bảo thư mục images tồn tại
            self.images_dir.mkdir(parents=True, exist_ok=True)
            
            updated_product = product.copy()
            
            # Xử lý ảnh sản phẩm (thêm nền trắng)
            if product['images']['product']:
                product_images_local = []
                for i, img_url in enumerate(product['images']['product']):
                    # Chỉ lấy ảnh đầu tiên và đặt tên theo mã sản phẩm
                    if i == 0:  # Chỉ lấy ảnh đầu tiên
                        filename = f"{product_code}.webp"
                        save_path = self.images_dir / filename
                        if self.download_and_process_image(img_url, str(save_path), add_white_background=True):
                            product_images_local.append(str(save_path))
                updated_product['images']['product'] = product_images_local
            
            # Xử lý ảnh thông số kỹ thuật
            if product['images']['specifications']:
                filename = f"{product_code}-SPEC.webp"
                save_path = self.images_dir / filename
                if self.download_and_process_image(product['images']['specifications'], str(save_path)):
                    updated_product['images']['specifications'] = str(save_path)
            
            # Xử lý ảnh wiring diagram
            if product['images']['wiring_diagram']:
                filename = f"{product_code}-WD.webp"
                save_path = self.images_dir / filename
                if self.download_and_process_image(product['images']['wiring_diagram'], str(save_path)):
                    updated_product['images']['wiring_diagram'] = str(save_path)
            
            # Xử lý ảnh dimensions
            if product['images']['dimensions']:
                filename = f"{product_code}-DMS.webp"
                save_path = self.images_dir / filename
                if self.download_and_process_image(product['images']['dimensions'], str(save_path)):
                    updated_product['images']['dimensions'] = str(save_path)
            
            return updated_product
        
        processed_products = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit các task download ảnh
            future_to_product = {
                executor.submit(download_product_images, product): product
                for product in products_list
            }
            
            # Xử lý kết quả
            for future in as_completed(future_to_product):
                original_product = future_to_product[future]
                try:
                    processed_product = future.result()
                    processed_products.append(processed_product)
                    logger.info(f"Hoàn thành xử lý ảnh: {processed_product['code']}")
                except Exception as e:
                    logger.error(f"Lỗi khi xử lý ảnh sản phẩm {original_product['code']}: {e}")
        
        return processed_products
    
    def process_ai_tasks_parallel(self, products_list: List[Dict]) -> List[Dict]:
        """
        Xử lý các tác vụ AI (dịch, trích xuất thông số) song song
        
        Args:
            products_list: Danh sách sản phẩm cần xử lý AI
            
        Returns:
            Danh sách sản phẩm đã xử lý AI
        """
        def process_ai_for_product(product):
            """Xử lý AI cho một sản phẩm"""
            updated_product = product.copy()
            
            # Dịch tên sản phẩm sang tiếng Việt
            if product['name']:
                vietnamese_name = self.translate_with_gemini(product['name'])
                updated_product['name_vietnamese'] = vietnamese_name
            
            # Trích xuất thông số kỹ thuật từ ảnh
            if product['images']['specifications']:
                specs_table = self.extract_specs_from_image_with_gemini(
                    product['images']['specifications'], 
                    product['code']
                )
                updated_product['specifications_table'] = specs_table
            
            return updated_product
        
        if not self.gemini_model:
            logger.warning("Gemini AI không khả dụng - bỏ qua xử lý AI")
            return products_list
        
        processed_products = []
        
        with ThreadPoolExecutor(max_workers=min(self.max_workers, 3)) as executor:  # Giới hạn cho AI
            # Submit các task AI
            future_to_product = {
                executor.submit(process_ai_for_product, product): product
                for product in products_list
            }
            
            # Xử lý kết quả
            for future in as_completed(future_to_product):
                original_product = future_to_product[future]
                try:
                    processed_product = future.result()
                    processed_products.append(processed_product)
                    logger.info(f"Hoàn thành xử lý AI: {processed_product['code']}")
                except Exception as e:
                    logger.error(f"Lỗi khi xử lý AI sản phẩm {original_product['code']}: {e}")
                    processed_products.append(original_product)  # Giữ bản gốc nếu lỗi
        
        return processed_products
    
    def save_to_excel(self, products_list: List[Dict], filename: str):
        """
        Lưu dữ liệu sản phẩm vào file Excel
        
        Args:
            products_list: Danh sách sản phẩm
            filename: Tên file Excel
        """
        try:
            # Chuẩn bị dữ liệu cho Excel
            excel_data = []
            
            for product in products_list:
                row = {
                    'Mã sản phẩm': product.get('code', ''),
                    'Tên sản phẩm (English)': product.get('name', ''),
                    'Tên sản phẩm (Tiếng Việt)': product.get('name_vietnamese', ''),
                    'Series': product.get('series_name', ''),
                    'Nhóm sản phẩm': product.get('group_name', ''),
                    'Mô tả tính năng': product.get('features', ''),
                    'URL sản phẩm': product.get('url', ''),
                    'Ảnh sản phẩm': ', '.join(product.get('images', {}).get('product', [])),
                    'Ảnh thông số kỹ thuật': product.get('images', {}).get('specifications', ''),
                    'Ảnh sơ đồ đấu nối': product.get('images', {}).get('wiring_diagram', ''),
                    'Ảnh kích thước': product.get('images', {}).get('dimensions', ''),
                    'Thông số kỹ thuật (HTML)': product.get('specifications_table', '')
                }
                excel_data.append(row)
            
            # Tạo DataFrame và lưu Excel
            df = pd.DataFrame(excel_data)
            excel_path = self.excel_dir / filename
            
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Sản phẩm', index=False)
                
                # Tự động điều chỉnh độ rộng cột
                worksheet = writer.sheets['Sản phẩm']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            logger.info(f"Đã lưu dữ liệu vào Excel: {excel_path}")
            
        except Exception as e:
            logger.error(f"Lỗi khi lưu Excel: {e}")
    
    def save_products_by_category(self, products_list: List[Dict]) -> None:
        """
        Lưu dữ liệu sản phẩm thành các file Excel riêng theo danh mục
        
        Args:
            products_list: Danh sách sản phẩm
        """
        try:
            # Tạo thư mục Excel categories
            excel_categories_dir = self.output_dir / "excel_categories"
            excel_categories_dir.mkdir(exist_ok=True, parents=True)
            
            # Nhóm sản phẩm theo category URL từ series_url
            category_groups = {}
            
            for product in products_list:
                series_url = product.get('series_url', '')
                
                # Trích xuất category ID từ series URL
                # Ví dụ: https://www.fotek.com.tw/en-gb/product-category/72/113 → category 72
                try:
                    if '/product-category/' in series_url:
                        category_part = series_url.split('/product-category/')[1]
                        category_id = category_part.split('/')[0]
                        
                        if category_id not in category_groups:
                            category_groups[category_id] = []
                        category_groups[category_id].append(product)
                except:
                    # Nếu không parse được, đặt vào nhóm "unknown"
                    if 'unknown' not in category_groups:
                        category_groups['unknown'] = []
                    category_groups['unknown'].append(product)
            
            # Lưu từng category thành file Excel riêng
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for category_id, category_products in category_groups.items():
                if not category_products:
                    continue
                    
                # Chuẩn bị dữ liệu cho Excel
                excel_data = []
                
                for product in category_products:
                    row = {
                        'Mã sản phẩm': product.get('code', ''),
                        'Tên sản phẩm (English)': product.get('name', ''),
                        'Tên sản phẩm (Tiếng Việt)': product.get('name_vietnamese', ''),
                        'Series': product.get('series_name', ''),
                        'Nhóm sản phẩm': product.get('group_name', ''),
                        'Mô tả tính năng': product.get('features', ''),
                        'URL sản phẩm': product.get('url', ''),
                        'Ảnh sản phẩm': ', '.join(product.get('images', {}).get('product', [])),
                        'Ảnh thông số kỹ thuật': product.get('images', {}).get('specifications', ''),
                        'Ảnh sơ đồ đấu nối': product.get('images', {}).get('wiring_diagram', ''),
                        'Ảnh kích thước': product.get('images', {}).get('dimensions', ''),
                        'Thông số kỹ thuật (HTML)': product.get('specifications_table', '')
                    }
                    excel_data.append(row)
                
                # Tạo DataFrame và lưu Excel
                df = pd.DataFrame(excel_data)
                filename = f"fotek_category_{category_id}_{timestamp}.xlsx"
                excel_path = excel_categories_dir / filename
                
                with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Sản phẩm', index=False)
                    
                    # Tự động điều chỉnh độ rộng cột
                    worksheet = writer.sheets['Sản phẩm']
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                
                logger.info(f"Đã lưu category {category_id}: {len(category_products)} sản phẩm → {excel_path}")
            
            logger.info(f"Hoàn thành lưu {len(category_groups)} file Excel theo category vào: {excel_categories_dir}")
            
        except Exception as e:
            logger.error(f"Lỗi khi lưu Excel theo category: {e}")
    
    def process_single_product_reprocess(self, row_data: tuple) -> Dict:
        """
        Xử lý một sản phẩm đơn lẻ trong quá trình reprocess (thread-safe)
        
        Args:
            row_data: Tuple chứa (index, row) từ DataFrame
            
        Returns:
            Dict chứa thông tin sản phẩm đã xử lý
        """
        idx, row = row_data
        
        try:
            product_code = row['Mã sản phẩm']
            english_name = row['Tên sản phẩm (English)']
            
            logger.info(f"[{idx+1}] Xử lý lại sản phẩm: {product_code}")
            
            # 1. Sửa tên tiếng Việt với Gemini
            vietnamese_name = self.fix_vietnamese_name_with_gemini(english_name)
            
            # 2. Xử lý lại specs HTML từ ảnh
            specs_html = ""
            spec_image_path = row.get('Ảnh thông số kỹ thuật', '')
            
            if spec_image_path and Path(spec_image_path).exists():
                logger.info(f"Đang dịch lại thông số kỹ thuật cho {product_code}...")
                specs_html = self.extract_specs_from_image_with_gemini(spec_image_path, product_code)
            
            # Tạo lại object sản phẩm
            product = {
                'code': product_code,
                'name': english_name,
                'name_vietnamese': vietnamese_name,
                'series_name': row.get('Series', ''),
                'group_name': row.get('Nhóm sản phẩm', ''),
                'features': row.get('Mô tả tính năng', ''),
                'url': row.get('URL sản phẩm', ''),
                'series_url': f"https://www.fotek.com.tw/en-gb/product-category/{row.get('Category_ID', 'unknown')}",  # Tạm thời
                'images': {
                    'product': [row.get('Ảnh sản phẩm', '')] if row.get('Ảnh sản phẩm', '') else [],
                    'specifications': spec_image_path,
                    'wiring_diagram': row.get('Ảnh sơ đồ đấu nối', ''),
                    'dimensions': row.get('Ảnh kích thước', '')
                },
                'specifications_table': specs_html
            }
            
            return product
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý sản phẩm {product_code}: {e}")
            return None

    def reprocess_existing_data(self, max_workers: int = 5) -> None:
        """
        Xử lý lại dữ liệu hiện có để sửa tên tiếng Việt và specs HTML với đa luồng
        Chỉ lấy lại ảnh thông số kỹ thuật để dịch lại
        
        Args:
            max_workers: Số lượng worker threads tối đa
        """
        try:
            # Tìm file Excel mới nhất
            excel_files = list(self.excel_dir.glob("fotek_products_*.xlsx"))
            if not excel_files:
                logger.error("Không tìm thấy file Excel nào để xử lý lại!")
                return
            
            latest_excel = max(excel_files, key=lambda f: f.stat().st_mtime)
            logger.info(f"Đang xử lý lại dữ liệu từ: {latest_excel}")
            
            # Đọc dữ liệu hiện có
            df = pd.read_excel(latest_excel)
            
            total_products = len(df)
            processed_count = 0
            products_list = []
            
            logger.info(f"🚀 Bắt đầu xử lý lại {total_products} sản phẩm với {max_workers} workers...")
            
            # Tạo danh sách các task (index, row)
            tasks = [(idx, row) for idx, row in df.iterrows()]
            
            # Xử lý đa luồng
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit tất cả tasks
                future_to_task = {
                    executor.submit(self.process_single_product_reprocess, task): task 
                    for task in tasks
                }
                
                # Thu thập kết quả
                for future in as_completed(future_to_task):
                    try:
                        product = future.result()
                        if product:
                            products_list.append(product)
                            processed_count += 1
                            
                            # Log tiến độ mỗi 50 sản phẩm (do đa luồng nên log ít hơn)
                            if processed_count % 50 == 0:
                                logger.info(f"✅ Đã xử lý {processed_count}/{total_products} sản phẩm ({processed_count/total_products*100:.1f}%)")
                                
                    except Exception as e:
                        task = future_to_task[future]
                        logger.error(f"Lỗi khi xử lý task {task[0]}: {e}")
                        continue
            
            logger.info(f"🎉 Hoàn thành xử lý lại {processed_count}/{total_products} sản phẩm")
            
            # Lưu thành các file Excel riêng theo category
            if products_list:
                logger.info("📊 Đang lưu thành các file Excel theo category...")
                self.save_products_by_category(products_list)
                logger.info("✅ Hoàn thành xử lý lại dữ liệu!")
            else:
                logger.warning("⚠️ Không có sản phẩm nào được xử lý thành công!")
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý lại dữ liệu: {e}")
    
    def run_full_scraping(self, category_urls: List[str], selected_series_indices: List[int] = None) -> Dict:
        """
        Chạy toàn bộ quy trình cào dữ liệu cho nhiều danh mục
        
        Args:
            category_urls: Danh sách URL các trang danh mục
            selected_series_indices: Danh sách index của series cần cào (None = tất cả)
            
        Returns:
            Dict chứa thống kê kết quả
        """
        start_time = time.time()
        results = {
            'categories_count': len(category_urls),
            'series_count': 0,
            'products_count': 0,
            'success_count': 0,
            'error_count': 0,
            'duration': 0
        }
        
        try:
            all_series = []
            
            # Bước 1: Trích xuất series từ tất cả các danh mục
            logger.info("🔍 Bắt đầu trích xuất danh sách series từ các danh mục...")
            for category_url in category_urls:
                series_list = self.extract_series_links(category_url)
                all_series.extend(series_list)
                logger.info(f"Đã trích xuất {len(series_list)} series từ: {category_url}")
            
            if not all_series:
                logger.error("Không tìm thấy series nào!")
                return results
            
            # Chọn series cần xử lý
            if selected_series_indices:
                selected_series = [all_series[i] for i in selected_series_indices if 0 <= i < len(all_series)]
            else:
                selected_series = all_series
            
            results['series_count'] = len(selected_series)
            logger.info(f"Sẽ xử lý {len(selected_series)} series")
            
            # Bước 2: Trích xuất sản phẩm từ các series (song song)
            logger.info("📦 Bắt đầu trích xuất sản phẩm từ các series...")
            all_products = self.process_series_parallel(selected_series)
            results['products_count'] = len(all_products)
            
            if not all_products:
                logger.error("Không tìm thấy sản phẩm nào!")
                return results
            
            logger.info(f"Tìm thấy tổng cộng {len(all_products)} sản phẩm")
            
            # Bước 3: Trích xuất chi tiết sản phẩm (song song)
            logger.info("🔍 Bắt đầu trích xuất chi tiết sản phẩm...")
            detailed_products = self.process_products_parallel(all_products)
            
            # Bước 4: Xử lý ảnh (song song)
            logger.info("🖼️ Bắt đầu xử lý và tải xuống ảnh...")
            processed_products = self.process_images_parallel(detailed_products)
            
            # Bước 5: Xử lý AI (song song)
            if self.gemini_model:
                logger.info("🤖 Bắt đầu xử lý AI (dịch và trích xuất thông số)...")
                processed_products = self.process_ai_tasks_parallel(processed_products)
            
            # Bước 6: Lưu dữ liệu
            logger.info("💾 Đang lưu dữ liệu...")
            
            # Lưu JSON
            json_path = self.output_dir / "fotek_products.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(processed_products, f, ensure_ascii=False, indent=2)
            
            # Lưu Excel
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            excel_filename = f"fotek_products_{timestamp}.xlsx"
            self.save_to_excel(processed_products, excel_filename)
            
            results['success_count'] = len(processed_products)
            results['error_count'] = results['products_count'] - results['success_count']
            
            logger.info("✅ Hoàn thành cào dữ liệu!")
            
        except Exception as e:
            logger.error(f"Lỗi trong quá trình cào dữ liệu: {e}")
            results['error_count'] += 1
        
        finally:
            results['duration'] = time.time() - start_time
        
        return results