# Hướng dẫn Cài đặt MongoDB & Redis bằng Docker Desktop

Tài liệu này giúp bạn cài đặt môi trường database cần thiết cho dự án **Social Media Storage System** mà không cần cài đặt trực tiếp lên hệ điều hành, giúp máy sạch sẽ và dễ quản lý.

---

## Bước 1: Cài đặt Docker Desktop

1. Truy cập [Docker Desktop Official Website](https://www.docker.com/products/docker-desktop/).
2. Tải bản cài đặt cho Windows (hoặc Mac).
3. Chạy file cài đặt, nhấn **Next** cho đến khi hoàn tất.
4. **Lưu ý:** Docker có thể yêu cầu bạn cài đặt **WSL 2** (Windows Subsystem for Linux). Nếu có thông báo, hãy click vào link Docker cung cấp và làm theo hướng dẫn (thường là chạy 1 lệnh trong PowerShell).
5. Khởi động Docker Desktop và đợi cho biểu tượng con cá voi ở góc dưới màn hình chuyển sang màu xanh (Running).

---

## Bước 2: Chạy MongoDB và Redis bằng lệnh

Mở **Terminal** (hoặc PowerShell/Command Prompt) trên máy tính của bạn và chạy 2 lệnh sau:

### 1. Chạy MongoDB

```bash
docker run -d --name mongodb-bda -p 27017:27017 mongo:latest
```

*Giải thích:* Lệnh này tải bản MongoDB mới nhất, đặt tên là `mongodb-bda` và mở cổng `27017` để dự án kết nối vào.

### 2. Chạy Redis

```bash
docker run -d --name redis-bda -p 6379:6379 redis:latest
```

*Giải thích:* Tương tự, lệnh này chạy Redis và mở cổng `6379`.

---

## Bước 3: Kiểm tra trạng thái

1. Mở giao diện **Docker Desktop**.
2. Vào mục **Containers**.
3. Bạn sẽ thấy `mongodb-bda` và `redis-bda` đang hiển thị trạng thái **Running** (màu xanh).

---

## Bước 4: Cấu hình Dự án để dùng DB thật

Sau khi đã có Docker chạy, bạn cần chỉnh lại code để dự án không dùng dữ liệu giả (Mock) nữa:

1. Mở file `config.py` trong dự án.
2. Tìm dòng:
   ```python
   USE_MOCK_DATA = True
   ```
3. Sửa thành:
   ```python
   USE_MOCK_DATA = False
   ```
4. Lưu file lại.

---

## Bước 5: Chạy dự án và Kiểm tra kết quả

1. Mở terminal tại thư mục dự án.
2. Chạy lệnh chính:
   ```bash
   python main.py
   ```
3. Bây giờ, hãy mở **MongoDB Compass** và **RedisInsight** (như đã hướng dẫn ở file `know.md`) để xem dữ liệu thực tế đã được lưu vào các container Docker.

---

## Các lệnh Docker hữu ích khác (Khi cần)

- **Dừng database:** `docker stop mongodb-bda redis-bda`
  *(Dùng khi bạn không làm việc nữa để tiết kiệm RAM)*
- **Chạy lại database:** `docker start mongodb-bda redis-bda`
- **Xóa bỏ hoàn toàn (để làm lại từ đầu):** `docker rm -f mongodb-bda redis-bda`

---

*Tài liệu hỗ trợ SV Huỳnh Thế Hy.*
