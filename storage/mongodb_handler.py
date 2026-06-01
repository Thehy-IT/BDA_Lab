# ============================================================
# storage/mongodb_handler.py
# Xử lý lưu trữ User Profiles & Posts vào MongoDB
# (Có fallback MockMongoDB dùng file JSON khi không có server)
# ============================================================

import json
import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


# ── Mock MongoDB (file-based) cho môi trường không có server ─
class MockCollection:
    """Giả lập MongoDB Collection bằng file JSON"""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            self._write([])

    def _read(self) -> List[dict]:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: List[dict]):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def insert_many(self, docs: List[dict]) -> int:
        existing = self._read()
        existing.extend(docs)
        self._write(existing)
        return len(docs)

    def insert_one(self, doc: dict) -> str:
        existing = self._read()
        existing.append(doc)
        self._write(existing)
        return doc.get("user_id") or doc.get("post_id", "")

    def find(self, query: dict = None) -> List[dict]:
        data = self._read()
        if not query:
            return data
        result = []
        for doc in data:
            if all(doc.get(k) == v for k, v in query.items()):
                result.append(doc)
        return result

    def find_one(self, query: dict) -> Optional[dict]:
        results = self.find(query)
        return results[0] if results else None

    def count_documents(self, query: dict = None) -> int:
        return len(self.find(query or {}))

    def update_one(self, query: dict, update: dict) -> bool:
        data = self._read()
        for i, doc in enumerate(data):
            if all(doc.get(k) == v for k, v in query.items()):
                if "$set" in update:
                    data[i].update(update["$set"])
                elif "$inc" in update:
                    for k, v in update["$inc"].items():
                        data[i][k] = data[i].get(k, 0) + v
                self._write(data)
                return True
        return False

    def delete_one(self, query: dict) -> bool:
        data = self._read()
        for i, doc in enumerate(data):
            if all(doc.get(k) == v for k, v in query.items()):
                data.pop(i)
                self._write(data)
                return True
        return False


class MockDatabase:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self._collections: Dict[str, MockCollection] = {}

    def __getitem__(self, name: str) -> MockCollection:
        if name not in self._collections:
            path = os.path.join(self.base_dir, f"{name}.json")
            self._collections[name] = MockCollection(path)
        return self._collections[name]


# ── MongoDB Handler chính ──────────────────────────────────
class MongoDBHandler:
    """
    Handler lưu trữ User Profiles và Posts.
    Tự động dùng MockDatabase nếu pymongo không cài hoặc server offline.
    """

    def __init__(self, uri: str = None, db_name: str = "social_media_db",
                 mock_dir: str = "data/mock_data"):
        self.db_name   = db_name
        self.mock_dir  = mock_dir
        self._db       = None
        self._use_mock = False
        self._connect(uri)

    def _connect(self, uri: str):
        try:
            import pymongo
            client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=2000)
            client.server_info()          # raise nếu không kết nối được
            self._db = client[self.db_name]
            logger.info("✅ Kết nối MongoDB thành công: %s", uri)
        except Exception as e:
            logger.warning("⚠️  Không kết nối được MongoDB (%s). "
                           "Chuyển sang MockDatabase.", e)
            self._db       = MockDatabase(self.mock_dir)
            self._use_mock = True

    # ── Tạo Index (chỉ khi dùng MongoDB thật) ─────────────
    def create_indexes(self):
        if self._use_mock:
            logger.info("MockDB: bỏ qua create_indexes")
            return
        try:
            import pymongo
            self._db["user_profiles"].create_index(
                [("platform", pymongo.ASCENDING),
                 ("username", pymongo.ASCENDING)],
                unique=True, name="idx_platform_username")
            self._db["posts"].create_index(
                [("published_at", pymongo.DESCENDING)], name="idx_published")
            self._db["posts"].create_index(
                [("hashtags", pymongo.ASCENDING)], name="idx_hashtags")
            self._db["posts"].create_index(
                [("author_id", pymongo.ASCENDING)], name="idx_author")
            logger.info("✅ Đã tạo indexes MongoDB")
        except Exception as e:
            logger.error("Lỗi tạo index: %s", e)

    # ──────────────────────────────────────────────────────
    # USER PROFILES
    # ──────────────────────────────────────────────────────
    def save_user(self, user_dict: dict) -> str:
        """Lưu 1 user (upsert theo platform + username)"""
        col = self._db["user_profiles"]
        query = {"platform": user_dict["platform"],
                 "username": user_dict["username"]}
        existing = col.find_one(query)
        if existing:
            user_dict["updated_at"] = datetime.utcnow().isoformat()
            col.update_one(query, {"$set": user_dict})
            logger.debug("  ↩  Cập nhật user: @%s", user_dict["username"])
            return user_dict["user_id"]
        col.insert_one(user_dict)
        logger.debug("  ✚  Lưu user mới: @%s", user_dict["username"])
        return user_dict["user_id"]

    def save_users_bulk(self, user_dicts: List[dict]) -> int:
        """Lưu nhiều user cùng lúc"""
        saved = 0
        for u in user_dicts:
            try:
                self.save_user(u)
                saved += 1
            except Exception as e:
                logger.warning("Lỗi lưu user %s: %s", u.get("username"), e)
        logger.info("  💾 Đã lưu %d/%d users vào MongoDB", saved, len(user_dicts))
        return saved

    def get_user(self, user_id: str) -> Optional[dict]:
        return self._db["user_profiles"].find_one({"user_id": user_id})

    def get_users_by_platform(self, platform: str) -> List[dict]:
        return self._db["user_profiles"].find({"platform": platform})

    def count_users(self) -> int:
        return self._db["user_profiles"].count_documents({})

    # ──────────────────────────────────────────────────────
    # POSTS
    # ──────────────────────────────────────────────────────
    def save_post(self, post_dict: dict) -> str:
        col = self._db["posts"]
        existing = col.find_one({"post_id": post_dict["post_id"]})
        if existing:
            col.update_one({"post_id": post_dict["post_id"]},
                           {"$set": {"likes_count":    post_dict["likes_count"],
                                     "comments_count": post_dict["comments_count"],
                                     "shares_count":   post_dict["shares_count"],
                                     "views_count":    post_dict["views_count"]}})
            logger.debug("  ↩  Cập nhật post: %s", post_dict["post_id"][:8])
            return post_dict["post_id"]
        col.insert_one(post_dict)
        logger.debug("  ✚  Lưu post mới: %s", post_dict["post_id"][:8])
        return post_dict["post_id"]

    def save_posts_bulk(self, post_dicts: List[dict]) -> int:
        saved = 0
        for p in post_dicts:
            try:
                self.save_post(p)
                saved += 1
            except Exception as e:
                logger.warning("Lỗi lưu post %s: %s", p.get("post_id"), e)
        logger.info("  💾 Đã lưu %d/%d posts vào MongoDB", saved, len(post_dicts))
        return saved

    def get_posts_by_author(self, author_id: str) -> List[dict]:
        return self._db["posts"].find({"author_id": author_id})

    def get_posts_by_hashtag(self, tag: str) -> List[dict]:
        posts = self._db["posts"].find({})
        return [p for p in posts if tag in p.get("hashtags", [])]

    def count_posts(self) -> int:
        return self._db["posts"].count_documents({})

    # ──────────────────────────────────────────────────────
    # STATS
    # ──────────────────────────────────────────────────────
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_users": self.count_users(),
            "total_posts": self.count_posts(),
            "storage_backend": "MockDB (JSON)" if self._use_mock else "MongoDB",
        }
