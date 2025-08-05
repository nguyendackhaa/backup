#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cấu hình cho Fotek Scraper
"""

import os
from pathlib import Path

class Config:
    """Cấu hình cơ bản"""
    
    # Thư mục gốc
    BASE_DIR = Path(__file__).parent.parent
    
    # Thư mục dữ liệu
    DATA_DIR = BASE_DIR / "data"
    IMAGES_DIR = DATA_DIR / "images"
    EXCEL_DIR = DATA_DIR / "excel"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fotek_scraper_secret_key_2024'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 5000))
    
    # Gemini AI
    GEMINI_API_KEY = "AIzaSyBEUiHyq0bBFW_6TRF9g-pmjG3_jQfPpBY"
    
    # Scraping settings
    DEFAULT_MAX_WORKERS = 5
    MAX_WORKERS_LIMIT = 10
    REQUEST_TIMEOUT = 30
    RETRY_ATTEMPTS = 3
    
    # Chrome settings
    CHROME_OPTIONS = [
        '--headless',
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--window-size=1920,1080',
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    ]
    
    # Image processing
    WEBP_QUALITY = 85
    WEBP_OPTIMIZE = True
    
    # Logging
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # URLs mẫu
    SAMPLE_URLS = [
        {
            'name': 'Proximity Sensors',
            'url': 'https://www.fotek.com.tw/en-gb/product-category/72',
            'description': 'Cảm biến tiệm cận'
        },
        {
            'name': 'Temperature Controllers',
            'url': 'https://www.fotek.com.tw/en-gb/product-category/73',
            'description': 'Bộ điều khiển nhiệt độ'
        },
        {
            'name': 'Photoelectric Sensors',
            'url': 'https://www.fotek.com.tw/en-gb/product-category/74',
            'description': 'Cảm biến quang điện'
        },
        {
            'name': 'Solid State Relays',
            'url': 'https://www.fotek.com.tw/en-gb/product-category/75',
            'description': 'Relay trạng thái rắn'
        },
        {
            'name': 'Power Supplies',
            'url': 'https://www.fotek.com.tw/en-gb/product-category/76',
            'description': 'Nguồn điện'
        },
        {
            'name': 'Counters & Timers',
            'url': 'https://www.fotek.com.tw/en-gb/product-category/77',
            'description': 'Bộ đếm và timer'
        }
    ]
    
    @classmethod
    def create_directories(cls):
        """Tạo các thư mục cần thiết"""
        for directory in [cls.DATA_DIR, cls.IMAGES_DIR, cls.EXCEL_DIR, cls.LOGS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_log_file_path(cls):
        """Lấy đường dẫn file log"""
        return cls.LOGS_DIR / "fotek_scraper.log"

class DevelopmentConfig(Config):
    """Cấu hình development"""
    DEBUG = True
    
class ProductionConfig(Config):
    """Cấu hình production"""
    DEBUG = False

# Cấu hình mặc định
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}