# ============================================================
# storage/redis_handler.py
# Xử lý Realtime Feed & Trending Tags bằng Redis
# (Có fallback MockRedis dùng RAM khi không có server)
# ============================================================

import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


# ── Mock Redis (in-memory) ────────────────────────────────
class MockRedis:
    """Giả lập Redis bằng cấu trúc dict trong RAM"""

    def __init__(self):
        self._store: Dict[str, any] = {}
        self._ttls:  Dict[str, float] = {}
        logger.warning("⚠️  Dùng MockRedis (in-memory). "
                       "Dữ liệu mất khi tắt chương trình.")

    # ── String / Counter ────────────────────────────────
    def set(self, key: str, value: str, ex: int = None):
        self._store[key] = value
        return True

    def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    def incr(self, key: str) -> int:
        val = int(self._store.get(key, 0)) + 1
        self._store[key] = str(val)
        return val

    def incrby(self, key: str, amount: int) -> int:
        val = int(self._store.get(key, 0)) + amount
        self._store[key] = str(val)
        return val

    def delete(self, *keys):
        for k in keys:
            self._store.pop(k, None)

    def exists(self, key: str) -> bool:
        return key in self._store

    # ── List (Feed) ─────────────────────────────────────
    def lpush(self, key: str, *values) -> int:
        lst = self._store.setdefault(key, [])
        for v in reversed(values):
            lst.insert(0, v)
        return len(lst)

    def ltrim(self, key: str, start: int, stop: int):
        lst = self._store.get(key, [])
        self._store[key] = lst[start: stop + 1]

    def lrange(self, key: str, start: int, stop: int) -> List[str]:
        lst = self._store.get(key, [])
        end = stop + 1 if stop != -1 else None
        return lst[start:end]

    def llen(self, key: str) -> int:
        return len(self._store.get(key, []))

    # ── Sorted Set (Trending) ────────────────────────────
    def zadd(self, key: str, mapping: dict):
        zset: Dict[str, float] = self._store.setdefault(key, {})
        for member, score in mapping.items():
            zset[member] = float(score)

    def zincrby(self, key: str, amount: float, member: str) -> float:
        zset: Dict[str, float] = self._store.setdefault(key, {})
        zset[member] = zset.get(member, 0.0) + amount
        return zset[member]

    def zrevrange(self, key: str, start: int, stop: int,
                  withscores: bool = False):
        zset: Dict[str, float] = self._store.get(key, {})
        sorted_items = sorted(zset.items(), key=lambda x: -x[1])
        end   = stop + 1 if stop != -1 else None
        chunk = sorted_items[start:end]
        if withscores:
            return [(m, s) for m, s in chunk]
        return [m for m, _ in chunk]

    def zcard(self, key: str) -> int:
        return len(self._store.get(key, {}))

    # ── Set (Online users) ────────────────────────────────
    def sadd(self, key: str, *members) -> int:
        s: set = self._store.setdefault(key, set())
        before = len(s)
        s.update(members)
        return len(s) - before

    def srem(self, key: str, *members):
        s: set = self._store.get(key, set())
        s.difference_update(members)

    def smembers(self, key: str) -> set:
        return set(self._store.get(key, set()))

    def scard(self, key: str) -> int:
        return len(self._store.get(key, set()))

    # ── Hash ──────────────────────────────────────────────
    def hset(self, key: str, mapping: dict):
        h: dict = self._store.setdefault(key, {})
        h.update(mapping)

    def hget(self, key: str, field: str) -> Optional[str]:
        return self._store.get(key, {}).get(field)

    def hgetall(self, key: str) -> dict:
        return dict(self._store.get(key, {}))

    def expire(self, key: str, seconds: int):
        pass    # MockRedis không xử lý TTL


