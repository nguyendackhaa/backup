# 🤖 Fotek Scraper - Công cụ cào dữ liệu Fotek.com.tw

Công cụ cào dữ liệu sản phẩm từ website Fotek.com.tw với giao diện web hiện đại, AI Gemini và xử lý đa luồng.

## ✨ Tính năng nổi bật

### 🚀 Core Features
- 🌐 **Giao diện Web hiện đại**: Bootstrap 5 responsive design
- ⚡ **Cào dữ liệu đa luồng**: Tăng tốc 3-5x với ThreadPoolExecutor
- 🤖 **AI Gemini tích hợp**: Dịch tiếng Việt + trích xuất thông số từ ảnh
- 🖼️ **Xử lý ảnh nâng cao**: WebP conversion + white background
- 📊 **Xuất Excel đầy đủ**: Thông tin sản phẩm và thông số kỹ thuật
- 🔄 **Real-time monitoring**: Theo dõi tiến trình live

### 💎 Advanced Features
- 📱 **Nhập nhiều URL**: Cào nhiều danh mục cùng lúc
- 🎯 **URL mẫu**: Template URLs sẵn có
- 📈 **Thống kê chi tiết**: Progress tracking và error reporting
- 🗂️ **Tổ chức file thông minh**: Cấu trúc theo series/sản phẩm
- 🔧 **Cấu hình linh hoạt**: Điều chỉnh số luồng, timeout, etc.

## 📂 Cấu trúc dự án

```
fotek_scraper/
├── 📱 app.py                  # Flask web application
├── 📄 requirements.txt       # Python dependencies
├── 📖 README.md              # Documentation
├── 🧪 test_demo.py           # Demo testing script
│
├── 📁 src/                   # Source code
│   └── 🐍 scraper.py        # Core scraping logic
│
├── 📁 templates/             # HTML templates
│   └── 🎨 index.html        # Main web interface
│
├── 📁 static/               # Static web assets
│   ├── 🎨 css/style.css    # Custom styles
│   └── ⚡ js/app.js        # Frontend JavaScript
│
├── 📁 config/               # Configuration files
│   └── ⚙️ config.py        # App configuration
│
├── 📁 data/                 # Output data (auto-created)
│   ├── 📊 excel/           # Excel exports
│   ├── 🖼️ images/          # Product images (WebP)
│   └── 📋 fotek_products.json # JSON data
│
└── 📁 logs/                 # Log files (auto-created)
    └── 📝 fotek_scraper.log
```

## 🚀 Cài đặt nhanh

### 1️⃣ Clone và setup

```bash
git clone <repository>
cd fotek_scraper
```

### 2️⃣ Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Cài đặt ChromeDriver

**Windows (PowerShell):**
```powershell
# Sử dụng chocolatey
choco install chromedriver

# Hoặc tải manual từ: https://chromedriver.chromium.org/
```

**MacOS:**
```bash
brew install chromedriver
```

**Linux:**
```bash
sudo apt-get install chromium-chromedriver
```

### 4️⃣ Chạy ứng dụng

```bash
python app.py
```

Truy cập: http://localhost:5000

## 🎯 Sử dụng

### 🌐 Giao diện Web (Khuyến nghị)

1. **Mở trình duyệt**: http://localhost:5000
2. **Nhập URLs**: 
   - Nhập từng URL một dòng
   - Hoặc chọn "Tải URL mẫu"
3. **Cấu hình**: Điều chỉnh số luồng (3-7 khuyến nghị)
4. **Bắt đầu**: Click "Bắt đầu cào dữ liệu"
5. **Theo dõi**: Xem progress real-time
6. **Tải kết quả**: Download Excel khi hoàn thành

### 🖥️ Command Line

```bash
# Test các chức năng
python test_demo.py

# Chạy trực tiếp (advanced)
python src/scraper.py
```

## 📝 URL mẫu Fotek

```
https://www.fotek.com.tw/en-gb/product-category/72  # Proximity Sensors
https://www.fotek.com.tw/en-gb/product-category/73  # Temperature Controllers  
https://www.fotek.com.tw/en-gb/product-category/74  # Photoelectric Sensors
https://www.fotek.com.tw/en-gb/product-category/75  # Solid State Relays
https://www.fotek.com.tw/en-gb/product-category/76  # Power Supplies
https://www.fotek.com.tw/en-gb/product-category/77  # Counters & Timers
```

## 🤖 AI Gemini Features

### 🌍 Dịch tiếng Việt
- Tự động dịch tên sản phẩm
- Giữ ngữ cảnh kỹ thuật
- Xử lý song song

### 📊 Trích xuất thông số
- OCR từ ảnh specifications
- Tạo bảng HTML chuẩn
- Dịch thông số sang tiếng Việt
- Format: `<table>` với Copyright "Haiphongtech.vn"

## 🖼️ Xử lý ảnh

### 🔄 WebP Conversion
- Chất lượng: 85% (tối ưu size/quality)
- Tự động optimize
- Giảm 60-80% dung lượng

### ⚪ White Background
- Chỉ áp dụng cho ảnh sản phẩm
- Giúp WordPress nhận diện tốt
- Không làm mờ/vỡ ảnh

