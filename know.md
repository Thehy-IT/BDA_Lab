# Hướng dẫn Tìm hiểu & Vận hành Hệ thống BDA Lab

Tài liệu này cung cấp cái nhìn chi tiết về cấu trúc, cách chạy và các điểm quan trọng cần quan sát trong dự án **Social Media Storage System** để phục vụ việc làm báo cáo và slide.

---

## 1. Kiến trúc Tổng quan (Kiến thức cốt lõi)

Hệ thống được thiết kế theo mô hình **Hybrid Storage** kết hợp hai loại NoSQL:

- **MongoDB (Document Store):** Lưu trữ dữ liệu có cấu trúc phức tạp, ít thay đổi và cần lưu lâu dài (Thông tin người dùng, Bài viết).
- **Redis (In-memory Store):** Lưu trữ dữ liệu thời gian thực, tần suất truy cập cao, có vòng đời ngắn (Feed tin nhắn, Tags xu hướng, Đếm lượt like, Trạng thái online).

**Cơ chế Fallback (Quan trọng):**
Nếu bạn không cài sẵn MongoDB hoặc Redis, hệ thống sẽ tự động chuyển sang:

- **MockDatabase:** Lưu dữ liệu vào	 các file JSON trong thư mục `data/mock_data/`.
- **MockRedis:** Lưu dữ liệu vào RAM (biến dict trong Python).

---

## 2. Cách Chạy Dự Án

### Bước 1: Cài đặt môi trường

Mở terminal tại thư mục gốc của dự án và chạy:

```bash
pip install -r requirements.txt
```

### Bước 2: Cấu hình (Tùy chọn)

Mở file `config.py`.

- Nếu muốn dùng DB thật: Cài đặt Mongo/Redis và set `USE_MOCK_DATA = False`.
- Nếu muốn chạy nhanh để lấy kết quả báo cáo: Để nguyên `USE_MOCK_DATA = True`.

### Bước 3: Thực thi Pipeline chính

Đây là lệnh quan trọng nhất để lấy output cho báo cáo:

```bash
python main.py
```

---

## 3. Hướng dẫn Chụp ảnh Báo cáo Thực tế

Đây là hướng dẫn chi tiết cách capture các bằng chứng thực tế cho slide báo cáo.

### A. Screenshot Terminal Output (`python main.py`)

Khi chạy lệnh `python main.py`, terminal sẽ in ra rất nhiều thông tin log. Bạn cần chụp **3 bức ảnh quan trọng** sau:

1. **Ảnh đầu tiên (Bắt đầu):** Chụp phần chữ "SOCIAL MEDIA STORAGE SYSTEM" và các bước khởi tạo (BƯỚC 1, BƯỚC 2).
2. **Ảnh thứ hai (Demo Truy vấn):** Kéo terminal đến phần **BƯỚC 5: Demo truy vấn dữ liệu**. Chụp trọn vẹn từ Q1 đến Q6. Đây là phần ăn điểm nhất vì nó show ra kết quả query thực tế.
3. **Ảnh thứ ba (Bảng tổng kết):** Chụp phần **BÁO CÁO TỔNG KẾT PIPELINE** ở dưới cùng. Đảm bảo nhìn rõ dòng "Thời gian thực thi" và số lượng dữ liệu đã xử lý.

### B. MongoDB Compass — Collections & Documents

*Điều kiện: Đảm bảo bạn đã cài đặt MongoDB server chạy ở localhost:27017 và set `USE_MOCK_DATA = False` trong `config.py` trước khi chạy `main.py`.*

