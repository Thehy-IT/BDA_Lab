# ============================================================
# crawlers/post_crawler.py
# Crawl Posts (bài đăng) từ mạng xã hội
# ============================================================

import time
import logging
from typing import List

from models.user_profile import UserProfile
from models.post import Post
from storage.mongodb_handler import MongoDBHandler
import config

logger = logging.getLogger(__name__)


class PostCrawler:
    """
    Crawl Posts từ các trang mạng xã hội.

    Luồng crawl thực tế:
      1. Lấy danh sách user từ MongoDB
      2. Với mỗi user, gọi API platform để lấy bài đăng gần nhất
      3. Parse → Post model → lưu vào MongoDB
      4. Trích hashtag → cập nhật trending trên Redis
    """

    def __init__(self, db: MongoDBHandler, platform: str = "all"):
        self.db       = db
        self.platform = platform
        self.delay    = config.CRAWL_DELAY
        self._stats   = {"crawled": 0, "saved": 0, "errors": 0}

    def crawl(self, users: List[UserProfile],
              posts_per_user: int = 5) -> List[Post]:
        """
        Crawl bài đăng của danh sách users.

        Args:
            users:          Danh sách users đã crawl từ ProfileCrawler
            posts_per_user: Số bài tối đa mỗi user
        Returns:
            Danh sách Post đã lưu
        """
        logger.info("═" * 55)
        logger.info("📝 Bắt đầu crawl Posts | users=%d | posts/user=%d",
                    len(users), posts_per_user)

        all_posts: List[Post] = []

        for i, user in enumerate(users, 1):
            logger.debug("  ▶ [%d/%d] Crawl posts của @%s",
                         i, len(users), user.username)
            posts = self._crawl_user_posts(user, posts_per_user)
            all_posts.extend(posts)

        # ── Lưu vào MongoDB ───────────────────────────────
        saved = self.db.save_posts_bulk([p.to_dict() for p in all_posts])
        self._stats["saved"] += saved

        logger.info("✅ Hoàn thành crawl posts | crawled=%d | saved=%d",
                    len(all_posts), saved)
        return all_posts

    def _crawl_user_posts(self, user: UserProfile,
                          limit: int) -> List[Post]:
        posts = []
        raw_list = self._fetch_posts(user, limit)

        for raw in raw_list:
            try:
                post = self._parse_post(raw)
                posts.append(post)
                self._stats["crawled"] += 1
            except Exception as e:
                self._stats["errors"] += 1
                logger.warning("    ✘ Lỗi parse post: %s", e)

        return posts

    def _fetch_posts(self, user: UserProfile, limit: int) -> List[dict]:
        """
        Gọi API lấy bài đăng của 1 user.
        Twitter API v2:
            GET /2/users/{id}/tweets
            ?max_results={limit}&expansions=attachments.media_keys
        Facebook Graph API:
            GET /{user-id}/posts?fields=message,story,created_time
        """
        from utils.mock_generator import generate_posts
        posts = generate_posts([user], n_per_user=limit)
        return [p.to_dict() for p in posts]

    def _parse_post(self, raw: dict) -> Post:
        return Post.from_dict(raw)

    def extract_hashtag_scores(self, posts: List[Post]) -> dict:
        """Đếm tần suất hashtag để cập nhật trending Redis"""
        counter: dict = {}
        for post in posts:
            for tag in post.hashtags:
                counter[tag] = counter.get(tag, 0) + 1
        return counter

    def get_stats(self) -> dict:
        return dict(self._stats)
