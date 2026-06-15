#!/usr/bin/env python3
# ============================================================
# main.py - Entry point của hệ thống
#
# Chạy: python main.py
# ============================================================

import logging
import sys
import json
from datetime import datetime

import config
from storage.mongodb_handler import MongoDBHandler
from storage.redis_handler    import RedisHandler
from crawlers.profile_crawler import ProfileCrawler
from crawlers.post_crawler    import PostCrawler
from crawlers.feed_crawler    import FeedBuilder


# ── Logging Setup ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/pipeline.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")


# ══════════════════════════════════════════════════════════
def main():
    start_time = datetime.now()

    print("  SOCIAL MEDIA STORAGE SYSTEM")
    print("  Đồ án môn: Hệ quản trị Cơ sở Dữ liệu")
    print("=" * 60)

    # ────────────────────────────────────────────────────────
    # BƯỚC 1: Khởi tạo kết nối DB
    # ────────────────────────────────────────────────────────
    logger.info("BƯỚC 1: Khởi tạo kết nối cơ sở dữ liệu")

    mongo = MongoDBHandler(
        uri=config.MONGO_URI,
        db_name=config.MONGO_DB_NAME,
        mock_dir=config.MOCK_DATA_DIR,
    )
    mongo.create_indexes()

    redis = RedisHandler(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
    )

    # ────────────────────────────────────────────────────────
    # BƯỚC 2: Crawl User Profiles → MongoDB
    # ────────────────────────────────────────────────────────
    logger.info("BƯỚC 2: Crawl User Profiles")

    profile_crawler = ProfileCrawler(db=mongo, platform="all")
    users = profile_crawler.crawl(limit=30)

    # ────────────────────────────────────────────────────────
    # BƯỚC 3: Crawl Posts → MongoDB
    # ────────────────────────────────────────────────────────
    logger.info("BƯỚC 3: Crawl Posts")

    post_crawler = PostCrawler(db=mongo, platform="all")
    posts = post_crawler.crawl(users=users, posts_per_user=8)

    # Khởi tạo likes counter trên Redis
    redis.init_post_likes([p.to_dict() for p in posts])

    # ────────────────────────────────────────────────────────
    # BƯỚC 4: Xây dựng Realtime Feed → Redis
    # ────────────────────────────────────────────────────────
    logger.info("BƯỚC 4: Xây dựng Realtime Feed")

    feed_builder = FeedBuilder(redis=redis)
    feed_builder.build_feeds(users, posts, items_per_user=15)
    feed_builder.simulate_online_users(users, online_ratio=0.3)

    # ────────────────────────────────────────────────────────
    # BƯỚC 5: Demo truy vấn
    # ────────────────────────────────────────────────────────
    logger.info("BƯỚC 5: Demo truy vấn dữ liệu")
    _demo_queries(mongo, redis, users, posts)

    # ────────────────────────────────────────────────────────
    # BƯỚC 6: In báo cáo tổng kết
    # ────────────────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).total_seconds()
    _print_summary(mongo, redis, profile_crawler, post_crawler,
                   feed_builder, elapsed)


# ══════════════════════════════════════════════════════════
def _demo_queries(mongo: MongoDBHandler, redis: RedisHandler,
                  users, posts):
    """Demo các truy vấn tiêu biểu"""

    # ── Q1: Lấy feed của user đầu tiên ────────────────────
    test_user = users[0]
    feed = redis.get_feed(test_user.user_id, page=0, size=5)
    logger.info("  ─ Q1 | Feed của @%s | %d items",
                test_user.username, len(feed))
    for item in feed[:3]:
        logger.info("      • [%s] score=%.3f  %s...",
                    item["source_type"],
                    item["final_score"],
                    item["content_preview"][:50])

    # ── Q2: Top trending hashtags ──────────────────────────
    trending = redis.get_trending_tags(top_n=5)
    logger.info("  ─ Q2 | Top 5 Trending Hashtags:")
    for rank, (tag, score) in enumerate(trending, 1):
        logger.info("      %d. #%s  (score=%.0f)", rank, tag, score)

    # ── Q3: Tìm posts theo hashtag ─────────────────────────
    if trending:
        top_tag = trending[0][0]
        tagged  = mongo.get_posts_by_hashtag(top_tag)
        logger.info("  ─ Q3 | Posts có hashtag #%s: %d bài", top_tag, len(tagged))

    # ── Q4: Lấy bài đăng của 1 user ───────────────────────
    author_posts = list(mongo.get_posts_by_author(test_user.user_id))
    logger.info("  ─ Q4 | Posts của @%s: %d bài",
                test_user.username, len(author_posts))

    # ── Q5: Like một bài đăng (Redis counter) ─────────────
    if posts:
        test_post = posts[0]
        new_count = redis.increment_likes(test_post.post_id, 1)
        logger.info("  ─ Q5 | Like post %s... → tổng likes: %d",
                    test_post.post_id[:8], new_count)

    # ── Q6: Số user đang online ────────────────────────────
    online = redis.get_online_count()
    logger.info("  ─ Q6 | Online users: %d", online)


def _print_summary(mongo, redis, p_crawler, post_crawler,
                   feed_builder, elapsed):
    mongo_stats = mongo.get_stats()
    redis_stats = redis.get_stats()

    print("\n" + "═" * 60)
    print("  BÁO CÁO TỔNG KẾT PIPELINE")
    print("═" * 60)
    print(f"  +  Thời gian thực thi      : {elapsed:.2f} giây")
    print(f"  + Tổng users đã lưu       : {mongo_stats['total_users']}")
    print(f"  + Tổng posts đã lưu       : {mongo_stats['total_posts']}")
    print(f"  + Feed items đã đẩy       : "
          f"{feed_builder.get_stats()['feed_items_pushed']}")
    print(f"  + Trending tags           : {redis_stats['trending_tags_count']}")
    print(f"  + Online users            : {redis_stats['online_users']}")
    print(f"  + MongoDB backend         : {mongo_stats['storage_backend']}")
    print(f"  + Redis backend            : {redis_stats['storage_backend']}")
    print("═" * 60)
    print("  Pipeline hoàn thành thành công!")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()