# ── Redis Handler chính ────────────────────────────────────
class RedisHandler:
    """
    Handler quản lý Realtime Feed và Trending Tags bằng Redis.
    Tự động fallback sang MockRedis nếu server offline.
    """

    FEED_PREFIX    = "feed:"
    TRENDING_KEY   = "trending_tags"
    ONLINE_KEY     = "online_users"
    LIKES_PREFIX   = "post_likes:"
    SESSION_PREFIX = "session:"
    FEED_MAX_SIZE  = 200
    FEED_TTL       = 86400   # 24 giờ

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self._r = self._connect(host, port, db)

    def _connect(self, host, port, db):
        try:
            import redis
            r = redis.Redis(host=host, port=port, db=db,
                            decode_responses=True, socket_timeout=2)
            r.ping()
            logger.info("✅ Kết nối Redis thành công: %s:%d", host, port)
            return r
        except Exception as e:
            logger.warning("⚠️  Không kết nối được Redis (%s). "
                           "Chuyển sang MockRedis.", e)
            return MockRedis()

    # ──────────────────────────────────────────────────────
    # REALTIME FEED
    # ──────────────────────────────────────────────────────
    def push_to_feed(self, user_id: str, feed_item_dict: dict,
                     max_size: int = None) -> int:
        """
        Đẩy 1 FeedItem vào đầu danh sách feed của user.
        Feed là Redis List: feed:{user_id}
        """
        max_size = max_size or self.FEED_MAX_SIZE
        key      = self.FEED_PREFIX + user_id
        payload  = json.dumps(feed_item_dict, ensure_ascii=False)
        length   = self._r.lpush(key, payload)
        # Giới hạn số phần tử
        self._r.ltrim(key, 0, max_size - 1)
        self._r.expire(key, self.FEED_TTL)
        return length

    def push_bulk_to_feed(self, feed_items: List[dict]) -> Dict[str, int]:
        """Đẩy nhiều FeedItem vào feed các user"""
        stats: Dict[str, int] = {}
        for item in feed_items:
            uid = item["user_id"]
            n   = self.push_to_feed(uid, item)
            stats[uid] = n
        total_users = len(stats)
        total_items = len(feed_items)
        logger.info("  💾 Đã đẩy %d feed items cho %d users vào Redis",
                    total_items, total_users)
        return stats

    def get_feed(self, user_id: str,
                 page: int = 0, size: int = 20) -> List[dict]:
        """Lấy feed của user, phân trang"""
        key   = self.FEED_PREFIX + user_id
        start = page * size
        stop  = start + size - 1
        raw   = self._r.lrange(key, start, stop)
        items = []
        for r in raw:
            try:
                items.append(json.loads(r))
            except json.JSONDecodeError:
                pass
        return items

    def get_feed_length(self, user_id: str) -> int:
        return self._r.llen(self.FEED_PREFIX + user_id)

    def clear_feed(self, user_id: str):
        self._r.delete(self.FEED_PREFIX + user_id)

    # ──────────────────────────────────────────────────────
    # TRENDING TAGS
    # ──────────────────────────────────────────────────────
    def update_trending(self, tag: str, increment: float = 1.0) -> float:
        """Tăng score cho một hashtag trong trending Sorted Set"""
        new_score = self._r.zincrby(self.TRENDING_KEY, increment, tag)
        return new_score

    def bulk_update_trending(self, tag_scores: Dict[str, float]):
        """Cập nhật trending cho nhiều tags cùng lúc"""
        for tag, score in tag_scores.items():
            self._r.zincrby(self.TRENDING_KEY, score, tag)
        logger.info("  📈 Cập nhật trending: %d tags", len(tag_scores))

    def get_trending_tags(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """Lấy top trending hashtags"""
        result = self._r.zrevrange(self.TRENDING_KEY, 0, top_n - 1,
                                   withscores=True)
        return [(tag, round(score, 1)) for tag, score in result]

    # ──────────────────────────────────────────────────────
    # POST LIKES (Counter)
    # ──────────────────────────────────────────────────────
    def increment_likes(self, post_id: str, amount: int = 1) -> int:
        key = self.LIKES_PREFIX + post_id
        return self._r.incrby(key, amount)

    def get_likes(self, post_id: str) -> int:
        val = self._r.get(self.LIKES_PREFIX + post_id)
        return int(val) if val else 0

    def init_post_likes(self, posts: List[dict]):
        """Khởi tạo counter likes cho danh sách posts"""
        for p in posts:
            key = self.LIKES_PREFIX + p["post_id"]
            self._r.set(key, str(p.get("likes_count", 0)))
        logger.info("  ❤️  Khởi tạo likes counter cho %d posts", len(posts))

    # ──────────────────────────────────────────────────────
    # ONLINE USERS
    # ──────────────────────────────────────────────────────
    def user_online(self, user_id: str):
        self._r.sadd(self.ONLINE_KEY, user_id)

    def user_offline(self, user_id: str):
        self._r.srem(self.ONLINE_KEY, user_id)

    def get_online_count(self) -> int:
        return self._r.scard(self.ONLINE_KEY)

    def get_online_users(self) -> set:
        return self._r.smembers(self.ONLINE_KEY)

    # ──────────────────────────────────────────────────────
    # STATS
    # ──────────────────────────────────────────────────────
    def get_stats(self) -> dict:
        trending = self.get_trending_tags(5)
        return {
            "trending_tags_count": self._r.zcard(self.TRENDING_KEY),
            "online_users":        self.get_online_count(),
            "top_trending":        trending,
            "storage_backend":     ("MockRedis (RAM)"
                                    if isinstance(self._r, MockRedis)
                                    else "Redis"),
        }
