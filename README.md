# Social Media Storage System
> **Đồ án môn: Hệ quản trị Cơ sở Dữ liệu**
> Thiết kế giải pháp lưu trữ NoSQL cho nền tảng mạng xã hội

---

## Cấu trúc dự án

```
social_media_storage/
├── main.py                  # Entry point – chạy toàn bộ pipeline
├── config.py                # Cấu hình MongoDB, Redis, Crawler
├── requirements.txt
│
├── models/                  # Data models
│   ├── user_profile.py      # UserProfile dataclass
│   ├── post.py              # Post + MediaItem dataclasses
│   └── feed.py              # FeedItem + TrendingTag dataclasses
│
├── crawlers/                # Crawl data từ mạng xã hội
│   ├── profile_crawler.py   # Crawl user profiles
│   ├── post_crawler.py      # Crawl bài đăng
│   └── feed_crawler.py      # Xây dựng realtime feed
│
├── storage/                 # Lưu trữ vào NoSQL
│   ├── mongodb_handler.py   # Lưu users & posts vào MongoDB
│   └── redis_handler.py     # Feed & trending vào Redis
│
├── utils/
│   └── mock_generator.py    # Tạo dữ liệu giả lập để test
│
├── tests/
│   └── test_pipeline.py     # Unit tests & integration tests
│
└── data/
    ├── mock_data/           # JSON files (fallback khi không có MongoDB)
    └── pipeline.log         # Log file
```

## Cài đặt & Chạy

```bash
# Cài dependencies
pip install -r requirements.txt

# Chạy pipeline chính
python main.py

# Chạy tests
pytest tests/ -v

# Chạy tests với coverage
pytest tests/ -v --cov=. --cov-report=term-missing
```

## Kiến trúc lưu trữ

| Dữ liệu         | NoSQL DB  | Cấu trúc        | Lý do chọn                          |
|-----------------|-----------|-----------------|--------------------------------------|
| User Profiles   | MongoDB   | Document        | Schema linh hoạt, dễ mở rộng        |
| Posts           | MongoDB   | Document        | Hỗ trợ array (hashtags, media)       |
| Realtime Feed   | Redis     | List            | O(1) push/pop, TTL tự động           |
| Trending Tags   | Redis     | Sorted Set      | Tự động xếp hạng theo score         |
| Post Likes      | Redis     | Counter (String)| Atomic increment cực nhanh          |
| Online Users    | Redis     | Set             | O(1) add/remove/check               |

## Fallback (không cần cài MongoDB/Redis)

Hệ thống tự động fallback:
- **MockDatabase**: Lưu JSON files vào `data/mock_data/`
- **MockRedis**: Dùng dict trong RAM

Cho phép chạy và test mà không cần cài server thật.
