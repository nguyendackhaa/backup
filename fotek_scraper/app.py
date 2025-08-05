#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask Web Application cho Fotek Scraper
Giao diện web để người dùng nhập nhiều link danh mục và theo dõi tiến trình
"""

from flask import Flask, render_template, request, jsonify, send_file
import json
import threading
import queue
import time
import os
import sys
from pathlib import Path

# Thêm src vào path để import scraper
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from scraper import FotekScraper

app = Flask(__name__)
app.secret_key = 'fotek_scraper_secret_key_2024'

# Global variables để theo dõi tiến trình
scraping_status = {
    'is_running': False,
    'progress': 0,
    'current_task': '',
    'results': {},
    'logs': [],
    'error': None
}

scraping_queue = queue.Queue()

class ScrapingThread(threading.Thread):
    """Thread để chạy scraping trong background"""
    
    def __init__(self, category_urls, max_workers=5):
        super().__init__()
        self.category_urls = category_urls
        self.max_workers = max_workers
        self.scraper = None
        
    def run(self):
        global scraping_status
        
        try:
            scraping_status['is_running'] = True
            scraping_status['progress'] = 0
            scraping_status['current_task'] = 'Khởi tạo scraper...'
            scraping_status['error'] = None
            scraping_status['logs'] = []
            
            # Khởi tạo scraper
            self.scraper = FotekScraper(max_workers=self.max_workers)
            
            # Cập nhật tiến trình
            scraping_status['progress'] = 10
            scraping_status['current_task'] = 'Bắt đầu trích xuất series...'
            
            # Chạy scraping
            results = self.scraper.run_full_scraping(self.category_urls)
            
            # Hoàn thành
            scraping_status['progress'] = 100
            scraping_status['current_task'] = 'Hoàn thành!'
            scraping_status['results'] = results
            scraping_status['is_running'] = False
            
        except Exception as e:
            scraping_status['error'] = str(e)
            scraping_status['is_running'] = False
            scraping_status['current_task'] = f'Lỗi: {str(e)}'

@app.route('/')
def index():
    """Trang chủ"""
    return render_template('index.html')

@app.route('/api/start_scraping', methods=['POST'])
def start_scraping():
    """API để bắt đầu scraping"""
    global scraping_status
    
    try:
        data = request.get_json()
        
        if scraping_status['is_running']:
            return jsonify({
                'success': False,
                'message': 'Scraping đang chạy, vui lòng đợi!'
            })
        
        # Lấy danh sách URLs
        urls = data.get('urls', [])
        max_workers = data.get('max_workers', 5)
        
        if not urls:
            return jsonify({
                'success': False,
                'message': 'Vui lòng nhập ít nhất một URL!'
            })
        
        # Validate URLs
        valid_urls = []
        for url in urls:
            url = url.strip()
            if url and 'fotek.com.tw' in url:
                valid_urls.append(url)
        
        if not valid_urls:
            return jsonify({
                'success': False,
                'message': 'Không có URL Fotek hợp lệ nào!'
            })
        
        # Bắt đầu scraping thread
        thread = ScrapingThread(valid_urls, max_workers)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Bắt đầu cào dữ liệu từ {len(valid_urls)} danh mục',
            'urls_count': len(valid_urls)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        })

@app.route('/api/scraping_status')
def get_scraping_status():
    """API để lấy trạng thái scraping"""
    global scraping_status
    return jsonify(scraping_status)

@app.route('/api/stop_scraping', methods=['POST'])
def stop_scraping():
    """API để dừng scraping"""
    global scraping_status
    
    try:
        # Reset trạng thái
        scraping_status['is_running'] = False
        scraping_status['current_task'] = 'Đã dừng theo yêu cầu'
        
        return jsonify({
            'success': True,
            'message': 'Đã dừng scraping'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        })

@app.route('/api/download_results')
def download_results():
    """API để tải xuống kết quả"""
    try:
        # Tìm file Excel mới nhất
        data_dir = Path('data')
        excel_dir = data_dir / 'excel'
        
        if not excel_dir.exists():
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy thư mục kết quả'
            })
        
        # Tìm file mới nhất
        excel_files = list(excel_dir.glob('*.xlsx'))
        if not excel_files:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy file kết quả'
            })
        
        latest_file = max(excel_files, key=os.path.getctime)
        
        return send_file(
            latest_file,
            as_attachment=True,
            download_name=f'fotek_products_{int(time.time())}.xlsx'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi tải file: {str(e)}'
        })

@app.route('/api/sample_urls')
def get_sample_urls():
    """API để lấy danh sách URL mẫu"""
    sample_urls = [
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
        }
    ]
    
    return jsonify(sample_urls)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': time.time(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    # Tạo thư mục cần thiết
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    print("🚀 Starting Fotek Scraper Web Interface...")
    print("📱 Access at: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)