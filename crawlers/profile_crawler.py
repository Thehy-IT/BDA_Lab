# ============================================================
# crawlers/profile_crawler.py
# Crawl User Profiles từ mạng xã hội
# ============================================================

import time
import logging
from typing import List, Optional

from models.user_profile import UserProfile
from storage.mongodb_handler import MongoDBHandler
import config

logger = logging.getLogger(__name__)


class ProfileCrawler:
    """
    Crawl thông tin User Profile từ các nền tảng mạng xã hội.

    Trong môi trường thực tế:
      - Twitter  → Twitter API v2 (Bearer Token)
      - Facebook → Graph API
      - Instagram → Instagram Basic Display API

    Trong bài tập này: dùng mock data generator
    để mô phỏng quá trình crawl.
    """

    def __init__(self, db: MongoDBHandler, platform: str = "all"):
        self.db       = db
        self.platform = platform
        self.delay    = config.CRAWL_DELAY
        self._stats   = {"crawled": 0, "saved": 0, "skipped": 0, "errors": 0}

    # ── Entry point ────────────────────────────────────────
    def crawl(self, user_ids: List[str] = None,
              limit: int = 20) -> List[UserProfile]:
        """
        Crawl danh sách user profiles.

        Args:
            user_ids: Danh sách ID để crawl (None = dùng mock)
            limit:    Số lượng tối đa
        Returns:
            Danh sách UserProfile đã lưu vào DB
        """
        logger.info("═" * 55)
        logger.info("🔍 Bắt đầu crawl User Profiles | platform=%s | limit=%d",
                    self.platform, limit)

        platforms = (config.SOCIAL_PLATFORMS
                     if self.platform == "all"
                     else [self.platform])

        all_profiles: List[UserProfile] = []

        for plat in platforms:
            logger.info("  ▶ Platform: %s", plat.upper())
            profiles = self._crawl_platform(plat, limit // len(platforms))
            all_profiles.extend(profiles)

        # ── Lưu vào MongoDB ───────────────────────────────
        saved = self.db.save_users_bulk([p.to_dict() for p in all_profiles])
        self._stats["saved"] += saved

        logger.info("✅ Hoàn thành crawl profiles | crawled=%d | saved=%d",
                    len(all_profiles), saved)
        return all_profiles

    def _crawl_platform(self, platform: str, n: int) -> List[UserProfile]:
        """Crawl từ 1 platform cụ thể"""
        from utils.mock_generator import generate_users

        profiles = []
        raw_data = self._fetch_profiles(platform, n)

        for raw in raw_data:
            try:
                profile = self._parse_profile(raw, platform)
                profiles.append(profile)
                self._stats["crawled"] += 1
                logger.debug("    ✔ @%s (%d followers)",
                             profile.username, profile.followers_count)
                time.sleep(0)   # giả lập delay (=0 vì mock)
            except Exception as e:
                self._stats["errors"] += 1
                logger.warning("    ✘ Lỗi parse profile: %s", e)

        return profiles

    def _fetch_profiles(self, platform: str, n: int) -> List[dict]:
        """
        Gọi API của platform để lấy dữ liệu thô.
        → Hiện tại trả về dữ liệu mock.
        """
        from utils.mock_generator import generate_users
        users = generate_users(n=n, platform=platform)
        return [u.to_dict() for u in users]

    def _parse_profile(self, raw: dict, platform: str) -> UserProfile:
        """Parse dữ liệu thô từ API thành UserProfile object"""
        # Trong thực tế: map các field của từng API → UserProfile
        # Twitter:  raw["data"]["username"], raw["data"]["public_metrics"]["followers_count"]
        # Facebook: raw["name"], raw["fan_count"]
        return UserProfile.from_dict(raw)

    def get_stats(self) -> dict:
        return dict(self._stats)
