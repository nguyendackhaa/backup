#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ứng dụng dịch tên sản phẩm Fotek
Phát triển bởi: Assistant AI
Chức năng: Dịch tên sản phẩm tiếng Anh sang tiếng Việt sử dụng Gemini AI và xuất Excel
"""

from flask import Flask, render_template, request, jsonify, send_file
import google.generativeai as genai
import logging
import os
import pandas as pd
from datetime import datetime
import io

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Cấu hình Gemini AI
GEMINI_API_KEY = "AIzaSyBEUiHyq0bBFW_6TRF9g-pmjG3_jQfPpBY"

try:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    logger.info("✅ Gemini AI đã được khởi tạo thành công")
except Exception as e:
    gemini_model = None
    logger.warning(f"⚠️ Không thể khởi tạo Gemini AI: {e}")

def translate_product_name(english_name: str) -> dict:
    """
    Dịch tên sản phẩm tiếng Anh sang tiếng Việt sử dụng Gemini AI
    
    Args:
        english_name: Tên sản phẩm tiếng Anh
        
    Returns:
        Dict chứa kết quả dịch
    """
    if not gemini_model:
        return {
            'success': False,
            'error': 'Gemini AI không khả dụng',
            'original': english_name,
            'translated': english_name,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    try:
        prompt = f"""
        Bạn là chuyên gia dịch thuật kỹ thuật. Hãy dịch tên sản phẩm sau sang tiếng Việt:

        Tên sản phẩm: "{english_name}"

        Yêu cầu:
        1. Dịch chính xác và ngắn gọn
        2. Giữ nguyên tên series (như PS, E2E, F, H5-AN...)
        3. Dịch các từ kỹ thuật sang tiếng Việt:
           - Inductive Proximity Sensor → Cảm biến tiệm cận cảm ứng
           - Capacitive Proximity Sensor → Cảm biến tiệm cận điện dung
           - Photo Sensor → Cảm biến quang điện
           - Temperature Controller → Bộ điều khiển nhiệt độ
           - Flow Meter → Đồng hồ đo lưu lượng
           - Pressure Sensor → Cảm biến áp suất
           - Level Sensor → Cảm biến mức
           - Counter → Bộ đếm
           - Timer → Bộ định thời
           - Relay → Rơ le
           - SSR → Module rơ le bán dẫn
           - SCR → Module điều khiển công suất
        4. Thêm từ "dòng" trước tên series
        5. KHÔNG thêm hậu tố FOTEK (sẽ thêm sau)
        6. CHỈ TRẢ VỀ TÊN TIẾNG VIỆT, KHÔNG CÓ GIẢI THÍCH

        Ví dụ:
        - "PS Series Inductive Proximity Sensor" → "Cảm biến tiệm cận cảm ứng dòng PS"
        - "E2E Series Capacitive Proximity Sensor" → "Cảm biến tiệm cận điện dung dòng E2E"
        - "F Series Standard Type Photo Sensor" → "Cảm biến quang điện loại chuẩn dòng F"
        - "H5-AN Series Temperature Controller" → "Bộ điều khiển nhiệt độ dòng H5-AN"

        Tên tiếng Việt:
        """
        
        response = gemini_model.generate_content(prompt)
        
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
                ">", "Tên tiếng Việt:", "Ví dụ:"
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
            
            # Kiểm tra nếu kết quả vẫn là tiếng Anh, thử prompt khác
            if vietnamese_name == english_name or len(vietnamese_name.split()) <= 2:
                # Thử prompt đơn giản hơn
                simple_prompt = f"Translate this product name to Vietnamese: {english_name}"
                simple_response = gemini_model.generate_content(simple_prompt)
                if simple_response and simple_response.text:
                    vietnamese_name = simple_response.text.strip()
                    # Loại bỏ các text không mong muốn
                    for pattern in unwanted_patterns:
                        if pattern in vietnamese_name:
                            vietnamese_name = vietnamese_name.split(pattern)[0].strip()
                            break
            
            # Thêm hậu tố FOTEK
            final_name = f"{vietnamese_name} FOTEK"
            
            logger.info(f"Đã dịch: {english_name} → {final_name}")
            
            return {
                'success': True,
                'original': english_name,
                'translated': final_name,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            logger.warning(f"Gemini không trả về kết quả cho: {english_name}")
            return {
                'success': False,
                'error': 'Không nhận được phản hồi từ Gemini',
                'original': english_name,
                'translated': f"{english_name} FOTEK",
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
    except Exception as e:
        logger.error(f"Lỗi khi dịch '{english_name}': {e}")
        return {
            'success': False,
            'error': str(e),
            'original': english_name,
            'translated': f"{english_name} FOTEK",
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def translate_batch_products(product_names: list) -> list:
    """
    Dịch hàng loạt tên sản phẩm
    
    Args:
        product_names: Danh sách tên sản phẩm tiếng Anh
        
    Returns:
        List các dict chứa kết quả dịch
    """
    results = []
    for i, name in enumerate(product_names):
        logger.info(f"Đang dịch {i+1}/{len(product_names)}: {name}")
        result = translate_product_name(name.strip())
        results.append(result)
    return results

def create_excel_file(translation_results: list) -> bytes:
    """
    Tạo file Excel từ kết quả dịch
    
    Args:
        translation_results: Danh sách kết quả dịch
        
    Returns:
        Bytes của file Excel
    """
    # Chuẩn bị dữ liệu cho Excel
    excel_data = []
    
    for result in translation_results:
        row = {
            'STT': len(excel_data) + 1,
            'Tên sản phẩm (Tiếng Anh)': result['original'],
            'Tên sản phẩm (Tiếng Việt)': result['translated'],
            'Trạng thái': 'Thành công' if result['success'] else 'Lỗi',
            'Lỗi (nếu có)': result.get('error', ''),
            'Thời gian': result['timestamp']
        }
        excel_data.append(row)
    
    # Tạo DataFrame
    df = pd.DataFrame(excel_data)
    
    # Tạo file Excel trong memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Bản dịch sản phẩm', index=False)
        
        # Tự động điều chỉnh độ rộng cột
        worksheet = writer.sheets['Bản dịch sản phẩm']
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
    
    output.seek(0)
    return output.getvalue()

@app.route('/')
def index():
    """Trang chủ với giao diện dịch"""
    return render_template('translator.html')

@app.route('/translate', methods=['POST'])
def translate():
    """API endpoint để dịch tên sản phẩm"""
    try:
        data = request.get_json()
        english_name = data.get('text', '').strip()
        
        if not english_name:
            return jsonify({
                'success': False,
                'error': 'Vui lòng nhập tên sản phẩm cần dịch',
                'original': '',
                'translated': '',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Thực hiện dịch
        result = translate_product_name(english_name)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Lỗi trong API translate: {e}")
        return jsonify({
            'success': False,
            'error': f'Lỗi server: {str(e)}',
            'original': '',
            'translated': '',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

@app.route('/translate_batch', methods=['POST'])
def translate_batch():
    """API endpoint để dịch hàng loạt và xuất Excel"""
    try:
        data = request.get_json()
        product_names_text = data.get('text', '').strip()
        
        if not product_names_text:
            return jsonify({
                'success': False,
                'error': 'Vui lòng nhập danh sách tên sản phẩm cần dịch'
            })
        
        # Tách danh sách sản phẩm (mỗi dòng một sản phẩm)
        product_names = [name.strip() for name in product_names_text.split('\n') if name.strip()]
        
        if not product_names:
            return jsonify({
                'success': False,
                'error': 'Không tìm thấy tên sản phẩm hợp lệ'
            })
        
        logger.info(f"Bắt đầu dịch {len(product_names)} sản phẩm...")
        
        # Thực hiện dịch hàng loạt
        results = translate_batch_products(product_names)
        
        # Tạo file Excel
        excel_data = create_excel_file(results)
        
        # Lưu file tạm thời
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fotek_translations_{timestamp}.xlsx"
        temp_path = f"temp_{filename}"
        
        with open(temp_path, 'wb') as f:
            f.write(excel_data)
        
        logger.info(f"Đã tạo file Excel: {filename}")
        
        return jsonify({
            'success': True,
            'message': f'Đã dịch {len(product_names)} sản phẩm thành công',
            'filename': filename,
            'temp_path': temp_path,
            'results_count': len(results)
        })
        
    except Exception as e:
        logger.error(f"Lỗi trong API translate_batch: {e}")
        return jsonify({
            'success': False,
            'error': f'Lỗi server: {str(e)}'
        })

@app.route('/download_excel/<filename>')
def download_excel(filename):
    """Download file Excel"""
    try:
        temp_path = f"temp_{filename}"
        if os.path.exists(temp_path):
            return send_file(
                temp_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify({'error': 'File không tồn tại'}), 404
    except Exception as e:
        logger.error(f"Lỗi khi download Excel: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Kiểm tra trạng thái hệ thống"""
    return jsonify({
        'status': 'healthy',
        'gemini_available': gemini_model is not None,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

if __name__ == '__main__':
    # Tạo thư mục templates nếu chưa có
    os.makedirs('templates', exist_ok=True)
    
    print("🚀 Khởi động ứng dụng dịch tên sản phẩm Fotek...")
    print(f"📡 Gemini AI: {'✅ Sẵn sàng' if gemini_model else '❌ Không khả dụng'}")
    print("🌐 Truy cập: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 