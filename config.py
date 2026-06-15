# ============================================================
# config.py - Cấu hình hệ thống
# ============================================================

# ── MongoDB Settings ──────────────────────────────────────
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "social_media_db"

MONGO_COLLECTIONS = {
    "users":    "user_profiles",
    "posts":    "posts",
    "hashtags": "hashtags",
    "comments": "comments",
}

# ── Redis Settings ─────────────────────────────────────────
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB   = 0

REDIS_KEYS = {
    "feed_prefix":    "feed:",        # feed:{user_id}  → List
    "trending":       "trending_tags",# Sorted Set
    "online_users":   "online_users", # Set
    "post_likes":     "post_likes:",  # post_likes:{post_id} → counter
    "session_prefix": "session:",     # session:{user_id} → Hash
}

REDIS_FEED_MAX_SIZE = 200   # số bài tối đa trong 1 feed
REDIS_TTL_FEED      = 86400 # feed hết hạn sau 24 giờ (giây)
REDIS_TTL_SESSION   = 3600  # session hết hạn sau 1 giờ

# ── Crawler Settings ───────────────────────────────────────
CRAWL_DELAY        = 1.0   # giây giữa các request
CRAWL_MAX_RETRIES  = 3
CRAWL_TIMEOUT      = 10
CRAWL_BATCH_SIZE   = 50    # số bản ghi xử lý mỗi batch

# ── Mock / Simulation ──────────────────────────────────────
USE_MOCK_DATA = False       # True = dùng dữ liệu giả lập (không cần DB thật)
MOCK_DATA_DIR = "data/mock_data"

SOCIAL_PLATFORMS = ["twitter", "facebook", "instagram"]
