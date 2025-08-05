# Fotek Product Translator

Ứng dụng web đơn giản để dịch tên sản phẩm tiếng Anh sang tiếng Việt sử dụng Google Gemini AI.

## 🚀 Tính năng

- **Dịch tên sản phẩm**: Chuyển đổi tên sản phẩm tiếng Anh sang tiếng Việt
- **Giao diện đẹp**: Thiết kế hiện đại, responsive với Bootstrap 5
- **AI Gemini**: Sử dụng Google Gemini AI để dịch chính xác
- **Real-time**: Kiểm tra trạng thái hệ thống real-time
- **Dễ sử dụng**: Giao diện thân thiện, không cần cài đặt phức tạp

## 📋 Yêu cầu hệ thống

- Python 3.7+
- Internet connection
- Google Gemini API key

## 🛠️ Cài đặt

### 1. Clone hoặc tải về project

```bash
cd fotek_scraper
```

### 2. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 3. Cấu hình API Key (Tùy chọn)

Nếu muốn sử dụng API key riêng, tạo file `.env`:

```bash
GEMINI_API_KEY=your_api_key_here
```

Hoặc chỉnh sửa trực tiếp trong file `translator_app.py`:

```python
GEMINI_API_KEY = "your_api_key_here"
```

## 🚀 Chạy ứng dụng

### Chạy ứng dụng dịch

```bash
python translator_app.py
```

Sau khi chạy thành công, truy cập: **http://localhost:5000**

### Chạy ứng dụng crawler chính (nếu cần)

```bash
python app.py
```

## 📖 Cách sử dụng

### 1. Truy cập ứng dụng
- Mở trình duyệt web
- Truy cập: `http://localhost:5000`

### 2. Dịch tên sản phẩm
- Nhập tên sản phẩm tiếng Anh vào ô text
- Nhấn nút "Dịch với AI Gemini"
- Xem kết quả dịch sang tiếng Việt

### 3. Ví dụ sử dụng

**Input (Tiếng Anh):**
```
PS Series Inductive Proximity Sensor
```

**Output (Tiếng Việt):**
```
Cảm biến tiệm cận cảm ứng dòng PS FOTEK
```

## 🎯 Ví dụ tên sản phẩm

| Tiếng Anh | Tiếng Việt |
|-----------|------------|
| PS Series Inductive Proximity Sensor | Cảm biến tiệm cận cảm ứng dòng PS FOTEK |
| E2E Series Capacitive Proximity Sensor | Cảm biến tiệm cận điện dung dòng E2E FOTEK |
| F Series Standard Type Photo Sensor | Cảm biến quang điện loại chuẩn dòng F FOTEK |
| H5-AN Series Temperature Controller | Bộ điều khiển nhiệt độ dòng H5-AN FOTEK |

## 🔧 API Endpoints

### POST /translate
Dịch tên sản phẩm

**Request:**
```json
{
    "text": "PS Series Inductive Proximity Sensor"
}
```

**Response:**
```json
{
    "success": true,
    "original": "PS Series Inductive Proximity Sensor",
    "translated": "Cảm biến tiệm cận cảm ứng dòng PS FOTEK",
    "timestamp": "2024-01-15 10:30:45"
}
```

### GET /health
Kiểm tra trạng thái hệ thống

**Response:**
```json
{
    "status": "healthy",
    "gemini_available": true,
    "timestamp": "2024-01-15 10:30:45"
}
```

## 🎨 Giao diện

- **Responsive Design**: Hoạt động tốt trên desktop, tablet, mobile
- **Modern UI**: Sử dụng Bootstrap 5 và Font Awesome icons
- **Real-time Status**: Hiển thị trạng thái Gemini AI
- **Loading Animation**: Hiệu ứng loading khi đang xử lý
- **Error Handling**: Hiển thị lỗi rõ ràng nếu có

## 🔍 Troubleshooting

### Lỗi "Gemini AI không khả dụng"
- Kiểm tra kết nối internet
- Kiểm tra API key có hợp lệ không
- Kiểm tra quota API có còn không

### Lỗi "Lỗi kết nối đến server"
- Kiểm tra ứng dụng có đang chạy không
- Kiểm tra port 5000 có bị chiếm không
- Thử restart ứng dụng

### Lỗi "Vui lòng nhập tên sản phẩm"
- Đảm bảo đã nhập text vào ô input
- Kiểm tra text không chỉ chứa khoảng trắng

## 📁 Cấu trúc file

```
fotek_scraper/
├── translator_app.py          # Ứng dụng Flask chính
├── templates/
│   └── translator.html        # Template giao diện
├── requirements.txt           # Dependencies
├── README_Translator.md       # Hướng dẫn này
└── .env                      # File cấu hình (tùy chọn)
```

## 🤝 Đóng góp

Nếu bạn muốn đóng góp vào dự án:

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Tạo Pull Request

## 📄 License

Dự án này được phát triển bởi Assistant AI.

## 📞 Hỗ trợ

Nếu gặp vấn đề, vui lòng:
- Kiểm tra phần Troubleshooting
- Tạo issue trên GitHub
- Liên hệ developer

---

**Lưu ý**: Ứng dụng sử dụng Google Gemini AI, vui lòng tuân thủ điều khoản sử dụng của Google. 