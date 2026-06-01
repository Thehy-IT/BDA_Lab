# ============================================================
# tests/test_pipeline.py - Unit Tests cho toàn bộ pipeline
# Chạy: python -m pytest tests/ -v
# ============================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from models.user_profile import UserProfile
from models.post import Post, MediaItem
from models.feed import FeedItem, TrendingTag
from storage.mongodb_handler import MongoDBHandler
from storage.redis_handler import RedisHandler
from crawlers.profile_crawler import ProfileCrawler
from crawlers.post_crawler import PostCrawler
from crawlers.feed_crawler import FeedBuilder
from utils.mock_generator import (generate_users, generate_posts,
                                   generate_feed_items, generate_trending_tags)

# ── Fixtures ───────────────────────────────────────────────
@pytest.fixture(scope="module")
def mongo():
    return MongoDBHandler(uri=None, mock_dir="data/test_mock")

@pytest.fixture(scope="module")
def redis():
    return RedisHandler(host="localhost", port=9999)   # port sai → dùng Mock

@pytest.fixture(scope="module")
def sample_users():
    return generate_users(n=5)

@pytest.fixture(scope="module")
def sample_posts(sample_users):
    return generate_posts(sample_users, n_per_user=3)


# ── Model Tests ────────────────────────────────────────────
class TestModels:

    def test_user_profile_creation(self):
        user = UserProfile(username="test_user", platform="twitter",
                           followers_count=1000)
        assert user.username == "test_user"
        assert user.platform == "twitter"
        assert user.followers_count == 1000
        assert user.user_id is not None

    def test_user_to_dict_and_back(self):
        user = UserProfile(username="roundtrip", platform="facebook",
                           bio="Test bio")
        d    = user.to_dict()
        user2 = UserProfile.from_dict(d)
        assert user2.username == user.username
        assert user2.bio      == user.bio

    def test_post_creation(self):
        post = Post(author_name="testuser", content="Hello #Python",
                    hashtags=["Python"], likes_count=42)
        assert "#Python" in post.content
        assert "Python"  in post.hashtags
        assert post.likes_count == 42

    def test_post_to_dict(self):
        post = Post(content="Test", author_id="abc123")
        d    = post.to_dict()
        assert d["content"]   == "Test"
        assert d["author_id"] == "abc123"

    def test_feed_item_scoring(self):
        fi = FeedItem(user_id="u1", post_id="p1",
                      relevance_score=0.8, recency_score=0.6,
                      final_score=0.72, source_type="following")
        assert fi.final_score == 0.72
        assert fi.source_type == "following"

    def test_media_item(self):
        media = MediaItem(media_type="image",
                          url="https://example.com/img.jpg",
                          width=800, height=600)
        d = media.to_dict()
        assert d["media_type"] == "image"
        assert d["width"] == 800


# ── Mock Generator Tests ───────────────────────────────────
class TestMockGenerator:

    def test_generate_users(self):
        users = generate_users(n=10)
        assert len(users) == 10
        for u in users:
            assert u.username != ""
            assert u.platform in ["twitter", "facebook", "instagram"]
            assert u.followers_count >= 0

    def test_generate_posts(self, sample_users):
        posts = generate_posts(sample_users, n_per_user=4)
        assert len(posts) >= len(sample_users)   # ít nhất 1 post/user
        for p in posts:
            assert p.content != ""
            assert len(p.hashtags) > 0

    def test_generate_feed_items(self, sample_users, sample_posts):
        items = generate_feed_items(sample_users, sample_posts, items_per_user=5)
        assert len(items) > 0
        for item in items:
            assert 0.0 <= item.final_score <= 1.0
            assert item.source_type in ["following", "trending", "recommended"]

    def test_generate_trending_tags(self, sample_posts):
        tags = generate_trending_tags(sample_posts)
        assert len(tags) > 0
        # Đảm bảo sort giảm dần theo score
        scores = [t.score for t in tags]
        assert scores == sorted(scores, reverse=True)


