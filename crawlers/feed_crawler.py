# ============================================================
# crawlers/feed_crawler.py
# Xây dựng Realtime Feed & lưu vào Redis
# ============================================================

import logging
from typing import List, Dict
from datetime import datetime

from models.user_profile import UserProfile
from models.post import Post
from models.feed import FeedItem, TrendingTag
from storage.redis_handler import RedisHandler

logger = logging.getLogger(__name__)


class FeedBuilder:
    """
    Xây dựng Realtime Feed cho từng user dựa trên:
      - Bài đăng của người họ follow (following feed)
      - Bài trending (trending feed)
      - Gợi ý cá nhân hoá (recommended feed)

    Feed được đẩy vào Redis List với TTL 24h.
    """

    def __init__(self, redis: RedisHandler):
        self.redis  = redis
        self._stats = {"users_processed": 0,
                       "feed_items_pushed": 0,
                       "trending_updated": 0}

    # ── Hàm chính ──────────────────────────────────────────
    def build_feeds(self, users: List[UserProfile],
                    posts: List[Post],
                    items_per_user: int = 20) -> Dict[str, int]:
        """
        Xây dựng feed cho tất cả users.

        Args:
            users:          Danh sách users
            posts:          Danh sách posts đã crawl được
            items_per_user: Số feed item tối đa mỗi user
        Returns:
            Dict {user_id: số item đã đẩy}
        """
        logger.info("═" * 55)
        logger.info("📡 Xây dựng Realtime Feed | users=%d | posts=%d",
                    len(users), len(posts))

        from utils.mock_generator import generate_feed_items

        # ── Tạo feed items ────────────────────────────────
        feed_items = generate_feed_items(users, posts, items_per_user)

        # ── Sắp xếp theo final_score giảm dần ────────────
        feed_items.sort(key=lambda x: x.final_score, reverse=True)

        # ── Đẩy vào Redis ─────────────────────────────────
        stats = self.redis.push_bulk_to_feed([fi.to_dict() for fi in feed_items])

        self._stats["users_processed"]  += len(users)
        self._stats["feed_items_pushed"] += len(feed_items)

        logger.info("✅ Feed đã được đẩy lên Redis | items=%d | users=%d",
                    len(feed_items), len(stats))

        # ── Cập nhật Trending Tags ─────────────────────────
        self._update_trending(posts)

        return stats

    def _update_trending(self, posts: List[Post]):
        """Cập nhật điểm trending cho các hashtag"""
        tag_counter: Dict[str, float] = {}
        for post in posts:
            for tag in post.hashtags:
                tag_counter[tag] = tag_counter.get(tag, 0.0) + 1.0

        self.redis.bulk_update_trending(tag_counter)
        self._stats["trending_updated"] += len(tag_counter)

        trending = self.redis.get_trending_tags(5)
        logger.info("  🔥 Top 5 Trending: %s",
                    " | ".join([f"#{t} ({s:.0f})" for t, s in trending]))

    def simulate_online_users(self, users: List[UserProfile],
                              online_ratio: float = 0.3):
        """Giả lập một số user đang online (lưu vào Redis Set)"""
        import random
        online = random.sample(users, int(len(users) * online_ratio))
        for u in online:
            self.redis.user_online(u.user_id)
        logger.info("  👥 Online users: %d/%d",
                    self.redis.get_online_count(), len(users))

    def get_stats(self) -> dict:
        return dict(self._stats)
