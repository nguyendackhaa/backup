#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tối ưu để xử lý lại dữ liệu với tốc độ cao nhất
Sử dụng 15 workers để tăng tốc độ tối đa
"""

import sys
import logging
import time
from pathlib import Path

# Thêm thư mục src vào Python path
sys.path.append(str(Path(__file__).parent / "src"))

from scraper import FotekScraper

def setup_logging():
    """Thiết lập logging tối ưu"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('reprocess_fast.log', encoding='utf-8')
        ]
    )

def main():
    """Hàm chính với cấu hình tốc độ cao"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Cấu hình tối ưu
    MAX_WORKERS = 15  # Số workers cao để tăng tốc tối đa
    
    logger.info("🚀 SCRIPT XỬ LÝ NHANH - FOTEK REPROCESSOR")
    logger.info(f"⚡ Cấu hình tốc độ cao: {MAX_WORKERS} workers")
    
    try:
        start_time = time.time()
        
        # Khởi tạo scraper với cấu hình tối ưu
        scraper = FotekScraper(max_workers=MAX_WORKERS)
        
        # Chạy xử lý lại dữ liệu
        logger.info("🔥 Bắt đầu xử lý siêu tốc...")
        scraper.reprocess_existing_data(max_workers=MAX_WORKERS)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        logger.info("🎉 HOÀN THÀNH XỬ LÝ SIÊU TỐC!")
        logger.info(f"⏱️ Tổng thời gian: {total_time/60:.1f} phút ({total_time:.0f} giây)")
        logger.info("📂 Kết quả đã được lưu vào fotek_data/excel_categories/")
        
    except KeyboardInterrupt:
        logger.info("⏹️ Đã dừng xử lý theo yêu cầu người dùng")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Lỗi: {e}")
        logger.info("💡 Thử giảm số workers nếu gặp lỗi rate limit")
        sys.exit(1)

if __name__ == "__main__":
    main()