## 📊 Dữ liệu đầu ra

### 📁 Cấu trúc file
```
data/
├── fotek_products.json           # JSON đầy đủ
├── excel/
│   └── fotek_products_20240801_091234.xlsx
└── images/
    ├── PS_Series_Inductive_Proximity_Sensor/
    │   ├── PS-05N/
    │   │   ├── product_1.webp
    │   │   ├── specifications.webp
    │   │   ├── wiring_diagram.webp
    │   │   └── dimensions.webp
    │   └── PS-05NB/...
    └── Temperature_Controllers/...
```

### 📈 Excel columns
- **Mã sản phẩm**: Product code
- **Tên sản phẩm (English)**: Original name
- **Tên sản phẩm (Tiếng Việt)**: AI translated
- **Series**: Product series name
- **Nhóm sản phẩm**: Product group
- **Mô tả tính năng**: Features description
- **URL sản phẩm**: Product page URL
- **Ảnh sản phẩm**: Local image paths
- **Ảnh thông số kỹ thuật**: Specs image
- **Ảnh sơ đồ đấu nối**: Wiring diagram
- **Ảnh kích thước**: Dimensions image
- **Thông số kỹ thuật (HTML)**: AI extracted specs table

## ⚙️ Cấu hình nâng cao

### 🔧 config/config.py
```python
# Điều chỉnh hiệu suất
DEFAULT_MAX_WORKERS = 5      # Số luồng mặc định
MAX_WORKERS_LIMIT = 10       # Giới hạn tối đa
REQUEST_TIMEOUT = 30         # Timeout request (giây)
RETRY_ATTEMPTS = 3           # Số lần retry

# Chất lượng ảnh
WEBP_QUALITY = 85           # Chất lượng WebP (1-100)
WEBP_OPTIMIZE = True        # Tối ưu hóa
```

### 🎛️ Web interface
- **Số luồng**: 1-10 (khuyến nghị 3-7)
- **Real-time progress**: Cập nhật mỗi giây
- **Error handling**: Hiển thị lỗi chi tiết
- **Download**: Tự động tạo filename với timestamp

## 🐛 Xử lý lỗi

### ❌ Lỗi thường gặp

**ChromeDriver not found:**
```bash
# Solution: Cài đặt ChromeDriver (xem phần cài đặt)
```

**Gemini API error:**
```bash
# Solution: API key đã được embed, kiểm tra kết nối internet
```

**Không tìm thấy sản phẩm:**
```bash
# Solution: Website có thể đã thay đổi cấu trúc, cần update selectors
```

**Lỗi memory:**
```bash
# Solution: Giảm số luồng xuống 2-3
```

### 📝 Debug logs
- File: `logs/fotek_scraper.log`
- Web interface: Real-time log panel
- Level: INFO (có thể chỉnh DEBUG)

## 🚀 Performance

### 📊 Benchmark
- **Single thread**: ~1 sản phẩm/phút
- **5 threads**: ~5-8 sản phẩm/phút  
- **10 threads**: ~8-12 sản phẩm/phút
- **Memory**: ~200-500MB cho 100 sản phẩm
- **Storage**: ~2-5MB/sản phẩm (với ảnh WebP)

### 💡 Tối ưu
- Số luồng tối ưu: **3-7** (tùy CPU và mạng)
- AI tasks giới hạn: **3 luồng** (tránh rate limit)
- Image processing: **Parallel với main threads**
- Excel export: **Batch processing** cuối workflow

## 🆕 What's New

### ✅ Version 2.0 Features
- ✅ **Web interface**: Modern Bootstrap 5 UI
- ✅ **Multiple URLs**: Nhập nhiều danh mục cùng lúc
- ✅ **Real-time progress**: Live monitoring
- ✅ **Better error handling**: Robust selenium + requests
- ✅ **Improved selectors**: Tăng success rate
- ✅ **API key embedded**: Không cần nhập manual
- ✅ **Professional structure**: Modular codebase
- ✅ **Enhanced logging**: Web + file logs

### 🔜 Roadmap
- 🔜 **Database support**: SQLite/PostgreSQL
- 🔜 **Scheduled scraping**: Cron jobs
- 🔜 **API endpoints**: RESTful API
- 🔜 **Docker support**: Containerization
- 🔜 **Multi-language**: English interface

## 🤝 Support

### 📞 Liên hệ
- **Issues**: Tạo GitHub issue
- **Email**: Support team
- **Documentation**: README + code comments

### 🔍 Troubleshooting
1. **Chạy test**: `python test_demo.py`
2. **Kiểm tra logs**: `logs/fotek_scraper.log`
3. **Verify ChromeDriver**: `chromedriver --version`
4. **Test internet**: Ping fotek.com.tw

## 📄 License

Phát triển cho mục đích giáo dục và nghiên cứu. Tuân thủ robots.txt và terms of service của website.

---

## 🎉 Quick Start

```bash
# 1. Cài đặt
pip install -r requirements.txt

# 2. Test
python test_demo.py

# 3. Chạy web app
python app.py

# 4. Mở browser: http://localhost:5000
```

**Happy Scraping! 🚀**