1. Mở MongoDB Compass, kết nối vào `mongodb://localhost:27017/`.
2. Chọn database `social_media_db` ở cột bên trái.
3. **Ảnh 1 (User Profiles):** Nhấp vào collection `user_profiles`. Chụp màn hình giao diện chứa danh sách các Document. Đảm bảo nhìn thấy các trường như `username`, `platform`, `followers_count`. Bạn có thể mở rộng (expand) 1 Document để thấy rõ cấu trúc.
4. **Ảnh 2 (Posts):** Nhấp vào collection `posts`. Chụp danh sách bài đăng. Đặc biệt, hãy mở rộng trường `hashtags` (mảng) và `media` (mảng các đối tượng) để giải thích ưu điểm lưu trữ mảng lồng nhau của MongoDB so với SQL truyền thống.

### C. RedisInsight — Visualize Trending Tags & Feed List

*Điều kiện: Đảm bảo bạn đã cài đặt Redis server chạy ở localhost:6379 và set `USE_MOCK_DATA = False` trong `config.py` trước khi chạy `main.py`.*

1. Mở RedisInsight, kết nối vào `localhost:6379`.
2. **Ảnh 1 (Trending Tags - Sorted Set):**
   - Nhập `trending_tags` vào ô tìm kiếm khóa (Key).
   - Chọn khóa `trending_tags`.
   - Giao diện bên phải sẽ hiển thị kiểu dữ liệu là **ZSET** (Sorted Set). Chụp màn hình danh sách các hashtag cùng với `Score` của chúng. Điều này minh họa cách Redis tự động sắp xếp hashtag thịnh hành.
3. **Ảnh 2 (Feed List - List):**
   - Tìm kiếm `feed:*` để thấy các khóa bắt đầu bằng `feed:`. Chọn một khóa bất kỳ (ví dụ: `feed:1234...`).
   - Giao diện sẽ hiển thị kiểu dữ liệu là **LIST**.
   - Chụp màn hình danh sách các chuỗi JSON bên trong list. Mở rộng 1 dòng JSON để giảng viên thấy cách dữ liệu feed được lưu trữ để truy xuất O(1).
4. **Ảnh 3 (Online Users - Set & Likes - Counter):**
   - Tìm khóa `online_users` (kiểu **SET**) và chụp ảnh minh họa.
   - Tìm một khóa `post_likes:*` (kiểu **STRING**) và chụp ảnh để giải thích về Atomic Counter.

---

## 4. Giải thích Kỹ thuật "Chuyên sâu" cho Slide

Nếu bị hỏi về lý do chọn công nghệ, bạn có thể trả lời dựa trên các điểm sau:

- **Tại sao dùng Redis cho Feed?** Vì Feed cần tốc độ truy xuất cực nhanh (O(1)). Redis List cho phép `LPUSH` bài mới vào đầu và `LRANGE` để lấy trang cũ rất mượt mà.
- **Tại sao dùng MongoDB cho Profile/Post?** Vì dữ liệu mạng xã hội thường xuyên thay đổi cấu trúc (thêm trường mới, metadata mới). MongoDB cho phép lưu trữ Document linh hoạt, không cần chạy Migration nặng nề như SQL.
- **Tại sao có cơ chế Mock?** Để đảm bảo tính **Portability** (khả năng di động). Dự án có thể demo ngay cả trên máy không có sẵn môi trường cài đặt DB phức tạp.

---

## 5. Các Mẹo Nhỏ Khi Trình Bày

1. **Slide Kiến trúc:** Vẽ lại sơ đồ luồng dữ liệu (Crawl -> Mongo & Redis). Dùng bảng so sánh trong `README.md`.
2. **Slide Demo 1 (Lưu trữ):** Đưa ảnh từ **MongoDB Compass** (mục B) lên để giải thích về NoSQL Document.
3. **Slide Demo 2 (Real-time):** Đưa ảnh từ **RedisInsight** (mục C) và **Terminal** (mục A, ảnh 2) để giải thích ưu điểm của Redis.
4. **Slide Tổng kết:** Dùng ảnh Bảng tổng kết cuối cùng của Terminal.

---

*Tài liệu được cập nhật bởi Gemini CLI - Hỗ trợ SV Huỳnh Thế Hy.*
