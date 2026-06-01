# ============================================================
# models/feed.py - Data model cho Realtime Feed
# ============================================================

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional
import uuid


@dataclass
class FeedItem:
    """
    Một mục trong Realtime Feed của user.
    Feed được lưu ở Redis dưới dạng LIST (feed:{user_id}).
    Mỗi item là JSON string đại diện cho FeedItem.
    """
    feed_item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id:      str = ""      # chủ nhân của feed
    post_id:      str = ""      # bài đăng được đưa vào feed
    source_type:  str = ""      # following | trending | recommended | ad

    # ── Thông tin tắt để render nhanh (tránh query thêm) ──
    author_id:    str = ""
    author_name:  str = ""
    content_preview: str = ""   # 200 ký tự đầu
    media_url:    Optional[str] = None
    likes_count:  int = 0
    comments_count: int = 0

    # ── Scoring ───────────────────────────────────────────
    relevance_score: float = 0.0    # điểm liên quan (0–1)
    recency_score:   float = 0.0    # điểm mới mẻ  (0–1)
    final_score:     float = 0.0    # tổng điểm xếp hạng

    # ── Metadata ──────────────────────────────────────────
    inserted_at:  str = field(default_factory=lambda: datetime.utcnow().isoformat())
    is_seen:      bool = False
    is_hidden:    bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FeedItem":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def __repr__(self):
        return (f"<FeedItem user={self.user_id} "
                f"post={self.post_id} "
                f"source={self.source_type} "
                f"score={self.final_score:.3f}>")


@dataclass
class TrendingTag:
    """
    Hashtag đang trending – lưu trong Redis Sorted Set.
    Key: trending_tags  |  score: số lần xuất hiện gần đây
    """
    tag:        str = ""
    score:      float = 0.0
    platform:   str = "all"
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)
