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
        logging.FileHandler('fotek_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FotekScraper:
    """Class chính cho việc cào dữ liệu từ Fotek.com.tw"""
    
    def __init__(self, gemini_api_key: str = None, max_workers: int = 5):
        """
        Khởi tạo FotekScraper
        
        Args:
            gemini_api_key: API key cho Google Gemini AI
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
        
        # Cấu hình Gemini AI
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.gemini_model = None
            logger.warning("Không có API key cho Gemini AI. Chức năng dịch và trích xuất sẽ bị vô hiệu hóa.")
        
        # Tạo thư mục lưu trữ
        self.output_dir = Path("fotek_data")
        self.images_dir = self.output_dir / "images"
        self.specs_dir = self.output_dir / "specifications"
        self.excel_dir = self.output_dir / "excel"
        
        for dir_path in [self.output_dir, self.images_dir, self.specs_dir, self.excel_dir]:
            dir_path.mkdir(exist_ok=True)
        
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
        
        response = self.safe_request(series_url)
        if not response:
            logger.error(f"Không thể truy cập trang series: {series_url}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        products_list = []
        
        # Tìm container chứa các sản phẩm
        container = soup.find('div', class_='container')
        if not container:
            logger.error("Không tìm thấy container sản phẩm")
            return []
        
        # Tìm tất cả các item-type (nhóm sản phẩm)
        item_types = container.find_all('div', class_='item-type')
        logger.info(f"Tìm thấy {len(item_types)} nhóm sản phẩm")
        
        for item_type in item_types:
            try:
                # Lấy tên nhóm sản phẩm
                group_name_element = item_type.find('h5')
                group_name = group_name_element.text.strip() if group_name_element else "Unknown Group"
                
                # Lấy ảnh nhóm
                img_div = item_type.find('div', class_='box-img')
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
            title_element = soup.find('p', class_='title-card')
            if title_element:
                product_details['name'] = title_element.text.strip()
            
            # Trích xuất ảnh sản phẩm chính
            gallery = soup.find('div', class_='gallery')
            if gallery:
                product_images = []
                for item in gallery.find_all('div', class_='item'):
                    link = item.find('a')
                    if link and link.get('href'):
                        img_url = urljoin(self.base_url, link['href'])
                        product_images.append(img_url)
                product_details['images']['product'] = product_images
            
            # Trích xuất thông tin từ các tab
            tab_content = soup.find('div', class_='tab-content')
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
    
    def extract_specs_from_image_with_gemini(self, image_url: str, product_code: str) -> str:
        """
        Trích xuất thông số kỹ thuật từ ảnh bằng Gemini AI và tạo bảng HTML
        
        Args:
            image_url: URL của ảnh thông số kỹ thuật
            product_code: Mã sản phẩm
            
        Returns:
            HTML table chứa thông số kỹ thuật
        """
        if not self.gemini_model:
            logger.warning("Gemini AI không khả dụng")
            return ""
        
        try:
            # Tải ảnh
            response = self.safe_request(image_url)
            if not response:
                return ""
            
            # Chuyển ảnh thành base64
            image_data = base64.b64encode(response.content).decode()
            
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
            
            Lưu ý: Hàng Copyright là bắt buộc phải có cuối bảng.
            """
            
            # Gửi request tới Gemini với ảnh
            response = self.gemini_model.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": image_data}
            ])
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Lỗi khi trích xuất thông số từ ảnh: {e}")
            return ""
    
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
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
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
            """Download và xử lý tất cả ảnh của một sản phẩm"""
            product_code = product['code']
            series_name = product.get('series_name', 'unknown_series')
            
            # Tạo thư mục cho sản phẩm
            product_dir = self.images_dir / series_name / product_code
            product_dir.mkdir(parents=True, exist_ok=True)
            
            updated_product = product.copy()
            
            # Xử lý ảnh sản phẩm (thêm nền trắng)
            if product['images']['product']:
                product_images_local = []
                for i, img_url in enumerate(product['images']['product']):
                    filename = f"product_{i+1}.webp"
                    save_path = product_dir / filename
                    if self.download_and_process_image(img_url, str(save_path), add_white_background=True):
                        product_images_local.append(str(save_path))
                updated_product['images']['product'] = product_images_local
            
            # Xử lý ảnh thông số kỹ thuật
            if product['images']['specifications']:
                save_path = product_dir / "specifications.webp"
                if self.download_and_process_image(product['images']['specifications'], str(save_path)):
                    updated_product['images']['specifications'] = str(save_path)
            
            # Xử lý ảnh wiring diagram
            if product['images']['wiring_diagram']:
                save_path = product_dir / "wiring_diagram.webp"
                if self.download_and_process_image(product['images']['wiring_diagram'], str(save_path)):
                    updated_product['images']['wiring_diagram'] = str(save_path)
            
            # Xử lý ảnh dimensions
            if product['images']['dimensions']:
                save_path = product_dir / "dimensions.webp"
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
    
    def run_full_scraping(self, category_url: str, selected_series_indices: List[int] = None) -> Dict:
        """
        Chạy toàn bộ quy trình cào dữ liệu
        
        Args:
            category_url: URL trang danh mục
            selected_series_indices: Danh sách index của series cần cào (None = tất cả)
            
        Returns:
            Dict chứa thống kê kết quả
        """
        start_time = time.time()
        results = {
            'series_count': 0,
            'products_count': 0,
            'success_count': 0,
            'error_count': 0,
            'duration': 0
        }
        
        try:
            # Bước 1: Trích xuất series
            logger.info("🔍 Bắt đầu trích xuất danh sách series...")
            all_series = self.extract_series_links(category_url)
            
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


