# Fotek Product Scraper

Chương trình cào dữ liệu sản phẩm từ website Fotek.com.tw với các tính năng nâng cao:

## ✨ Tính năng chính

- 🚀 **Cào dữ liệu đa luồng**: Tăng tốc độ xử lý với ThreadPoolExecutor
- 🤖 **Tích hợp AI Gemini**: Dịch tên sản phẩm và trích xuất thông số kỹ thuật từ ảnh
- 🖼️ **Xử lý ảnh nâng cao**: Chuyển đổi sang WebP và thêm nền trắng cho ảnh sản phẩm
- 📊 **Xuất dữ liệu đa định dạng**: JSON và Excel với định dạng đẹp
- 🗂️ **Tổ chức file thông minh**: Cấu trúc thư mục theo series và sản phẩm

## 🔧 Cài đặt

### 1. Cài đặt Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Cài đặt ChromeDriver

Tải ChromeDriver từ [https://chromedriver.chromium.org/](https://chromedriver.chromium.org/) và đặt vào PATH, hoặc cài đặt qua package manager:

**Windows:**
```bash
# Sử dụng chocolatey
choco install chromedriver

# Hoặc sử dụng scoop
scoop install chromedriver
```

**MacOS:**
```bash
brew install chromedriver
```

**Linux:**
```bash
sudo apt-get install chromium-chromedriver
```

### 3. Lấy API key cho Google Gemini (tùy chọn)

1. Truy cập [Google AI Studio](https://aistudio.google.com/)
2. Tạo API key mới
3. Lưu API key để sử dụng khi chạy chương trình

## 🚀 Sử dụng

### Chạy chương trình

```bash
python CaoDuLieuFotek.py
```

### Các bước sử dụng

1. **Nhập URL danh mục**: Nhập URL trang danh mục sản phẩm Fotek (ví dụ: `https://www.fotek.com.tw/en-gb/product-category/72`)

2. **Nhập Gemini API key** (tùy chọn): Để sử dụng tính năng dịch và trích xuất thông số kỹ thuật

3. **Chọn số luồng**: Số luồng xử lý song song (mặc định: 5)

4. **Chọn series**: 
   - Nhập số thứ tự series (ví dụ: `1`)
   - Nhập nhiều series (ví dụ: `1,3,5`)
   - Nhập dải series (ví dụ: `1-5`)
   - Nhập `all` để cào tất cả series

### Ví dụ URLs thử nghiệm

- Proximity Sensors: `https://www.fotek.com.tw/en-gb/product-category/72`
- Temperature Controllers: `https://www.fotek.com.tw/en-gb/product-category/73`
- Photoelectric Sensors: `https://www.fotek.com.tw/en-gb/product-category/74`

## 📁 Cấu trúc dữ liệu đầu ra

```
fotek_data/
├── fotek_products.json              # Dữ liệu JSON đầy đủ
├── excel/
│   └── fotek_products_YYYYMMDD_HHMMSS.xlsx
├── images/
│   ├── [Series Name]/
│   │   ├── [Product Code]/
│   │   │   ├── product_1.webp       # Ảnh sản phẩm (có nền trắng)
│   │   │   ├── specifications.webp  # Ảnh thông số kỹ thuật
│   │   │   ├── wiring_diagram.webp  # Ảnh sơ đồ đấu nối
│   │   │   └── dimensions.webp      # Ảnh kích thước
└── specifications/                  # Thông số kỹ thuật đã trích xuất
```

## 📊 Dữ liệu thu thập

Chương trình sẽ thu thập các thông tin sau cho mỗi sản phẩm:

### Thông tin cơ bản
- **Mã sản phẩm**: Mã model của sản phẩm
- **Tên sản phẩm** (English): Tên gốc từ website
- **Tên sản phẩm** (Tiếng Việt): Được dịch bằng AI Gemini
- **Series**: Tên series sản phẩm
- **Nhóm sản phẩm**: Loại sản phẩm (Square type, Long square type, v.v.)

### Hình ảnh (tất cả được chuyển sang WebP)
- **Ảnh sản phẩm**: Ảnh chính với nền trắng được thêm vào
- **Ảnh thông số kỹ thuật**: Bảng specifications từ website
- **Ảnh sơ đồ đấu nối**: Wiring diagram
- **Ảnh kích thước**: Dimensions/Drawing

### Thông số kỹ thuật
- **Bảng HTML**: Được trích xuất từ ảnh bằng AI và dịch sang tiếng Việt
- **Copyright**: Luôn có dòng "Haiphongtech.vn" như yêu cầu

## ⚙️ Cấu hình nâng cao

### Tùy chỉnh số luồng

```python
scraper = FotekScraper(max_workers=10)  # Tăng số luồng
```

### Sử dụng không có AI

```python
scraper = FotekScraper(gemini_api_key=None)  # Không dùng AI
```

### Chỉ cào series cụ thể

```python
results = scraper.run_full_scraping(url, selected_series_indices=[0, 2, 4])
```

## 🐛 Xử lý lỗi

### Lỗi thường gặp

1. **ChromeDriver không tìm thấy**
   ```
   selenium.common.exceptions.WebDriverException: 'chromedriver' executable needs to be in PATH
   ```
   **Giải pháp**: Cài đặt ChromeDriver theo hướng dẫn ở trên

2. **Lỗi kết nối mạng**
   ```
   requests.exceptions.ConnectionError
   ```
   **Giải pháp**: Kiểm tra kết nối internet và thử lại

3. **Lỗi Gemini API**
   ```
   google.generativeai.types.generation_types.BlockedPromptException
   ```
   **Giải pháp**: Kiểm tra API key hoặc chạy không dùng AI

### Log files

Chương trình tự động tạo file log: `fotek_scraper.log` để theo dõi quá trình xử lý.

## 🔧 Tính năng kỹ thuật

### Đa luồng (Multithreading)
- **Series processing**: Xử lý nhiều series song song
- **Product details**: Cào chi tiết sản phẩm song song  
- **Image processing**: Tải và xử lý ảnh song song
- **AI tasks**: Dịch và trích xuất thông số song song (giới hạn 3 luồng)

### Xử lý ảnh
- **Format conversion**: Tự động chuyển tất cả ảnh sang WebP
- **White background**: Thêm nền trắng cho ảnh sản phẩm
- **Quality optimization**: Tối ưu kích thước file với quality=85

### AI Integration
- **Translation**: Dịch tên sản phẩm sang tiếng Việt
- **OCR + Analysis**: Trích xuất và dịch thông số kỹ thuật từ ảnh
- **Structured output**: Tạo bảng HTML có định dạng chuẩn

## 📈 Hiệu suất

- **Tốc độ**: 5-10 sản phẩm/phút (tùy thuộc vào số luồng và tốc độ mạng)
- **Memory usage**: ~200-500MB cho 100 sản phẩm
- **Storage**: ~2-5MB/sản phẩm (bao gồm ảnh WebP)

## 🤝 Đóng góp

Nếu bạn muốn cải thiện chương trình:

1. Fork repository
2. Tạo feature branch
3. Commit các thay đổi
4. Tạo Pull Request

## 📞 Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra file log `fotek_scraper.log`
2. Đảm bảo đã cài đặt đầy đủ dependencies
3. Kiểm tra kết nối mạng và ChromeDriver

## ⚖️ License

Chương trình này được phát triển cho mục đích giáo dục và nghiên cứu. Vui lòng tuân thủ robots.txt và điều khoản sử dụng của website đích.