# ── Storage Tests ──────────────────────────────────────────
class TestMongoDBHandler:

    def test_save_and_get_user(self, mongo, sample_users):
        user = sample_users[0]
        uid  = mongo.save_user(user.to_dict())
        assert uid == user.user_id

        fetched = mongo.get_user(user.user_id)
        assert fetched is not None
        assert fetched["username"] == user.username

    def test_save_users_bulk(self, mongo, sample_users):
        saved = mongo.save_users_bulk([u.to_dict() for u in sample_users])
        assert saved == len(sample_users)

    def test_save_and_get_post(self, mongo, sample_posts):
        post = sample_posts[0]
        pid  = mongo.save_post(post.to_dict())
        assert pid == post.post_id

    def test_get_posts_by_author(self, mongo, sample_users, sample_posts):
        mongo.save_posts_bulk([p.to_dict() for p in sample_posts])
        author_id = sample_users[0].user_id
        posts = mongo.get_posts_by_author(author_id)
        assert all(p["author_id"] == author_id for p in posts)

    def test_get_posts_by_hashtag(self, mongo, sample_posts):
        mongo.save_posts_bulk([p.to_dict() for p in sample_posts])
        # Lấy hashtag đầu tiên của post đầu tiên
        tag = sample_posts[0].hashtags[0]
        posts = mongo.get_posts_by_hashtag(tag)
        assert len(posts) > 0
        assert all(tag in p["hashtags"] for p in posts)

    def test_count(self, mongo):
        assert mongo.count_users() >= 0
        assert mongo.count_posts() >= 0


class TestRedisHandler:

    def test_push_and_get_feed(self, redis, sample_users):
        user_id = sample_users[0].user_id
        item = FeedItem(user_id=user_id, post_id="post_test",
                        content_preview="Test content",
                        final_score=0.9, source_type="following")
        redis.push_to_feed(user_id, item.to_dict())
        feed = redis.get_feed(user_id, page=0, size=10)
        assert len(feed) >= 1
        assert feed[0]["post_id"] == "post_test"

    def test_trending_update(self, redis):
        redis.update_trending("TestTag", 5.0)
        trending = redis.get_trending_tags(10)
        tags = [t for t, _ in trending]
        assert "TestTag" in tags

    def test_bulk_trending(self, redis):
        redis.bulk_update_trending({"Python": 10, "AI": 8, "NoSQL": 6})
        top = redis.get_trending_tags(3)
        assert len(top) > 0

    def test_likes_counter(self, redis):
        redis.increment_likes("post_abc", 5)
        likes = redis.get_likes("post_abc")
        assert likes >= 5

    def test_online_users(self, redis, sample_users):
        uid = sample_users[0].user_id
        redis.user_online(uid)
        assert redis.get_online_count() >= 1
        online = redis.get_online_users()
        assert uid in online

    def test_feed_length(self, redis, sample_users):
        uid = sample_users[1].user_id
        for i in range(5):
            item = FeedItem(user_id=uid, post_id=f"p{i}")
            redis.push_to_feed(uid, item.to_dict())
        assert redis.get_feed_length(uid) >= 5


# ── Integration Test ───────────────────────────────────────
class TestFullPipeline:

    def test_end_to_end(self, mongo, redis):
        """Test toàn bộ pipeline từ đầu đến cuối"""
        # Crawl
        p_crawler    = ProfileCrawler(db=mongo)
        users        = p_crawler.crawl(limit=5)
        assert len(users) == 5

        post_crawler = PostCrawler(db=mongo)
        posts        = post_crawler.crawl(users, posts_per_user=3)
        assert len(posts) >= 5

        # Build feed
        feed_builder = FeedBuilder(redis=redis)
        stats        = feed_builder.build_feeds(users, posts, items_per_user=10)
        assert len(stats) == len(users)

        # Verify feed exists
        for user in users:
            length = redis.get_feed_length(user.user_id)
            assert length > 0

        # Verify trending updated
        trending = redis.get_trending_tags(5)
        assert len(trending) > 0

        # Verify stats
        mongo_stats = mongo.get_stats()
        assert mongo_stats["total_users"] >= 5
        assert mongo_stats["total_posts"] >= 5
