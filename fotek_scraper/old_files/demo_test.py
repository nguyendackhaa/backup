#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo test cho Fotek Scraper
Kiểm tra các chức năng cơ bản mà không cần chạy toàn bộ chương trình
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from CaoDuLieuFotek import FotekScraper
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
    test_save_path = "test_image.webp"
    
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
    """Test chức năng dịch AI (nếu có API key)"""
    print(f"\n🧪 Test: Dịch AI (tùy chọn)")
    
    api_key = input("Nhập Gemini API key để test (Enter để bỏ qua): ").strip()
    
    if not api_key:
        print("⏭️ Bỏ qua test AI do không có API key")
        return False
    
    scraper = FotekScraper(gemini_api_key=api_key, max_workers=1)
    
    if not scraper.gemini_model:
        print("❌ Không thể khởi tạo Gemini AI")
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

def main():
    """Chạy tất cả các test"""
    print("=" * 60)
    print("🚀 FOTEK SCRAPER - DEMO TEST")
    print("=" * 60)
    print("Test các chức năng cơ bản của Fotek Scraper\n")
    
    start_time = time.time()
    
    # Test 1: Trích xuất series
    series_info = test_series_extraction()
    
    # Test 2: Trích xuất sản phẩm
    product_info = test_products_extraction(series_info)
    
    # Test 3: Chi tiết sản phẩm
    product_details = test_product_details(product_info)
    
    # Test 4: Xử lý ảnh
    test_image_processing()
    
    # Test 5: AI (tùy chọn)
    test_ai_translation()
    
    # Kết quả
    duration = time.time() - start_time
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ TEST")
    print("=" * 60)
    print(f"⏱️  Thời gian test: {duration:.2f} giây")
    print("✅ Tất cả test cơ bản đã hoàn thành!")
    print("\n💡 Để chạy chương trình đầy đủ:")
    print("   python CaoDuLieuFotek.py")

if __name__ == "__main__":
    main()