#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo test mới cho Fotek Scraper với cấu trúc đã cập nhật
Kiểm tra các chức năng cơ bản
"""

import sys
import os
from pathlib import Path

# Thêm src vào path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))

from scraper import FotekScraper
import json
import time

def test_series_extraction():
    """Test chức năng trích xuất danh sách series"""
    print("🧪 Test: Trích xuất danh sách series")
    
    scraper = FotekScraper(max_workers=2)
    test_url = "https://www.fotek.com.tw/en-gb/product-category/72"
    
    try:
        series_list = scraper.extract_series_links(test_url)
        
        if series_list:
            print(f"✅ Thành công! Tìm thấy {len(series_list)} series:")
            for i, series in enumerate(series_list[:3], 1):  # Chỉ hiển thị 3 series đầu
                print(f"   {i}. {series['name']}")
                print(f"      URL: {series['url']}")
                print(f"      Image: {series['image'][:50]}..." if series['image'] else "      Image: Không có")
                print()
            
            if len(series_list) > 3:
                print(f"   ... và {len(series_list) - 3} series khác")
            
            return series_list[0] if series_list else None
        else:
            print("❌ Không tìm thấy series nào!")
            return None
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None

def test_products_extraction(series_info):
    """Test chức năng trích xuất sản phẩm từ series"""
    if not series_info:
        print("⏭️ Bỏ qua test sản phẩm do không có series")
        return None
        
    print(f"\n🧪 Test: Trích xuất sản phẩm từ series '{series_info['name']}'")
    
    scraper = FotekScraper(max_workers=2)
    
    try:
        products = scraper.extract_products_from_series(series_info['url'])
        
        if products:
            print(f"✅ Thành công! Tìm thấy {len(products)} sản phẩm:")
            for i, product in enumerate(products[:3], 1):  # Chỉ hiển thị 3 sản phẩm đầu
                print(f"   {i}. {product['code']} - {product['group_name']}")
                print(f"      Features: {product['features'][:50]}...")
                print(f"      URL: {product['url']}")
                print()
            
            if len(products) > 3:
                print(f"   ... và {len(products) - 3} sản phẩm khác")
            
            return products[0] if products else None
        else:
            print("❌ Không tìm thấy sản phẩm nào!")
            return None
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None

def test_product_details(product_info):
    """Test chức năng trích xuất chi tiết sản phẩm"""
    if not product_info:
        print("⏭️ Bỏ qua test chi tiết sản phẩm do không có sản phẩm")
        return None
        
    print(f"\n🧪 Test: Trích xuất chi tiết sản phẩm '{product_info['code']}'")
    
    scraper = FotekScraper(max_workers=1)
    
    try:
        details = scraper.extract_product_details(product_info['url'], product_info['code'])
        
        if details:
            print(f"✅ Thành công! Chi tiết sản phẩm {details['code']}:")
            print(f"   Tên: {details.get('name', 'Không có')}")
            print(f"   URL: {details['url']}")
            
            images = details.get('images', {})
            print(f"   Ảnh sản phẩm: {len(images.get('product', []))} ảnh")
            print(f"   Ảnh thông số: {'Có' if images.get('specifications') else 'Không'}")
            print(f"   Ảnh wiring: {'Có' if images.get('wiring_diagram') else 'Không'}")
            print(f"   Ảnh dimension: {'Có' if images.get('dimensions') else 'Không'}")
            
            return details
        else:
            print("❌ Không lấy được chi tiết sản phẩm!")
            return None
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None

def test_image_processing():
    """Test chức năng xử lý ảnh"""
    print(f"\n🧪 Test: Xử lý ảnh (download và chuyển WebP)")
    
    scraper = FotekScraper(max_workers=1)
    
    # Test với một ảnh mẫu từ Fotek
    test_image_url = "https://www.fotek.com.tw/image/catalog/product/Item/PROXI-PS-05N.png"
    test_save_path = "fotek_data/test_image.webp"
    
    try:
        success = scraper.download_and_process_image(
            test_image_url, 
            test_save_path, 
            add_white_background=True
        )
        
        if success and os.path.exists(test_save_path):
            file_size = os.path.getsize(test_save_path)
            print(f"✅ Thành công! Ảnh đã được lưu:")
            print(f"   File: {test_save_path}")
            print(f"   Kích thước: {file_size} bytes")
            
            # Cleanup
            os.remove(test_save_path)
            print(f"   Đã dọn dẹp file test")
            
            return True
        else:
            print("❌ Không thể xử lý ảnh!")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False

def test_ai_translation():
    """Test chức năng dịch AI"""
    print(f"\n🧪 Test: Dịch AI Gemini")
    
    scraper = FotekScraper(max_workers=1)
    
    if not scraper.gemini_model:
        print("❌ Gemini AI không khả dụng (kiểm tra API key)")
        return False
    
    try:
        test_text = "PS Series Inductive Proximity Sensor"
        vietnamese_text = scraper.translate_with_gemini(test_text)
        
        print(f"✅ Dịch thành công:")
        print(f"   Gốc: {test_text}")
        print(f"   Dịch: {vietnamese_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi AI: {e}")
        return False

def test_full_workflow():
    """Test luồng công việc đầy đủ với 1 sản phẩm"""
    print(f"\n🧪 Test: Luồng công việc đầy đủ")
    
    scraper = FotekScraper(max_workers=2)
    test_urls = ["https://www.fotek.com.tw/en-gb/product-category/72"]
    
    try:
        print("   Bắt đầu cào dữ liệu...")
        
        # Giới hạn chỉ test 1 series để nhanh
        results = scraper.run_full_scraping(test_urls, selected_series_indices=[0])
        
        print(f"✅ Hoàn thành test workflow:")
        print(f"   Series: {results.get('series_count', 0)}")
        print(f"   Sản phẩm: {results.get('products_count', 0)}")
        print(f"   Thành công: {results.get('success_count', 0)}")
        print(f"   Thời gian: {results.get('duration', 0):.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi workflow: {e}")
        return False

def test_config():
    """Test cấu hình"""
    print(f"\n🧪 Test: Cấu hình hệ thống")
    
    try:
        from pathlib import Path
        
        # Kiểm tra thư mục
        data_dir = Path("fotek_data")
        directories = [
            data_dir,
            data_dir / "images", 
            data_dir / "excel", 
            data_dir / "specifications"
        ]
        
        for directory in directories:
            if directory.exists():
                print(f"   ✅ {directory.name}: OK")
            else:
                print(f"   ❌ {directory.name}: Thiếu")
                return False
        
        # Kiểm tra scraper cơ bản
        scraper = FotekScraper(max_workers=1)
        print(f"   API Key: {'Có' if scraper.gemini_model else 'Không'}")
        print(f"   Max Workers: {scraper.max_workers}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi config: {e}")
        return False

def main():
    """Chạy tất cả các test"""
    print("=" * 70)
    print("🚀 FOTEK SCRAPER - DEMO TEST (CẤU TRÚC MỚI)")
    print("=" * 70)
    print("Test các chức năng với cấu trúc thư mục đã cập nhật\n")
    
    start_time = time.time()
    test_results = {}
    
    # Test 0: Cấu hình
    test_results['config'] = test_config()
    
    # Test 1: Trích xuất series
    series_info = test_series_extraction()
    test_results['series'] = series_info is not None
    
    # Test 2: Trích xuất sản phẩm
    product_info = test_products_extraction(series_info)
    test_results['products'] = product_info is not None
    
    # Test 3: Chi tiết sản phẩm
    product_details = test_product_details(product_info)
    test_results['details'] = product_details is not None
    
    # Test 4: Xử lý ảnh
    test_results['images'] = test_image_processing()
    
    # Test 5: AI
    test_results['ai'] = test_ai_translation()
    
    # Test 6: Workflow đầy đủ (tùy chọn)
    do_full_test = input("\n❓ Chạy test workflow đầy đủ? (y/N): ").lower().strip() == 'y'
    if do_full_test:
        test_results['workflow'] = test_full_workflow()
    
    # Kết quả
    duration = time.time() - start_time
    print("\n" + "=" * 70)
    print("📊 KẾT QUẢ TEST")
    print("=" * 70)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.capitalize()}: {status}")
    
    print(f"\n📈 Tổng kết: {passed}/{total} test thành công")
    print(f"⏱️  Thời gian: {duration:.2f} giây")
    
    if passed == total:
        print("\n🎉 Tất cả test đều thành công!")
        print("💡 Hệ thống sẵn sàng để chạy:")
        print("   1. Web interface: python app.py")
        print("   2. CLI: python src/scraper.py")
    else:
        print(f"\n⚠️  Có {total - passed} test thất bại!")
        print("💡 Vui lòng kiểm tra lại cấu hình và kết nối mạng")

if __name__ == "__main__":
    main()