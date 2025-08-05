#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để xử lý lại dữ liệu hiện có với đa luồng:
1. Sửa tên tiếng Việt bằng Gemini + thêm hậu tố FOTEK 
2. Loại bỏ markdown formatting trong HTML specs
3. Chia thành 22 file Excel riêng theo category
4. Chỉ dịch lại ảnh thông số kỹ thuật, không tải ảnh mới
5. Xử lý song song nhiều sản phẩm để tăng tốc độ

Sử dụng:
    python reprocess_data.py --workers 10    # Sử dụng 10 workers
    python reprocess_data.py --workers 5     # Sử dụng 5 workers (mặc định)
"""

import sys
import logging
import argparse
import time
from pathlib import Path

# Thêm thư mục src vào Python path
sys.path.append(str(Path(__file__).parent / "src"))

from scraper import FotekScraper

def setup_logging():
    """Thiết lập logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('reprocess_data.log', encoding='utf-8')
        ]
    )

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Xử lý lại dữ liệu Fotek với đa luồng để tăng tốc độ',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
    python reprocess_data.py --workers 10    # Sử dụng 10 workers (nhanh nhất)
    python reprocess_data.py --workers 5     # Sử dụng 5 workers (cân bằng)
    python reprocess_data.py --workers 2     # Sử dụng 2 workers (ổn định)
    
Lưu ý:
    - Workers cao hơn = nhanh hơn nhưng có thể bị giới hạn rate limit của Gemini
    - Khuyến nghị: 5-10 workers cho tốc độ tối ưu
    - Nếu gặp lỗi rate limit, hãy giảm số workers
        """
    )
    
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=5,
        help='Số lượng worker threads (mặc định: 5)'
    )
    
    parser.add_argument(
        '--estimate-time',
        action='store_true',
        help='Chỉ ước tính thời gian, không thực hiện xử lý'
    )
    
    return parser.parse_args()

def estimate_processing_time(total_products: int, max_workers: int):
    """Ước tính thời gian xử lý"""
    # Mỗi sản phẩm ước tính ~6 giây (Gemini API calls)
    time_per_product = 6  # seconds
    total_sequential_time = total_products * time_per_product
    
    # Với đa luồng, thời gian giảm theo số workers (với một ít overhead)
    efficiency = 0.8  # 80% hiệu quả do overhead và rate limits
    parallel_time = (total_sequential_time / max_workers) * (1 / efficiency)
    
    return total_sequential_time, parallel_time

def format_time(seconds):
    """Format thời gian thành chuỗi dễ đọc"""
    if seconds < 60:
        return f"{seconds:.0f} giây"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} phút"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} giờ"

def main():
    """Hàm chính"""
    args = parse_arguments()
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🔄 Khởi tạo script xử lý lại dữ liệu hiện có...")
    logger.info(f"⚙️ Cấu hình: {args.workers} workers")
    
    try:
        # Khởi tạo scraper để đọc thông tin
        scraper = FotekScraper(max_workers=1)
        
        # Đọc số lượng sản phẩm để ước tính thời gian
        excel_files = list(scraper.excel_dir.glob("fotek_products_*.xlsx"))
        if not excel_files:
            logger.error("❌ Không tìm thấy file Excel nào!")
            return
        
        import pandas as pd
        latest_excel = max(excel_files, key=lambda f: f.stat().st_mtime)
        df = pd.read_excel(latest_excel)
        total_products = len(df)
        
        # Ước tính thời gian
        sequential_time, parallel_time = estimate_processing_time(total_products, args.workers)
        
        logger.info(f"📊 Tổng số sản phẩm: {total_products}")
        logger.info(f"⏱️ Thời gian ước tính:")
        logger.info(f"   - Tuần tự (1 worker): {format_time(sequential_time)}")
        logger.info(f"   - Song song ({args.workers} workers): {format_time(parallel_time)}")
        logger.info(f"   - Tăng tốc: {sequential_time/parallel_time:.1f}x")
        
        if args.estimate_time:
            logger.info("📋 Chỉ ước tính thời gian - không thực hiện xử lý")
            return
        
        # Xác nhận từ người dùng
        logger.info(f"🚀 Bắt đầu xử lý với {args.workers} workers...")
        
        start_time = time.time()
        
        # Khởi tạo scraper với số workers được chỉ định
        scraper = FotekScraper(max_workers=args.workers)
        
        # Chạy xử lý lại dữ liệu
        scraper.reprocess_existing_data(max_workers=args.workers)
        
        end_time = time.time()
        actual_time = end_time - start_time
        
        logger.info(f"✅ Hoàn thành xử lý lại dữ liệu!")
        logger.info(f"⏱️ Thời gian thực tế: {format_time(actual_time)}")
        logger.info(f"🎯 So với ước tính: {abs(actual_time - parallel_time)/parallel_time*100:.1f}% chênh lệch")
        
    except KeyboardInterrupt:
        logger.info("⚠️ Đã dừng xử lý theo yêu cầu người dùng")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Lỗi trong quá trình xử lý lại dữ liệu: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()