if __name__ == "__main__":
    # Ví dụ sử dụng
    print("=== FOTEK SCRAPER ===")
    print("Chương trình cào dữ liệu từ website Fotek.com.tw")
    print("Vui lòng cung cấp thông tin cần thiết:")
    
    # Nhập thông tin từ người dùng
    category_url = input("Nhập URL danh mục sản phẩm: ").strip()
    if not category_url:
        category_url = "https://www.fotek.com.tw/en-gb/product-category/72"  # URL mặc định
    
    gemini_api_key = input("Nhập Gemini API key (tùy chọn): ").strip()
    max_workers = input("Số luồng xử lý (mặc định 5): ").strip()
    max_workers = int(max_workers) if max_workers.isdigit() else 5
    
    # Khởi tạo scraper
    scraper = FotekScraper(gemini_api_key=gemini_api_key, max_workers=max_workers)
    
    try:
        # Bước 1: Trích xuất các series
        print(f"\n🔍 Đang trích xuất danh sách series từ: {category_url}")
        series_list = scraper.extract_series_links(category_url)
        
        if not series_list:
            print("❌ Không tìm thấy series nào!")
            exit(1)
        
        print(f"✅ Tìm thấy {len(series_list)} series")
        for i, series in enumerate(series_list, 1):
            print(f"  {i}. {series['name']}")
        
        # Cho phép người dùng chọn series cụ thể
        choice = input(f"\nChọn series để cào (1-{len(series_list)}, hoặc 'all' để cào tất cả): ").strip()
        
        selected_indices = []
        if choice.lower() == 'all':
            selected_indices = list(range(len(series_list)))
        else:
            try:
                # Hỗ trợ nhiều lựa chọn: 1,3,5 hoặc 1-5
                if ',' in choice:
                    indices = [int(x.strip()) - 1 for x in choice.split(',')]
                elif '-' in choice:
                    start, end = map(int, choice.split('-'))
                    indices = list(range(start - 1, end))
                else:
                    indices = [int(choice) - 1]
                
                selected_indices = [i for i in indices if 0 <= i < len(series_list)]
                
                if not selected_indices:
                    print("❌ Lựa chọn không hợp lệ!")
                    exit(1)
                    
            except ValueError:
                print("❌ Lựa chọn không hợp lệ!")
                exit(1)
        
        print(f"\n🚀 Bắt đầu cào dữ liệu {len(selected_indices)} series...")
        
        # Chạy quy trình cào dữ liệu hoàn chỉnh
        results = scraper.run_full_scraping(category_url, selected_indices)
        
        # Hiển thị kết quả
        print("\n" + "="*50)
        print("📊 KẾT QUẢ CÀO DỮ LIỆU")
        print("="*50)
        print(f"🏷️  Số series xử lý: {results['series_count']}")
        print(f"📦 Tổng số sản phẩm: {results['products_count']}")
        print(f"✅ Thành công: {results['success_count']}")
        print(f"❌ Lỗi: {results['error_count']}")
        print(f"⏱️  Thời gian: {results['duration']:.2f} giây")
        
        if results['success_count'] > 0:
            print(f"\n💾 Dữ liệu đã được lưu vào thư mục: {scraper.output_dir}")
            print("📁 Cấu trúc file:")
            print("   ├── fotek_products.json (Dữ liệu JSON)")
            print("   ├── excel/ (File Excel)")
            print("   └── images/ (Ảnh sản phẩm theo series)")
            
            # Hiển thị một số sản phẩm đầu tiên
            json_path = scraper.output_dir / "fotek_products.json"
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    products = json.load(f)
                    if products:
                        print(f"\n🔍 Một số sản phẩm đã cào:")
                        for i, product in enumerate(products[:5], 1):
                            name_vn = product.get('name_vietnamese', 'Chưa dịch')
                            print(f"   {i}. {product['code']} - {name_vn}")
                        if len(products) > 5:
                            print(f"   ... và {len(products) - 5} sản phẩm khác")
        
        print("\n🎉 Hoàn thành chương trình!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Dừng chương trình theo yêu cầu người dùng")
    except Exception as e:
        logger.error(f"Lỗi không mong muốn: {e}")
        print(f"❌ Lỗi: {e}")